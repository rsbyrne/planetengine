import os

from planetengine import frame
from planetengine import fieldops
from planetengine import mapping
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
        self.fullInField = fieldops.make_fullLocalMeshVar(self.inVar)

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
        tolerance = 0.
        while tolerance < 0.1:
            try:
                evalCoords = mapping.unbox(
                    self.fullInField.mesh,
                    coordArray,
                    tolerance = tolerance
                    )
                outArray = self.fullInField.evaluate(evalCoords)
                break
            except:
                if tolerance == 0.:
                    tolerance += 0.00001
                else:
                    tolerance *= 1.01
        raise Exception("Acceptable tolerance for load IC could not be found.")

        return outArray

    # def _apply(self, var, boxDims = None):
    #     tolerance = fieldops.copyField(self.inVar, var)

    def _pre_save_hook(self, path, name = None):
        path = os.path.join(path, self.inFrame.instanceID)
        self.inFrame.checkpoint(path)
