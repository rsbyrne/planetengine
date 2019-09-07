import sys
workpath = '/home/jovyan/workspace'
if not workpath in sys.path:
    sys.path.append(workpath)

from planetengine import tests

tests.framestest()
tests.functionstest()
