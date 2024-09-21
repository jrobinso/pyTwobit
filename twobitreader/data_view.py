

class DataView:

    def __init__(self, bytes, byte_order):

        self.bytes = bytes
        self.position = 0
        self.byte_order = byte_order


    def getByte(self):
        val = self.bytes[self.position]
        self.position = self.position + 1
        return val

    def getString(self, length):
        val = self.bytes[self.position:self.position+length].decode('utf8')
        self.position = self.position + length
        return val

    def uint32(self):

        val =  int.from_bytes(self.bytes[self.position:self.position+4], self.byte_order)
        self.position = self.position + 4
        return val


    def available(self):

        return len(self.bytes) - self.position