name = 'test'
outputPath = '.'

from everest.builts import set_global_anchor
set_global_anchor(name, outputPath, purge = True)

from planetengine.systems.isovisc import Isovisc
from planetengine.traverse import Traverse

Traverse(Isovisc, 10)()
