try:
    from numpy import *
except:
    from Numeric import *

class ScoringScheme( object ):
    def __init__( self, gap_open, gap_extend, default=-100, alphabet1="ACGT", alphabet2=None, gap1="-", gap2=None, text1_range=128, text2_range=None, typecode=Int ):
        if (text2_range == None): text2_range = text1_range
        if (alphabet2 == None): alphabet2 = alphabet1
        if (gap2 == None): gap2 = gap1 # (scheme with gap1=gap2=None is legit)
        if type(alphabet1) == str: alphabet1 = [ch for ch in alphabet1]
        if type(alphabet2) == str: alphabet2 = [ch for ch in alphabet2]
        self.table = zeros( (text1_range, text2_range), typecode )
        self.table *= default
        self.gap_open = gap_open
        self.gap_extend = gap_extend
        self.gap1 = gap1
        self.gap2 = gap2
        self.alphabet1 = alphabet1
        self.alphabet2 = alphabet2
    def set_score( self, a, b, val ):
        self.table[a,b] = val
    def score_alignment( self, a ):
        return score_alignment(self,a)
    def score_texts( self, text1, text2 ):
        return score_texts( self, text1, text2 )
    def __str__ (self):
        isDna1 = "".join( self.alphabet1 ) == "ACGT"
        isDna2 = "".join( self.alphabet2 ) == "ACGT"
        labelRows = not ( isDna1 and isDna2 )
        width = 3
        for a in self.alphabet1:
            for b in self.alphabet2:
                score = self.table[ord(a),ord(b)]
                if (type(score) == float): s = "%8.6f" % score
                else:                      s = "%d"    % score
                if (len(s)+1 > width):
                    width = len(s)+1
        lines = []
        line = []
        if labelRows:
            if isDna1: line.append(" ")
            else:      line.append("  ")
        for b in self.alphabet2:
            if isDna2: s = b
            else:      s = "%02X" % ord(b)
            line.append("%*s" % (width,s))
        lines.append(("".join(line))+"\n")
        for a in self.alphabet1:
            line = []
            if labelRows:
                if isDna1: line.append(a)
                else:      line.append("%02X" % ord(a))
            for b in self.alphabet2:
                score = self.table[ord(a),ord(b)]
                if (type(score) == float): s = "%8.6f" % score
                else:                      s = "%d"    % score
                line.append("%*s" % (width,s))
            lines.append(("".join(line))+"\n")
        return "".join(lines)

def build_scoring_scheme( s, gap_open, gap_extend, gap1="-", gap2=None ):
    """
    Initialize scoring scheme from a blastz style text blob, first line
    specifies the bases for each row/col, subsequent lines contain the
    corresponding scores.  Slaw extensions allow for unusual and/or
    asymmetric alphabets.  Symbols can be two digit hex, and each row
    begins with symbol.  Note that a row corresponds to a symbol in text1
    and a column to a symbol in text2.

    examples:

       blastz                       slaw

          A    C    G    T               01   02    A    C    G    T
         91 -114  -31 -123          01  200 -200  -50  100  -50  100
       -114  100 -125  -31          02 -200  200  100  -50  100  -50
        -31 -125  100 -114
       -123  -31 -114   91
    """
    # perform initial parse to determine alphabets and locate scores
    bad_matrix = "invalid scoring matrix"
    s = s.rstrip( "\n" )
    lines = s.split( "\n" )
    rows  = []
    symbols2 = lines.pop(0).split()
    symbols1 = None
    rows_have_syms = False
    a_la_blastz = True
    for i, line in enumerate( lines ):
        row_scores = line.split()
        if len( row_scores ) == len( symbols2 ):        # blastz-style row
            if symbols1 == None:
                if len( lines ) != len( symbols2 ):
                    raise bad_matrix
                symbols1 = symbols2
            elif (rows_have_syms):
                raise bad_matrix
        elif len( row_scores ) == len( symbols2 ) + 1:  # row starts with symbol
            if symbols1 == None:
                symbols1 = []
                rows_have_syms = True
                a_la_blastz = False
            elif not rows_have_syms:
                raise bad_matrix
            symbols1.append( row_scores.pop(0) )
        else:
            raise bad_matrix
        rows.append( row_scores )
    # convert alphabets from strings to characters
    try:
        alphabet1 = [sym_to_char( sym ) for sym in symbols1]
        alphabet2 = [sym_to_char( sym ) for sym in symbols2]
    except ValueError:
        raise bad_matrix
    if (alphabet1 != symbols1) or (alphabet2 != symbols2):
        a_la_blastz = False
    if a_la_blastz:
        alphabet1 = [ch.upper() for ch in alphabet1]
        alphabet2 = [ch.upper() for ch in alphabet2]
	# decide if rows and/or columns should reflect case
    if a_la_blastz:
    	foldcase1 = foldcase2 = True
    else:
        foldcase1 = "".join( alphabet1 ) == "ACGT"
        foldcase2 = "".join( alphabet2 ) == "ACGT"
    # create appropriately sized matrix
    text1_range = text2_range = 128
    if ord( max( alphabet1 ) ) >= 128: text1_range = 256
    if ord( max( alphabet2 ) ) >= 128: text2_range = 256
    typecode = Int
    for i, row_scores in enumerate( rows ):
        for j, score in enumerate( map( int_or_float, row_scores ) ):
            if type( score ) == float: typecode = Float
    ss = ScoringScheme( gap_open, gap_extend, alphabet1=alphabet1, alphabet2=alphabet2, gap1=gap1, gap2=gap2, text1_range=text1_range, text2_range=text2_range, typecode=typecode )
    # fill matrix
    for i, row_scores in enumerate( rows ):
        for j, score in enumerate( map( int_or_float, row_scores ) ):
            ss.set_score( ord( alphabet1[i] ), ord( alphabet2[j] ), score )
            if foldcase1 and foldcase2:
                ss.set_score( ord( alphabet1[i].lower() ), ord( alphabet2[j].upper() ), score )
                ss.set_score( ord( alphabet1[i].upper() ), ord( alphabet2[j].lower() ), score )
                ss.set_score( ord( alphabet1[i].lower() ), ord( alphabet2[j].lower() ), score )
            elif foldcase1:
                ss.set_score( ord( alphabet1[i].lower() ), ord( alphabet2[j]         ), score )
            elif foldcase2:
                ss.set_score( ord( alphabet1[i]         ), ord( alphabet2[j].lower() ), score )
    return ss

def int_or_float( s ):
    try:    return int( s )
    except: return float( s )

# convert possible two-char symbol to a single character
def sym_to_char( sym ):
    if   len( sym ) == 1: return sym
    elif len( sym ) != 2: raise ValueError
    else:                 return chr(int(sym,base=16))

def score_alignment( scoring_scheme, a ):
    score = 0
    ncomps = len( a.components )
    for i in range( ncomps ):
        for j in range( i+1, ncomps ):
            score += score_texts( scoring_scheme, a.components[i].text, a.components[j].text )
    return score
    
def score_texts( scoring_scheme, text1, text2 ):
    rval = 0
    last_gap_a = last_gap_b = False
    for i in range( len( text1 ) ):
        a = text1[i]
        b = text2[i]
        # Ignore gap/gap pair
        if a == scoring_scheme.gap1 and b == scoring_scheme.gap2: 
            continue
        # Gap in first species
        elif a == scoring_scheme.gap1:
            rval -= scoring_scheme.gap_extend
            if not last_gap_a:
               rval -= scoring_scheme.gap_open
               last_gap_a = True
               last_gap_b = False
        # Gap in second species
        elif b == scoring_scheme.gap2:
            rval -= scoring_scheme.gap_extend
            if not last_gap_b:
               rval -= scoring_scheme.gap_open
               last_gap_a = False
               last_gap_b = True
        # Aligned base
        else:   
            rval += scoring_scheme.table[ord(a),ord(b)]
            last_gap_a = last_gap_b = False
    return rval

def accumulate_scores( scoring_scheme, text1, text2, skip_ref_gaps=False ):
    """
    Return cumulative scores for each position in alignment as a Numeric array.
    
    If `skip_ref_gaps` is False positions in returned array correspond to each
    column in alignment, if True they correspond to each non-gap position (each
    base) in text1.
    """
    if skip_ref_gaps:
        rval = zeros( len( text1 ) - text1.count( scoring_scheme.gap1 ) )
    else:
        rval = zeros( len( text1 ) )
    score = 0
    pos = 0
    last_gap_a = last_gap_b = False
    for i in range( len( text1 ) ):
        a = text1[i]
        b = text2[i]
        # Ignore gap/gap pair
        if a == scoring_scheme.gap1 and b == scoring_scheme.gap2: 
            continue
        # Gap in first species
        elif a == scoring_scheme.gap1:
            score -= scoring_scheme.gap_extend
            if not last_gap_a:
               score -= scoring_scheme.gap_open
               last_gap_a = True
               last_gap_b = False
        # Gap in second species
        elif b == scoring_scheme.gap2:
            score -= scoring_scheme.gap_extend
            if not last_gap_b:
               score -= scoring_scheme.gap_open
               last_gap_a = False
               last_gap_b = True
        # Aligned base
        else:   
            score += scoring_scheme.table[ord(a),ord(b)]
            last_gap_a = last_gap_b = False
        if not( skip_ref_gaps ) or a != scoring_scheme.gap1:
            rval[pos] = score
            pos += 1
    return rval

hox70 = build_scoring_scheme( """  A    C    G    T
                                  91 -114  -31 -123
                                -114  100 -125  -31
                                 -31 -125  100 -114
                                -123  -31 -114   91 """, 400, 30 )