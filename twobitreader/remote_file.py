import requests

class RemoteFile:

    """
    A "file like" object for random access to a remote binary file.   Used in place of a local file
    handle in 'array.fromfile' calls.  Includes a simple buffer to redunce the number of http requests
    for small bits of data.
    """
    def __init__(self, url):
        self.url = url
        self.offset = 0
        self.buffer_size = 0
        self.buffer_start = 0
        self.buffer = b''

    def seek(self, offet):
        self.offset = offet

    def tell(self):
        return self.offset

    def close(self):
        self.offset = 0
        self.buffer_start = 0
        self.buffer = b''

    def read(self, n):

        if n == 0:
            return b''

        if(n > self.buffer_size):
            self.buffer = b''
            bytes = fetch(self.url, self.offset, n)
        else:
            buffer_end = self.buffer_start + len(self.buffer)
            if self.offset < self.buffer_start or self.offset + n > buffer_end:
                # Refill buffer
                self.buffer = fetch(self.url, self.offset, self.buffer_size)
                self.buffer_start = self.offset
            s = self.offset - self.buffer_start
            bytes = self.buffer[s : s+n]

        self.offset += n
        return bytes


    def size(self):

        response = requests.head(self.url)
        sz = response.headers.get('content-length')
        return int(sz) if sz is not None else None

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        pass

def fetch(url, start, n) :

    end = start + n - 1
    headers = {
        "Content-Type":"application/octet-stream",
        "Range":f"bytes={start}-{end}"}

    print(f"{start} - {end}")

    response = requests.get(url, headers = headers)
    bytes = response.content
    return bytes