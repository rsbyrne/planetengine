import sys
import os
import shutil
import subprocess
import traceback

from . import mpi

workPath = '/home/jovyan/workspace'
# if not workPath in sys.path:
#     sys.path.append(workPath)
# ignoreme = subprocess.call(['chmod', '-R', '777', workPath])
outPath = os.path.join(workPath, 'out')
# if not os.path.isdir(outPath):
#     os.makedirs(outPath)
# ignoreme = subprocess.call(['chmod', '-R', '777', outPath])
testPath = os.path.join(outPath, 'test')
# defaultPath = os.path.join(outPath, 'default')
# if not os.path.isdir(defaultPath):
#     os.makedirs(defaultPath)
# ignoreme = subprocess.call(['chmod', '-R', '777', defaultPath])
# ignoreme = subprocess.call(['chmod', '-R', '777', outPath])
defaultPath = os.path.join(outPath, 'default')

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

def liberate_paths():
    subprocess.call(
        ['chmod', '777', workPath]
        )
    subprocess.call(
        ['chmod', '777', outPath]
        )
    subprocess.call(
        ['chmod', '777', testPath]
        )

def make_testdir():

    delete_testdir()

    if mpi.rank == 0:
        os.makedirs(testPath)
        assert os.path.isdir(testPath)
    # mpi.barrier()

    return testPath

def delete_testdir():
    if mpi.rank == 0:
        if os.path.isdir(testPath):
            shutil.rmtree(testPath)
        if os.path.isdir(testPath):
            raise Exception
    # mpi.barrier()
