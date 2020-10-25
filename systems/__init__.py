from collections import OrderedDict
from functools import wraps
import numpy as np

import underworld as uw

from grouper import Grouper
from wordhash import w_hash
from everest.frames._wanderer import Wanderer
from everest.frames._observable import Observable #, _observation_mode
from everest.frames._producer import OutsNull
from everest.frames._chroner import Chroner
from everest.frames._stateful import State, Statelet
from everest.frames._configurable import Config

from .. import fieldops, mapping
from ..visualisation import QuickFig

from ..exceptions import PlanetEngineException, NotYetImplemented
from everest.frames import \
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

class SystemVar(Statelet):
    def __init__(self, var, name):
        super().__init__(var, name)
        var = self.var
        self.shape = (var.mesh.nodesGlobal, var.nodeDofCount)
        self._initialData = var.data[...]
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
        copy(fromVar.var, self.var)
        self.update()
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

class System(Observable, Chroner, Wanderer):

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

        # self._systemObserverClasses = self.ghosts['observers']

        super().__init__(
            options = dOptions,
            params = dParams,
            supertype = 'System',
            **kwargs
            )

        self.params, self.options = params, options

    def system_construct(self):
        self.locals = Grouper(self._system_construct(
            self.options,
            self.params,
            self.configs
            ))
        self.state.clear()
        for k in self.configs.keys():
            self.state[k] = SystemVar(self.locals[k], k)
        self.observables.clear()
        self.observables.update(self.locals)
        self.baselines.clear()
        self.baselines.update(
            {'mesh': fieldops.get_global_var_data(self.locals.mesh)}
            )
        if hasattr(self.locals, 'obsVars'):
            self._fig = QuickFig(*self.locals.obsVars)
        else:
            self._fig = QuickFig(self.state[0])

    @property
    def constructed(self):
        return hasattr(self, 'locals')

    def _configurable_changed_state_hook(self):
        for k, v in self.configs.items():
            if v is Ellipsis:
                self.state[k].var.data[...] = self.state[k]._initialData

    def _voyager_changed_state_hook(self):
        super()._voyager_changed_state_hook()
        assert self.constructed
        for var in self.state:
            var.update()
        self.locals.solve()

    def _iterate(self):
        dt = self.locals.integrate()
        self.indices.chron.value += dt
        super()._iterate()

    def _out(self):
        outs = super()._out()
        add = self.evaluate()
        outs.update(add)
        return outs
    def _evaluate(self):
        if hasattr(self, 'locals'):
            add = {vn: mut.data for vn, mut in self.state.items()}
        else:
            add = {vn: OutsNull for vn in self.configs.keys()}
        return add

    def _save(self):
        super()._save()
        self.writer.add_dict(self.baselines, 'baselines')

    @_system_construct_if_necessary
    def _load_process(self, outs):
        outs = super()._load_process(outs)
        for key, mut in self.state.items():
            mut.mutate(outs.pop(key))
        return outs

    @property
    def fig(self):
        if self.indices.isnull or not hasattr(self, 'locals'):
            raise Exception("Nothing to show yet.")
        return self._fig
    def show(self):
        self.fig.show()

    def _observation_mode_hook(self):
        if self.indices.isnull:
            self.initialise()
        super()._observation_mode_hook()

# Aliases
# from .conductive import Conductive
from .isovisc import Isovisc
# from .arrhenius import Arrhenius
# from .viscoplastic import Viscoplastic
# from .viscoplasticmaterial import ViscoplasticMaterial
