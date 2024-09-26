from bisect import bisect_left
from urllib.parse import urlparse
import math
from .remote_file import RemoteFile
from .data_view import DataView

twoBit = ['T', 'C', 'A', 'G']
byteTo4Bases = []
for i in range(0, 256):
    byteTo4Bases.append(
        twoBit[(i >> 6) & 3] +
        twoBit[(i >> 4) & 3] +
        twoBit[(i >> 2) & 3] +
        twoBit[i & 3])

maskedByteTo4Bases = []
for i in range(0, 256):
    maskedByteTo4Bases.append(byteTo4Bases[i].lower())


class TwoBit:

    def __init__(self, path):

        self.path = path
        self.init()

    def open_file_handle(self):
        if urlparse(self.path).scheme in ['http', 'https']:
            return RemoteFile(self.path)
        else:
            return open(self.path, 'rb')

    def check_magic(self, dataview):
        magic = dataview.uint32()
        if magic != 0x1A412743:
            self.byte_order = 'big'
            dataview.byte_order = 'big'
            dataview.position = 0
            magic = dataview.uint32()
            if magic != 0x1A412743:
                raise Exception("Bad magic number")

    def init(self):

        with self.open_file_handle() as file_handle:

            self.meta_index = {}

            self.byte_order = 'little'  # Assumption, will be checked

            dataview = self._dataview(file_handle, 0, 1024)

            self.check_magic(dataview) # Checks magic, side effect - advances dataview cursor

            self.version = dataview.uint32()
            self.sequenceCount = dataview.uint32()
            self.reserved = dataview.uint32()

            # Read index
            index = {}
            estNameLength = 20
            ptr = 0
            for i in range(0, self.sequenceCount):

                if dataview.available() < 1:
                    ptr = ptr + dataview.position
                    size = (self.sequenceCount - i) * estNameLength
                    dataview = self._dataview(file_handle, ptr, size)

                strlen = dataview.getByte()
                if dataview.available() < strlen + 5:
                    ptr = ptr + dataview.position
                    size = (self.sequenceCount - i) * estNameLength
                    dataview = self._dataview(file_handle, ptr, size)

                name = dataview.getString(strlen)
                offset = dataview.uint32()
                index[name] = offset

            self.index = index

    def sequence_record(self, seqName):

        with self.open_file_handle() as file_handle:

            if seqName not in self.meta_index:

                if seqName not in self.index:
                    return None

                offset = self.index[seqName]
                dataview = self._dataview(file_handle, offset, 8)
                dnaSize = dataview.uint32()
                nBlockCount = dataview.uint32()

                offset = offset + 8

                # Read "N" blocks
                size = nBlockCount * (4 + 4) + 4
                dataview = self._dataview(file_handle, offset, size)

                nBlockStarts = []
                for i in range(0, nBlockCount):
                    nBlockStarts.append(dataview.uint32())

                nBlockSizes = []
                for i in range(0, nBlockCount):
                    nBlockSizes.append(dataview.uint32())

                # Read "mask" blocks
                maskBlockCount = dataview.uint32()
                offset += size

                size = maskBlockCount * (4 + 4) + 4
                dataview = self._dataview(file_handle, offset, size)

                maskBlockStarts = []
                for i in range(0, maskBlockCount):
                    maskBlockStarts.append(dataview.uint32())

                maskBlockSizes = []
                for i in range(0, maskBlockCount):
                    maskBlockSizes.append(dataview.uint32())

                # Transform "N" and "mask" block data into something more useful
                nBlocks = []
                for i in range(0, nBlockCount):
                    nBlocks.append(Block(nBlockStarts[i],nBlockSizes[i]))

                maskBlocks = []
                for i in range(0, maskBlockCount):
                    maskBlocks.append(Block(maskBlockStarts[i],maskBlockSizes[i]))

                reserved = dataview.uint32()
                if reserved != 0:
                    raise 'Bad 2-bit file'

                offset += size
                meta = {
                    "dnaSize": dnaSize,
                    "nBlocks": nBlocks,
                    "maskBlocks": maskBlocks,
                    "packedPos": offset,
                    "bpLength": dnaSize
                }

                self.meta_index[seqName] = meta

            return self.meta_index[seqName]

    def fetch(self, seqName, regionStart=None, regionEnd=None):

        with self.open_file_handle() as file_handle:

            record = self.sequence_record(seqName)
            if record is None:
                return None

            if regionStart is None:
                regionStart = 0
            elif regionStart < 0:
                raise 'regionStart cannot be less than 0'


            # end defaults to the end of the sequence
            if regionEnd is None or regionEnd > record["dnaSize"]:
                regionEnd = record["dnaSize"]

            # Get the "N" and "mask" blocks
            nBlocks = getOverlappingBlocks(regionStart, regionEnd, record["nBlocks"])
            maskBlocks = getOverlappingBlocks(regionStart, regionEnd, record["maskBlocks"])

            baseBytesOffset = math.floor(regionStart / 4)
            start = record["packedPos"] + baseBytesOffset
            size = math.floor(regionEnd / 4) - baseBytesOffset + 1

            file_handle.seek(start)
            baseBytes = file_handle.read(size)

            sequenceBases = []

            genomicPosition = regionStart
            while genomicPosition < regionEnd:

                # check if we are currently masked
                # trim masks to the left of genomic position
                n = next((i for i, block in enumerate(maskBlocks) if block.end > genomicPosition), None)
                if n is not None and n > 0:
                    maskBlocks = maskBlocks[n:]

                baseIsMasked = len(maskBlocks) > 0 and maskBlocks[0].start <= genomicPosition and maskBlocks[0].end > genomicPosition

                # process the N block if we have one.  Masked "N" ("n")  is not supported
                if len(nBlocks) > 0 and genomicPosition >= nBlocks[0].start and genomicPosition < nBlocks[0].end:
                    currentNBlock = nBlocks[0]
                    nBlocks = nBlocks[1:]
                    n_count = min(currentNBlock.end, regionEnd) - genomicPosition
                    sequenceBases.extend(['N'] * n_count)
                    genomicPosition += n_count
                    genomicPosition = genomicPosition - 1
                else:
                    bytePosition = math.floor(genomicPosition / 4) - baseBytesOffset
                    subPosition = genomicPosition % 4
                    byte = baseBytes[bytePosition]
                    if baseIsMasked:
                        sequenceBases.append(maskedByteTo4Bases[byte][subPosition])
                    else:
                        sequenceBases.append(byteTo4Bases[byte][subPosition])

                genomicPosition = genomicPosition + 1

            seqstring = ''.join(sequenceBases)
            return seqstring


    def _dataview(self, file_handle, offset, size):
        file_handle.seek(offset)
        bytes = file_handle.read(size)
        return DataView(bytes, self.byte_order)

class Block:
    def __init__(self, start, size):
        self.start = start
        self.end = start + size


def getOverlappingBlocks(start, end, blocks):

    overlappingBlocks = []

    for block in blocks:
        if block.start > end:
            break
        elif block.end < start:
            continue
        else:
            overlappingBlocks.append(block)

    return overlappingBlocks
