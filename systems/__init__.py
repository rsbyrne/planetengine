from collections import OrderedDict
from functools import wraps

import underworld as uw

from everest.utilities import w_hash, Grouper
from everest.builts._wanderer import Wanderer
from everest.builts._producer import OutsNull
from everest.builts._chroner import Chroner
from everest.builts._mutable import Mutant

from .. import fieldops, mapping

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
    set_scales(toVar)
    set_boundaries(toVar)

class StateVar(Mutant):
    def __init__(self, target, *props):
        super().__init__(target, *props)
    def _data(self):
        return fieldops.get_global_var_data(self.var)
    def _mutate(self, data):
        var = self.var
        var.data[...] = data[var.mesh.data_nodegId.flatten()]
        self.update
    def _imitate(self, fromVar):
        copy(fromVar.var, self.var)
    def update(self):
        var = self.var
        set_scales(var)
        set_boundaries(var)

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
        self.mutables.update({
            key: StateVar(self, 'locals', key)
                for key in self.configs.keys()
            })
        self.observables.clear()
        self.observables.update(self.locals)
        self.baselines.clear()
        self.baselines.update(
            {'mesh': fieldops.get_global_var_data(self.locals.mesh)}
            )
    def _system_construct(self, locals):
        localObj = Grouper(locals)
        del localObj.self
        return localObj

    @_system_construct_if_necessary
    def _configure(self):
        super()._configure()

    def _voyager_changed_state_hook(self):
        super()._voyager_changed_state_hook()
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

# Aliases
# from .conductive import Conductive
from .isovisc import Isovisc
# from .arrhenius import Arrhenius
# from .viscoplastic import Viscoplastic
# from .viscoplasticmaterial import ViscoplasticMaterial
