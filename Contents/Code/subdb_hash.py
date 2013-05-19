# http://thesubdb.com/api/

import os, sys, hashlib

filename = sys.argv[1]
readsize = 64 * 1024

with open(filename, 'rb') as f:
  data = f.read(readsize)
  f.seek(-readsize, os.SEEK_END)
  data += f.read(readsize)

print hashlib.md5(data).hexdigest()
