name = 'test'
outputPath = '.'

from planetengine.systems.isovisc import Isovisc

system = Isovisc()
system.anchor(name, outputPath)
