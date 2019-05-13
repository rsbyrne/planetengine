import underworld as uw
from planetengine.mapping import box
from planetengine.utilities import copyField
from planetengine.utilities import setboundaries
from planetengine import frame
import underworld as uw
import numpy as np
import os

LOADTYPE = True

class IC:

    def __init__(
            self,
            inFrame = None,
            sourceVarName = None,
            loadStep = None,
            hashID = None,
            _outputPath = '',
            ):

        assert sourceVarName is not None, \
            "sourceVarName input must be a string correlating to a varsOfState attribute on the input frame."
        assert inFrame is not None or type(hashID) == str, \
            "Must provide a str or frame instance for 'inFrame' keyword argument."

        self.inputs = locals().copy()
        del self.inputs['self']
        del self.inputs['inFrame']
        del self.inputs['_outputPath']
        self.script = __file__

        self.sourceVarName = sourceVarName
        if loadStep is None:
            if type(inFrame) == frame.Frame:
                self.loadStep = inFrame.step
            else:
                self.loadStep = 0
            self.inputs['loadStep'] = self.loadStep
        else:
            self.loadStep = loadStep

        if inFrame is None and type(hashID) == str:
            self.inFrame = frame.load_frame(_outputPath, hashID, loadStep = self.loadStep)
        elif type(inFrame) == str:
            self.inFrame = frame.load_frame(inFrame, loadStep = self.loadStep)
        elif type(inFrame) == frame.Frame:
            self.inFrame = inFrame
            self.inFrame.load_checkpoint(self.loadStep)
        else:
            raise Exception("inFrame input not recognised.")
        self.inputs['hashID'] = self.inFrame.hashID
        self.inVar = self.inFrame.system.varsOfState[self.sourceVarName]
        if not type(self.inVar) == uw.mesh._meshvariable.MeshVariable:
            try:
                self.inVar = self.inFrame.projections[self.sourceVarName]
                if not self.inFrame.allProjected:
                    self.inFrame.project(self.sourceVarName)
            except:
                pass

    def apply(self, outVar, boxDims = None):

        if boxDims is None:
            tolerance = copyField(self.inVar, outVar)
        else:
            tolerance = copyField(self.inVar, outVar, boxDims)