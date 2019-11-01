import sys
workpath = '/home/jovyan/workspace'
if not workpath in sys.path:
    sys.path.append(workpath)

from planetengine import tests

# tests.archivertest.testfn()
# tests.framestest.testfn()
tests.functionstest.testfn()
print(planetengine.fieldops.fullLocalMeshVars)
tests.functionstest.testfn()
