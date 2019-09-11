import os

from planetengine import frame
from planetengine.fieldops import copyField
from planetengine.initials._IC import _IC

def build(*args, name = None, **kwargs):
    built = IC(*args, **kwargs)
    if type(name) == str:
        built.name = name
    return built

class IC(_IC):

    script = __file__

    def __init__(
            self,
            *args,
            inFrame = None,
            varName = None,
            _loadStep = None,
            **kwargs
            ):

        assert not varName is None
        if isinstance(inFrame, frame.Frame): # hence new
            assert _loadStep is None
            _loadStep = inFrame.step
        elif type(inFrame) == str: # hence loaded
            assert type(_loadStep) == int
            outputPath = os.path.dirname(self.script)
            inFrame = frame.load_frame(
                outputPath,
                inFrame,
                loadStep = _loadStep
                )
        else:
            raise Exception

        self.inFrame = inFrame
        self.inVar = inFrame.saveVars[varName]

        inputs = {
            'varName': varName,
            '_loadStep': _loadStep,
            'inFrame': inFrame.instanceID
            }

        super().__init__(
            args = args,
            kwargs = kwargs,
            inputs = inputs,
            script = self.script
            )

    def evaluate(self, coordArray):
        return coordArray

    def _apply(self, var, boxDims = None):
        tolerance = copyField(self.inVar, var)

    def _pre_save_hook(self, path, name = None):
        path = os.path.join(path, self.inFrame.instanceID)
        self.inFrame.checkpoint(path)
