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

    def seek(self, offet):
        self.offset = offet

    def tell(self):
        return self.offset

    def close(self):
        self.offset = 0

    def read(self, n):

        if n == 0:
            return b''

        end = self.offset + n - 1
        headers = {
            "Content-Type":"application/octet-stream",
            "Range":f"bytes={self.offset}-{end}"}
        response = requests.get(self.url, headers = headers)
        bytes = response.content
        return bytes

    def size(self):

        response = requests.head(self.url)
        sz = response.headers.get('content-length')
        return int(sz) if sz is not None else None

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        pass
