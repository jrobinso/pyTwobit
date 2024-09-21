# Some of this test code is specific to 2.7
import pathlib
import sys
sys.path.insert(0, "..")
import unittest
from twobitreader import TwoBit

class TwoBitLocalTest(unittest.TestCase):

    def setUp(self):
        # Edit URL as appropriate
        self.filename = str((pathlib.Path(__file__).parent / "foo.2bit").resolve())


    def test_init(self):
        t = TwoBit(self.filename)
        self.assertTrue(isinstance(t, TwoBit))
        self.assertEqual(t.sequenceCount, 1)
        self.assertIsNotNone(t.index)

    def test_getSequenceRecord(self):
        t = TwoBit(self.filename)
        sequence_record = t.getSequenceRecord('chr1')
        self.assertEqual(sequence_record["dnaSize"], 159)

    def test_getSequence(self):
        twobit = TwoBit(self.filename)

        #Non-masked no "N" region
        expectedSeq = "CTATCTA"
        seq =  twobit.readSequence("chr1", 50, 57)
        self.assertEqual(expectedSeq, seq)

        #"N" region
        expectedSeq = "NNNNN"
        seq =  twobit.readSequence("chr1", 42, 47)
        self.assertEqual(expectedSeq, seq)

        # Mixed region
        expectedSeq = "NNNACT"
        seq =  twobit.readSequence("chr1", 44, 50)
        self.assertEqual(expectedSeq, seq)

        # partially masked region
        expectedSeq = "tagcatcctcctacctcacNNacCNctTGGACNCcCaGGGatttcNNNcc"
        seq =  twobit.readSequence("chr1", 100, 150)
        self.assertEqual(expectedSeq, seq)


class TwoBitRemoteTest(unittest.TestCase):

    def test_twobit_sequence(self):
        url = "https://hgdownload.soe.ucsc.edu/goldenPath/hg38/bigZips/hg38.2bit"
        twobit = TwoBit(url)

        #Non-masked no "N" region  chr1:11,830-11,869
        expectedSeq = "GATTGCCAGCACCGGGTATCATTCACCATTTTTCTTTTCG"
        seq =  twobit.readSequence("chr1", 11829, 11869)
        self.assertEqual(expectedSeq, seq)

        #"N" region  chr1:86-124
        expectedSeq = "NNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNN"
        seq =  twobit.readSequence("chr1", 85, 124)
        self.assertEqual(expectedSeq, seq)

        # partially masked region chr1:120,565,295-120,565,335
        expectedSeq = "TATGAACTTTTGTTCGTTGGTgctcagtcctagaccctttt"
        seq =  twobit.readSequence("chr1", 120565294, 120565335)
        self.assertEqual(expectedSeq, seq)

        # Unrecongized sequence name
        seq =  twobit.readSequence("noSuchSequence", 0)
        self.assertIsNone(seq)




if __name__ == '__main__':
    unittest.main()
