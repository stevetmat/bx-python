import base
import unittest

class Test1( base.BaseScriptTest, unittest.TestCase ):
    command_line = "./scripts/out_to_chain.py ./test_data/epo_tests/epo_547_hs_mm_12way_mammals_65.out --chrsizes ./test_data/epo_tests/hg19.chrom.sizes ./test_data/epo_tests/mm9.chrom.sizes"
    command_line = "./scripts/bnMapper.py ./test_data/epo_tests/hpeaks.bed ./test_data/epo_tests/epo_547_hs_mm_12way_mammals_65.chain"
    output_stdout = base.TestFile( filename="./test_data/epo_tests/hpeaks.mapped.bed4" )

class Test2( base.BaseScriptTest, unittest.TestCase ):
    command_line = "./scripts/bnMapper.py -fBED12 ./test_data/epo_tests/hpeaks.bed ./test_data/epo_tests/epo_547_hs_mm_12way_mammals_65.chain"
    output_stdout = base.TestFile( filename="./test_data/epo_tests/hpeaks.mapped.bed12" )

unittest.main()
