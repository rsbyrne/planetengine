import sys
import os
import shutil
import subprocess
import traceback

from . import mpi

workPath = '/home/jovyan/workspace'
outPath = os.path.join(workPath, 'out')
testPath = os.path.join(outPath, 'test')
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
        ignoreme = subprocess.call(['chmod', '-R', '777', testPath])
    # mpi.barrier()

    return testPath

def delete_testdir():
    if mpi.rank == 0:
        if os.path.isdir(testPath):
            shutil.rmtree(testPath)
        if os.path.isdir(testPath):
            raise Exception
    # mpi.barrier()
