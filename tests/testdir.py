import sys
import os
import shutil
import subprocess
import underworld as uw

workpath = '/home/jovyan/workspace'
outputPath = os.path.join(workpath, 'data/test')

class TestDir:

    def __init__(self):
        self.workpath = workpath
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
            if not self.workpath in sys.path:
                sys.path.append(self.workpath)
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
