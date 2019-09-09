import sys
import os
import shutil
import subprocess
import traceback
import underworld as uw

workPath = '/home/jovyan/workspace'
if not workPath in sys.path:
    sys.path.append(workPath)
# ignoreme = subprocess.call(['chmod', '-R', '777', workPath])
outPath = '/home/jovyan/workspace/out'
if not os.path.isdir(outPath):
    os.makedirs(outPath)
# ignoreme = subprocess.call(['chmod', '-R', '777', outPath])
testPath = '/home/jovyan/workspace/out/test'
defaultPath = os.path.join(outPath, 'default')
if not os.path.isdir(defaultPath):
    os.makedirs(defaultPath)
# ignoreme = subprocess.call(['chmod', '-R', '777', defaultPath])
ignoreme = subprocess.call(['chmod', '-R', '777', outPath])

class TestDir:

    def __init__(self):
        self.workPath = workPath
        self.outputPath = testPath
        pass

    def __enter__(self):
        outputPath = make_testdir()
        return outputPath # accessed using 'as' after 'with'

    def __exit__(self, *args):
        exc_type, exc_value, tb = args
        if exc_type is not None:
            traceback.print_exception(exc_type, exc_value, tb)
            return False
        delete_testdir()
        return True

def make_testdir():

    if uw.mpi.rank == 0:
        if not workPath in sys.path:
            sys.path.append(workPath)
        delete_testdir()
        os.makedirs(testPath)
        ignoreme = subprocess.call(
            ['chmod', '-R', '777', testPath]
            )
    return testPath

def delete_testdir():
    if uw.mpi.rank == 0:
        if os.path.isdir(testPath):
            subprocess.call(
                ['chmod', '-R', '777', testPath]
                )
            shutil.rmtree(testPath)
