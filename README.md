# pyTwobit

Package for fetching sequence from twobit files from local paths or URLs. 

## Installing

```
pip install pyTwobit
```

## Usage

To fetch sequence for a genomic region create a TwoBit object with either a local file path or url.  Sequence
is fetched with the `fetch` function which takes chromosome name, start, and end coordinates.
The UCSC coordinate convention is used (0 start, half-open).


Local file

```python

from pytwobit import TwoBit

twobit = TwoBit('test.2bit')
seq = twobit.fetch("chr1", 50, 57)  # -> "CTATCTA"


```

Remote file

```python

from pytwobit import TwoBit

twobit = TwoBit("https://igv.org/genomes/data/hg38/hg38.2bit")
seq = twobit.fetch("chr1", 120565294, 120565335)  # -> "TATGAACTTTTGTTCGTTGGTgctcagtcctagaccctttt"

```
