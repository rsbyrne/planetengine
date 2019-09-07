import sys
import os
import shutil
import subprocess
import traceback
import underworld as uw
from .. import workPath
from .. import testPath as outputPath

class TestDir:

    def __init__(self):
        self.workPath = workPath
        self.outputPath = outputPath
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
        os.makedirs(outputPath)
        ignoreme = subprocess.call(
            ['chmod', '-R', '777', outputPath]
            )
    return outputPath

def delete_testdir():
    if uw.mpi.rank == 0:
        if os.path.isdir(outputPath):
            subprocess.call(
                ['chmod', '-R', '777', outputPath]
                )
            shutil.rmtree(outputPath)
