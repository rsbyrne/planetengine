import underworld as uw
from planetengine import mapping
from planetengine.utilities import meshify
from planetengine import frame
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
            _is_child = False,
            ):

        assert sourceVarName is not None, \
            "sourceVarName input must be a string \
            correlating to a varsOfState attribute \
            on the input frame."
        assert inFrame is not None or type(hashID) == str, \
            "Must provide a str or frame instance \
            for 'inFrame' keyword argument."

        self.inputs = {
            'sourceVarName': sourceVarName,
            'loadStep': loadStep
            }
        self.script = __file__

        self.LOADTYPE = None

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
            self.inFrame = frame.load_frame(
                _outputPath,
                hashID,
                loadStep = self.loadStep,
                _is_child = _is_child
                )
        elif type(inFrame) == str:
            self.inFrame = frame.load_frame(
                os.path.dirname(inFrame),
                os.path.basename(inFrame),
                loadStep = self.loadStep,
                _is_child = _is_child
                )
        elif type(inFrame) == frame.Frame:
            self.inFrame = inFrame
            self.inFrame.load_checkpoint(self.loadStep)
        else:
            raise Exception("inFrame input not recognised.")

        self.inputs['hashID'] = self.inFrame.hashID

        self.inVar = self.inFrame.system.varsOfState[self.sourceVarName]