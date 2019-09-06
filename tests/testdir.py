import sys
import os
import shutil
import subprocess

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
        subprocess.call(['chmod', '-R', '777', self.outputPath])
        shutil.rmtree(self.outputPath)
        return True

    def make_testdir(self):
        import sys
        import os
        import shutil
        import subprocess
        sys.path.append(self.workpath)
        if os.path.isdir(self.outputPath):
            subprocess.call(['chmod', '-R', '777', self.outputPath])
            shutil.rmtree(self.outputPath)
        os.mkdir(self.outputPath)
        ignoreme = subprocess.call(['chmod', '-R', '777', self.outputPath])
        return self.outputPath
