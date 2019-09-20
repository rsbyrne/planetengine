import sys

script = str(sys.argv[1])
chunks = int(sys.argv[2])
jobs
coresperchunk = int(sys.argv[4])

import subprocess

while
subprocess.call(['chmod', '-R', '777', workPath])
subprocess.call([
    'mpirun',
    '-np',
    str(coresperchunk),
    'python',
    str(script),
    str(chunks),
    str(chunkno),
    str(iterno)
    ])
