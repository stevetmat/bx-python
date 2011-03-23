"""
BigWig file.
"""

from collections import deque
from bbi_file cimport *
from cirtree_file cimport CIRTreeFile
import numpy
cimport numpy
from types cimport *
from bx.misc.binary_file import BinaryFileReader
from cStringIO import StringIO
import zlib

DEF big_wig_sig = 0x888FFC26
DEF bwg_bed_graph = 1
DEF bwg_variable_step = 2
DEF bwg_fixed_step = 3

cdef inline int range_intersection( int start1, int end1, int start2, int end2 ):
    return min( end1, end2 ) - max( start1, start2 )

cdef class BigWigBlockHandler( BlockHandler ):
    """
    BlockHandler that parses the block into a series of wiggle records, and calls `handle_interval_value` for each.
    """
    cdef handle_block( self, str block_data, BBIFile bbi_file ):
        cdef bits32 b_chrom_id, b_start, b_end, b_valid_count
        cdef bits32 b_item_step, b_item_span
        cdef bits16 b_item_count
        cdef UBYTE b_type
        cdef int s, e
        cdef float val
        # Now we parse the block, first the header
        block_reader = BinaryFileReader( StringIO( block_data ), is_little_endian=bbi_file.reader.is_little_endian )
        b_chrom_id = block_reader.read_uint32()
        b_start = block_reader.read_uint32()
        b_end = block_reader.read_uint32()
        b_item_step = block_reader.read_uint32()
        b_item_span = block_reader.read_uint32()
        b_type = block_reader.read_uint8()
        block_reader.skip(1)
        b_item_count = block_reader.read_uint16()
        for i from 0 <= i < b_item_count:
            # Depending on the type, s and e are either read or 
            # generate using header, val is always read
            if b_type == bwg_bed_graph: 
                s = block_reader.read_uint32()
                e = block_reader.read_uint32()
                val = block_reader.read_float()
            elif b_type == bwg_variable_step:
                s = block_reader.read_uint32()
                e = s + b_item_span
                val = block_reader.read_float()
            elif b_type == bwg_fixed_step:
                s = b_start + ( i * b_item_span )
                e = s + b_item_span
                val = block_reader.read_float()
            self.handle_interval_value( s, e, val )

    cdef handle_interval_value( self, bits32 s, bits32 e, float val ):
        pass

cdef class SummarizingBigWigBlockHandler( BigWigBlockHandler ):
    """
    Accumulates intervals into a SummarizedData
    """
    cdef SummarizedData sd
    def __init__( self, bits32 start, bits32 end, int summary_size ):
        BlockHandler.__init__( self )
        # What we will load into
        self.sd = SummarizedData( start, end, summary_size )
        for i in range(summary_size):
            self.sd.min_val[i] = +numpy.inf
        for i in range(summary_size):
            self.sd.max_val[i] = -numpy.inf

    cdef handle_interval_value( self, bits32 s, bits32 e, float val ):
         self.sd.accumulate_interval_value( s, e, val )

cdef class BigWigFile( BBIFile ): 
    """
    A "big binary indexed" file whose raw data is in wiggle format.
    """
    def __init__( self, file=None ):
        BBIFile.__init__( self, file, big_wig_sig, "bigwig" )

    cdef _summarize_from_full( self, bits32 chrom_id, bits32 start, bits32 end, int summary_size ):
        """
        Create summary from full data.
        """
        self.reader.seek( self.unzoomed_index_offset )
        v = SummarizingBigWigBlockHandler( start, end, summary_size )
        self.visit_blocks_in_region( chrom_id, start, end, v )
        # Round valid count, in place
        for i from 0 <= i < summary_size:
            v.sd.valid_count[i] = round( v.sd.valid_count[i] )
        return v.sd
        
    cpdef get( self, char * chrom, bits32 start, bits32 end ):
        """
        Gets all data points over the regions `chrom`:`start`-`end`.
        """
        if start >= end:
            return None
        chrom_id, chrom_size = self._get_chrom_id_and_size( chrom )
        if chrom_id is None:
            return None


