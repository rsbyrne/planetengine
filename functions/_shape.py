import underworld as uw
_fn = uw.function
UWFn = _fn._function.Function

from . import _basetypes
from . import _planetvar
from .. import utilities
hasher = utilities.hashToInt
from .. import shapes
from .. import mapping

class Shape(_basetypes.BaseTypes):

    opTag = 'Shape'

    def __init__(self, vertices, varName = None, *args, **kwargs):

        shape = _fn.shape.Polygon(vertices)
        self.vertices = vertices
        self.richvertices = vertices
        self.richvertices = shapes.interp_shape(self.vertices, num = 1000)
        self.morphs = {}
        self._currenthash = hasher(self.vertices)

        self.defaultName = str(self._currenthash)
        self.varName = varName

        self._hashVars = [self.vertices,]
        # self.data = self.vertices

        self.stringVariants = {'varName': varName}
        self.inVars = []
        self.parameters = []
        self.var = shape
        self.mesh = self.substrate = None

        super().__init__(**kwargs)

    def _check_hash(self, **kwargs):
        return self._currenthash

    def morph(self, mesh):
        try:
            morphpoly = self.morphs[mesh]
        except:
            morphverts = mapping.unbox(mesh, self.richvertices)
            morphpoly = _fn.shape.Polygon(morphverts)
            self.morphs[mesh] = morphpoly
        return morphpoly
