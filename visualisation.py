from underworld import function as fn
import glucifer
import numpy as np
import os

from . import functions as pfn
from .utilities import message
from .functions import convert
from . import functions as pfn
from .meshutils import get_meshUtils

from . import mpi

def quickShow(*args, **kwargs):

    quickFig = QuickFig(*args, **kwargs)
    quickFig.show()

styles = {
    'smallblack': {
        'colourBar': False,
        'facecolour': 'black',
        'quality': 2,
        'figsize': (300, 300)
        }
    }

class QuickFig:

    def __init__(self, *args, figname = 'default', style = {}):

        if type(style) == str:
            style = styles[style]
        elif not type(style) == dict:
            raise Exception

        if not style == {}:
            self.fig = glucifer.Figure(**style)
        else:
            self.fig = glucifer.Figure()

        self.figname = figname
        self.features = set()
        self.fittedvars = []
        self.updateFuncs = []

        self.vars = []
        self.planetVars = []

        self.inventory = [
            self.add_surface,
            self.add_contours,
            self.add_arrows,
            self.add_points,
            self.add_stipple
            ]

        self.functions_used = []

        self.add_vars(args)

    def add_vars(self, args):

        args = list(args)

        if len(args) == 1 and type(args[0]) == dict:
            args = sorted(args[0].items())
        for arg in args:
            if hasattr(arg, 'subMesh'):
                args.remove(arg)
                self.add_grid(arg)
            elif hasattr(arg, 'particleCoordinates'):
                args.remove(arg)
                self.add_swarm(arg)
        for arg in args:
            if type(arg) == tuple:
                varName, var = arg
                planetVar = convert(var, varName)
            else:
                var = arg
                planetVar = convert(var)
            self.planetVars.append(planetVar)
            self.updateFuncs.append(planetVar.update)

        for planetVar in self.planetVars:
            found = False
            for function in self.inventory:
                if not function in self.functions_used:
                    if not found:
                        try:
                            function(planetVar)
                            found = True
                            self.functions_used.append(function)
                        except:
                            continue
            if found:
                self.fittedvars.append(planetVar)
        self.notfittedvars = [var for var in self.vars if not var in self.fittedvars]

        message(
            "Fitted " + str(len(self.fittedvars)) + " variables to the figure."
            )

    def add_grid(self, arg, **kwargs):
        self.fig.append(
            glucifer.objects.Mesh(
                arg,
                **kwargs
                )
            )

    def add_swarm(self, arg, **kwargs):
        self.fig.append(
            glucifer.objects.Points(
                arg,
                fn_size = 1e3 / float(arg.particleGlobalCount)**0.5,
                **kwargs
                )
            )

    def add_stipple(self, arg, **kwargs):
        planetVar = convert(arg)
        if not planetVar.valSets == [{0., 1.}]:
            raise Exception
        if not planetVar.varDim == 1:
            raise Exception
        drawing = glucifer.objects.Drawing(
            pointsize = 3.,
            )
        allCoords = planetVar.meshUtils.cartesianScope
        for coord in allCoords:
            try:
                val = planetVar.evaluate(np.array([coord]))
                if bool(val):
                    drawing.point(coord)
            except:
                pass
        self.fig.append(drawing)

    def add_surface(self, arg, **kwargs):
        planetVar = convert(arg)
        if not planetVar.varDim == 1:
            raise Exception
        self.fig.append(
            glucifer.objects.Surface(
                planetVar.mesh,
                planetVar,
                **kwargs
                )
            )

    def add_contours(self, arg, **kwargs):
        planetVar = convert(arg)
        normed = pfn.Normalise(
            planetVar, [2., 1024.]
            )
        self.updateFuncs.append(normed.update)
        if 0. in planetVar.valSets:
            raise Exception
        if not planetVar.varDim == 1:
            raise Exception
        self.fig.append(
            glucifer.objects.Contours(
                planetVar.mesh,
                fn.math.log2(normed),
                colours = "red black",
                interval = 1.,
                **kwargs
                )
            )

    def add_arrows(self, arg, **kwargs):
        planetVar = convert(arg)
        if not planetVar.varDim == planetVar.mesh.dim:
            raise Exception
        self.fig.append(
            glucifer.objects.VectorArrows(
                planetVar.mesh,
                planetVar,
                **kwargs
                )
            )

    def add_points(self, arg, **kwargs):
        planetVar = convert(arg)
        # if not planetVar.varType in {'swarmVar' or 'swarmFn'}:
        #     raise Exception
        if not planetVar.varDim == 1:
            raise Exception
        self.fig.append(
            glucifer.objects.Points(
                planetVar.substrate,
                fn_colour = planetVar,
                fn_mask = planetVar,
                opacity = 0.5,
                fn_size = 1e3 / float(planetVar.substrate.particleGlobalCount)**0.5,
                colours = "purple green brown pink red",
                **kwargs
                )
            )

    def update(self):
        for updateFunc in self.updateFuncs:
            updateFunc()

    def show(self):
        self.update()
        for var in self.fittedvars:
            message(var.varName)
        self.fig.show()

    def save(self, path = '', name = None):
        self.update()
        if name is None:
            name = self.figname
        if mpi.rank == 0:
            if not os.path.isdir(path):
                os.mkdir(path)
            assert os.path.isdir(path)
        # mpi.barrier()
        self.fig.save(os.path.join(path, name))
