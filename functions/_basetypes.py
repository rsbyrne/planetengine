class BaseTypes(PlanetVar):

    def __init__(self, *args, **kwargs):
        super().__init__(**kwargs)

    def evaluate(self, evalInput = None, **kwargs):
        if evalInput is None:
            evalInput = self.substrate
        return self.var.evaluate(evalInput)

    # def _update(self, **kwargs):
    #     self._partial_update()
    #     # self._set_summary_stats()

    def __call__(self):
        return self.var

class Constant(BaseTypes):

    opTag = 'Constant'

    def __init__(self, inVar, *args, **kwargs):

        var = UWFn.convert(inVar)
        if var is None:
            raise Exception
        if len(list(var._underlyingDataItems)) > 0:
            raise Exception

        self.value = var.evaluate()[0]
        valString = utilities.stringify(
            self.value
            )
        self._currenthash = hasher(self.value)
        self._hashVars = [var]
        # self.data = np.array([[val,] for val in self.value])

        sample_data = np.array([[val,] for val in self.value])
        self.dType = get_dType(sample_data)
        self.varType = 'const'

        self.stringVariants = {'val': valString}
        self.inVars = []
        self.parameters = []
        self.var = var
        self.mesh = self.substrate = None
        self.meshUtils = None
        self.meshbased = False

        super().__init__(**kwargs)

    def _check_hash(self, **kwargs):
        return self._currenthash

class Parameter(BaseTypes):

    opTag = 'Parameter'

    def __init__(self, inFn, **kwargs):

        initialVal = inFn()
        var = fn.misc.constant(initialVal)
        if not len(list(var._underlyingDataItems)) == 0:
            raise Exception

        self._hashVars = []
        self.stringVariants = {}
        self.inVars = []
        self.parameters = []
        self.var = var
        self.mesh = self.substrate = None

        self._paramfunc = inFn
        self._hashval = random.randint(1, 1e18)

        self._update_attributes()
        sample_data = np.array([[val,] for val in self.value])
        self.dType = get_dType(sample_data)

        super().__init__(**kwargs)

    def _check_hash(self, **kwargs):
        return random.randint(0, 1e18)

    def _update_attributes(self):
        self.value = self.var.evaluate()[0]
        # self.data = np.array([[val,] for val in self.value])

    def _partial_update(self):
        self.var.value = self._paramfunc()
        self._update_attributes()

    def __hash__(self):
        return self._hashval

class Variable(BaseTypes):

    opTag = 'Variable'

    defaultName = 'anon'

    convertTypes = {
        uw.mesh._meshvariable.MeshVariable,
        uw.swarm._swarmvariable.SwarmVariable
        }

    def __init__(self, inVar, varName = None, *args, **kwargs):

        var = UWFn.convert(inVar)

        if var is None:
            raise Exception
        if len(list(var._underlyingDataItems)) == 0:
            raise Exception

        if varName is None:
            if hasattr(var, 'name'):
                varName = var.name
            else:
                varName = self.defaultName

        if not type(var) in self.convertTypes:
            vanillaVar = Vanilla(var)
            projVar = vanillaVar.meshVar()
            var = projVar.var
            self._projUpdate = projVar.update
            if hasattr(vanillaVar, 'scales'):
                var.scales = vanillaVar.scales
            if hasattr(vanillaVar, 'bounds'):
                var.bounds = vanillaVar.bounds

        self.data = var.data

        if type(var) == uw.mesh._meshvariable.MeshVariable:
            self.substrate = self.mesh = var.mesh
            self.meshdata = self.data
            self.meshbased = True
            self.varType = 'meshVar'
        elif type(var) == uw.swarm._swarmvariable.SwarmVariable:
            self.substrate = var.swarm
            self.mesh = var.swarm.mesh
            self.meshbased = False
            self.varType = 'swarmVar'
        else:
            raise Exception

        self._hashVars = [var]

        self.stringVariants = {'varName': varName}
        self.inVars = []
        self.parameters = []
        self.var = var

        if not varName == self.defaultName:
            var._planetVar = weakref.ref(self)
        # self._set_meshdata()

        sample_data = self.data[0:1]
        self.dType = get_dType(sample_data)
        self.varDim = self.data.shape[1]
        self.meshUtils = get_meshUtils(self.mesh)

        if hasattr(var, 'scales'):
            self.scales = var.scales
        if hasattr(var, 'bounds'):
            self.bounds = var.bounds

        super().__init__(**kwargs)

    def _check_hash(self, lazy = False):
        if lazy and hasattr(self, '_currenthash'):
            return self._currenthash
        else:
            currenthash = hasher(self.data)
            self._currenthash = currenthash
        return currenthash

    def _set_meshdata(self):
        self.meshdata = self.var.evaluate(self.mesh)

    def _partial_update(self):
        if hasattr(self, '_projUpdate'):
            self._projUpdate()
        if not type(self.var) == uw.mesh._meshvariable.MeshVariable:
            self._set_meshdata()

class Shape(BaseTypes):

    opTag = 'Shape'

    defaultName = 'anon'

    def __init__(self, vertices, varName = None, *args, **kwargs):

        if varName is None:
            varName = self.defaultName

        shape = fn.shape.Polygon(vertices)
        self.vertices = vertices
        self.richvertices = vertices
        self.richvertices = interp_shape(self.vertices, num = 1000)
        self.morphs = {}
        self._currenthash = hasher(self.vertices)

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
            morphverts = unbox(mesh, self.richvertices)
            morphpoly = fn.shape.Polygon(morphverts)
            self.morphs[mesh] = morphpoly
        return morphpoly
