import sys
import os
import shutil
import subprocess
import traceback
import underworld as uw
from .. import workdir
from .. import outdir

workPath = workdir
outputPath = os.path.join(outdir, 'test')

class TestDir:

    def __init__(self):
        self.workPath = workPath
        self.outputPath = outputPath
        pass

    def __enter__(self):
        outputPath = self.make_testdir()
        return outputPath # accessed using 'as' after 'with'

    def __exit__(self, *args):
        exc_type, exc_value, tb = args
        if exc_type is not None:
            traceback.print_exception(exc_type, exc_value, tb)
            return False
        self.delete_testdir()
        return True

    def make_testdir(self):
        import sys
        import os
        import shutil
        import subprocess
        if uw.mpi.rank == 0:
            if not self.workPath in sys.path:
                sys.path.append(self.workPath)
            if os.path.isdir(self.outputPath):
                ignoreme = subprocess.call(['chmod', '-R', '777', self.outputPath])
                shutil.rmtree(self.outputPath)
            os.makedirs(self.outputPath)
            ignoreme = subprocess.call(['chmod', '-R', '777', self.outputPath])
        return self.outputPath

    def delete_testdir(self):
        if uw.mpi.rank == 0:
            subprocess.call(['chmod', '-R', '777', self.outputPath])
            shutil.rmtree(self.outputPath)
