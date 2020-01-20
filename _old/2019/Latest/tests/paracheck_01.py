import h5py
import os

import everest

IC = everest.examples.myobject2.build(400.)
system = everest.examples.myobject1.build(a = 1, b = 0.5, initial_time = IC)

outputPath = ''
name = 'test'
extension = 'h5'
path = os.path.join(outputPath, name + '.' + extension)
if everest.mpi.rank == 0:
    if os.path.exists(path):
        os.remove(path)

system.anchor(path)

for i in range(10):
    system.go(10)
    system.store()
system.save()
for i in range(10):
    system.go(10)
    system.store()
system.save()
system.load(20)
for i in range(10):
    system.go(10)
    system.store()
system.save()

if everest.mpi.rank == 0:
    with h5py.File(path) as h5file:
        print(h5file[system.hashID]['var']['data'][...])
