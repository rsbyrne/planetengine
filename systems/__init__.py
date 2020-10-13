from collections import OrderedDict
from functools import wraps
import numpy as np

import underworld as uw

from everest.utilities import w_hash, Grouper
from everest.builts._wanderer import Wanderer
from everest.builts._producer import OutsNull
from everest.builts._chroner import Chroner
from everest.builts._mutable import Mutant
from everest.builts._configurable import Config
from everest.prop import Prop

from .. import fieldops, mapping
from ..visualisation import QuickFig

from ..exceptions import PlanetEngineException, NotYetImplemented
from everest.builts import \
    BuiltException, MissingMethod, MissingAttribute, MissingKwarg
class SystemException(BuiltException, PlanetEngineException):
    pass
class SystemMissingMethod(MissingMethod, SystemException):
    pass
class SystemMissingAttribute(MissingAttribute, SystemException):
    pass
class SystemMissingKwarg(MissingKwarg, PlanetEngineException):
    pass
class SystemNotConstructed(SystemException):
    pass

def get_mesh_data(var):
    if type(var) == uw.mesh.MeshVariable:
        return var.mesh, var.mesh.data
    elif type(var) == uw.swarm.SwarmVariable:
        return var.swarm.mesh, var.swarm.data
    else:
        raise TypeError
def set_scales(var):
    if hasattr(var, 'scales'):
        fieldops.clip_var(var, var.scales)
def set_boundaries(var):
    if hasattr(var, 'bounds'):
        fieldops.set_boundaries(var, var.bounds)

def copy(fromVar, toVar, boxDims = None, tiles = None, mirrored = None):
    toCoords = mapping.box(
        *get_mesh_data(toVar),
        boxDims = boxDims,
        tiles = tiles,
        mirrored = mirrored
        )
    toVar.data[...] = fieldops.safe_box_evaluate(fromVar, toCoords)

class StateVar(Config, Mutant):
    def __init__(self, target, *props):
        self.host = target
        self._varProp = Prop(target, *props)
        super().__init__(target, *props)
        var = self.var
        self.shape = (var.mesh.nodesGlobal, var.nodeDofCount)
    def _name(self):
        return self._varProp.props[-1]
    def _var(self):
        return self._varProp()
    def _data(self):
        return self.var.data
    def _out(self):
        return fieldops.get_global_var_data(self.var)
    def _mutate(self, vals, indices = Ellipsis):
        var = self.var
        vals = np.array(vals)
        if indices is Ellipsis:
            if vals.shape == self.shape:
                vals = vals[var.mesh.data_nodegId.flatten()]
        else:
            nodes = var.mesh.data_nodegId.flatten().aslist()
            indices = [nodes.index(i) for i in indices]
        var.data[indices] = vals
        self.update()
    def _imitate(self, fromVar):
        if hasattr(fromVar, 'var'):
            copy(fromVar.var, self.var)
        else:
            self.mutate(fromVar)
        self.update()
    def update(self):
        var = self.var
        set_scales(var)
        set_boundaries(var)
    def _hashID(self):
        return self._varProp._hashID()

def _system_construct_if_necessary(func):
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        if not hasattr(self, 'locals'):
            self.system_construct()
        return func(self, *args, **kwargs)
    return wrapper

class System(Chroner, Wanderer):

    def __init__(self, **kwargs):

        si = self._sortedInputKeys['options']
        options = Grouper(OrderedDict([(k, self.inputs[k]) for k in si]))
        si = self._sortedInputKeys['params']
        params = Grouper(OrderedDict([(k, self.inputs[k]) for k in si]))
        si = self._sortedGhostKeys['configs']
        configs = Grouper(OrderedDict([(k, self.ghosts[k]) for k in si]))

        dOptions = options.copy()
        dOptions['hash'] = options.hashID
        dParams = params.copy()
        dParams['hash'] = params.hashID

        super().__init__(
            options = dOptions,
            params = dParams,
            _defaultConfigs = configs,
            supertype = 'System',
            **kwargs
            )

        self.params, self.options = params, options

    def system_construct(self):
        self.locals = self._system_construct(
            self.options,
            self.params,
            self.configs
            )
        self.mutables.clear()
        for k in self.configs.keys():
            self.mutables[k] = StateVar(self, 'locals', k)
        self.observables.clear()
        self.observables.update(self.locals)
        self.baselines.clear()
        self.baselines.update(
            {'mesh': fieldops.get_global_var_data(self.locals.mesh)}
            )
        if hasattr(self.locals, 'obsVars'):
            self._fig = QuickFig(*self.locals.obsVars)
        else:
            self._fig = QuickFig(self.mutables.values()[0])
    def _system_construct(self, locals):
        localObj = Grouper(locals)
        del localObj.self
        return localObj

    @property
    def constructed(self):
        return hasattr(self, 'locals')

    @_system_construct_if_necessary
    def _configure(self):
        super()._configure()
        for k, v in self.configs.items():
            if v is Ellipsis:
                self.mutables[k].var.data[...] = 0. # May be problematic

    def _voyager_changed_state_hook(self):
        super()._voyager_changed_state_hook()
        assert self.constructed
        for var in self.mutables.values():
            var.update()
        self.locals.update()

    def _iterate(self):
        dt = self.locals.integrate()
        self.indices.chron.value += dt
        super()._iterate()

    def _out(self):
        outs = super()._out()
        if hasattr(self, 'locals'):
            add = {vn: mut.data for vn, mut in self.mutables.items()}
        else:
            add = {vn: OutsNull for vn in self.configs.keys()}
        outs.update(add)
        return outs

    def _save(self):
        super()._save()
        self.writer.add_dict(self.baselines, 'baselines')

    @_system_construct_if_necessary
    def _load_process(self, outs):
        outs = super()._load_process(outs)
        for key, mut in self.mutables.items():
            mut.mutate(outs.pop(key))
        return outs

    @property
    def fig(self):
        if self._indexers_isnull or not hasattr(self, 'locals'):
            raise Exception("Nothing to show yet.")
        return self._fig
    def show(self):
        self.fig.show()

# Aliases
# from .conductive import Conductive
from .isovisc import Isovisc
# from .arrhenius import Arrhenius
# from .viscoplastic import Viscoplastic
# from .viscoplasticmaterial import ViscoplasticMaterial
