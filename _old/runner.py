# import sys
# import os
#
# script = str(sys.argv[1])
# chunks = int(sys.argv[2])
# coresperchunk = int(sys.argv[4])
#
# from .utilities import hashstamp
# from . import mpi
# from .paths import workPath
# from . import disk
#
# import time
# presenttime = None
# if mpi.rank == 0:
#     presenttime = time.time()
# presenttime = mpi.comm.bcast(presenttime, root = 0)
#
# campaignName = hashstamp([script, presenttime])
# campaignLog = []
# disk.save_json(campaignName, workPath)
#
# chunksIter = [[]] * chunks
#
# import subprocess
#
# while True
#     for chunk in chunks:
#         iterno = 0
#         while True:
#             campaignLog = disk.load_json(campaignName, workPath)
#             if
#             with open(campaignFile, 'w') as file:
#                 file.write(campaignName)
#             subprocess.call([
#                 'mpirun',
#                 '-np',
#                 str(coresperchunk),
#                 'python',
#                 str(script),
#                 str(chunks),
#                 str(chunkno),
#                 str(iterno),
#                 campaignName
#                 ])
#             iterno += 1
