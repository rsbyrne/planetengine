import underworld as uw
import numpy as np
import os

from .. import paths
from .. import mapping
from .. import frames
from ._IC import _IC

def build(*args, **kwargs):
    return IC(*args, **kwargs)

class IC(_IC):

    def __init__(
            self,
            inFrame = None,
            sourceVarName = None,
            loadStep = None,
            hashID = None,
            _outputPath = None,
            _is_child = False
            ):

        if _outputPath is None:
            _outputPath = paths.defaultPath

        assert sourceVarName is not None, \
            "sourceVarName input must be a string \
            correlating to a varsOfState attribute \
            on the input model."
        assert inFrame is not None or type(hashID) == str, \
            "Must provide a str or model instance \
            for 'inFrame' keyword argument."

        self.inputs = {
            'sourceVarName': sourceVarName,
            'loadStep': loadStep
            }
        script = os.path.join(
            os.path.dirname(__file__),
            '_load_dummy.py'
            )
        self.script = script

        self.sourceVarName = sourceVarName
        if loadStep is None:
            if type(inFrame) == model.ModelFrame:
                self.loadStep = inFrame.step
            else:
                self.loadStep = 0
            self.inputs['loadStep'] = self.loadStep
        else:
            self.loadStep = loadStep

        if inFrame is None and type(hashID) == str:
            self.inFrame = frames.load_frame(
                _outputPath,
                hashID,
                _is_child = _is_child
                )

        elif type(inFrame) == str:
            self.inFrame = frames.load_frame(
                os.path.dirname(inFrame),
                os.path.basename(inFrame),
                _is_child = _is_child
                )
        elif isinstace(inFrame, frame.Frame):
            self.inFrame = inFrame
            self.inFrame.load_checkpoint(self.loadStep)
        else:
            raise Exception("inFrame input not recognised.")

        self.inFrame.load_checkpoint(self.loadStep)

        self.inputs['hashID'] = self.inFrame.hashID

        self.inVar = self.inFrame.saveVars[self.sourceVarName]

        try:
            self.varDim = self.inVar.nodeDofCount
            self.meshDim = self.inVar.mesh.dim
        except:
            self.varDim = self.inVar.count
            self.meshDim = self.inVar.swarm.mesh.dim

        super().__init__()
