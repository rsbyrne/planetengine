import underworld as uw
import numpy as np
from .. import fieldops
from ..utilities import message
class AsciiRaster:
    def __init__(self, inVar, size = 10):
        mesh = uw.mesh.FeMesh_Cartesian(
            elementRes = (size - 1, size - 1)
            )
        self.var = mesh.add_variable(1)
        self.var.scales = [[0., 9.]]
        self.inVar = inVar
        self.greyscale = " .:-=+*#%@"
        self.outStr = ''
        self.allStr = ''
        self.size = size
        self.update()
    def update(self):
        tolerance = fieldops.copyField(
            self.inVar,
            self.var
            )
        mangledArray = np.round(
            np.flip(
                self.var.data.reshape([self.size, self.size]), axis = 0
                )
            ).astype('int')
        outStr = ''
        for row in mangledArray:
            for val in row:
                newChar = self.greyscale[val]
                outStr += newChar
            outStr += '\n'
        self.outStr = outStr
        self.allStr += outStr
    def reset(self):
        self.allStr = ''
    def show(self):
        self.update()
        message(self.outStr)
    def allshow(self):
        message(self.allStr)
    def prettyshow(self):
        self.update()
        print(prettify(self.outStr))
    def allprettyshow(self):
        message(prettify(self.allStr))
    def __call__(self):
        self.update()
        return self.outStr
def prettify(string):
    prettyStr = ''
    for character in string:
        if character == '\n':
            prettyStr += '\n'
        else:
            prettyStr += character * 2
    return prettyStr
