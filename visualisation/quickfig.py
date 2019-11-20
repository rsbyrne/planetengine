from underworld import function as _fn
import glucifer
import numpy as np
import os

from .. import functions as pfn
from ..utilities import message
from ..functions import convert
from .. import functions as pfn
from ..meshutils import get_meshUtils
from .. import mpi
from . import _fig

def quickShow(*args, **kwargs):

    quickFig = QuickFig(*args, **kwargs)
    quickFig.show()

class QuickFig(_fig.Fig):

    def __init__(
            self,
            *args,
            onMesh = True,
            facecolour = 'white',
            edgecolour = 'white',
            colourBar = False,
            quality = 3.,
            **kwargs
            ):

        args = list(args)

        self.fig = glucifer.Figure(
            facecolour = facecolour,
            quality = 3.,
            **kwargs
            )

        self.features = set()
        self.fittedvars = []
        self.updateFuncs = []

        self.vars = []
        self.planetVars = []

        self.inventory = [
            self.add_surface,
            self.add_contours,
            self.add_stipple,
            self.add_points,
            self.add_arrows,
            self.add_arrows_red,
            self.add_arrows_blue,
            ]

        self.functions_used = []

        self.add_vars(
            *args,
            # onMesh = onMesh,
            colourBar = colourBar,
            **kwargs
            )

        super().__init__(**kwargs)

    def add_vars(self, *args, **kwargs):

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
                            function(planetVar, **kwargs)
                            found = True
                            self.functions_used.append(function)
                        except Exception as e:
                            # message(function, e)
                            continue
            if found:
                self.fittedvars.append(planetVar)
        self.notfittedvars = [var for var in self.vars if not var in self.fittedvars]

        # message(
        #     "Fitted " + str(len(self.fittedvars)) + " variables to the figure."
        #     )

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

    def add_contours(self, arg, colours = "red black", **kwargs):
        planetVar = convert(arg)
        normed = pfn.normalise.default(
            planetVar, [2., 1024.]
            )
        self.updateFuncs.append(normed.update)
        if not planetVar.varDim == 1:
            raise Exception
        self.fig.append(
            glucifer.objects.Contours(
                planetVar.mesh,
                _fn.math.log2(normed),
                colours = colours,
                interval = 1.,
                **kwargs
                )
            )

    def add_arrows(self, arg, colour = 'black', **kwargs):
        planetVar = convert(arg)
        if not planetVar.vector:
            raise Exception
        kwargs = {**kwargs}
        topop = {'colourBar', 'colour'}
        for val in topop:
            try:
                kwargs.pop(val)
            except:
                pass
        self.fig.append(
            glucifer.objects.VectorArrows(
                planetVar.mesh,
                planetVar,
                colour = colour,
                **kwargs
                )
            )

    def add_arrows_red(self, arg, **kwargs):
        self.add_arrows(arg, colour = 'red', **kwargs)

    def add_arrows_blue(self, arg, **kwargs):
        self.add_arrows(arg, colour = 'blue', **kwargs)

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
                # opacity = 0.5,
                # fn_size = 1e3 / float(planetVar.substrate.particleGlobalCount)**0.5,
                # colours = "purple green brown pink red",
                **kwargs
                )
            )

    def _update(self):
        for updateFunc in self.updateFuncs:
            updateFunc()

    def show(self):
        self._update()
        for var in self.fittedvars:
            message(var.varName)
        self.fig.show()

    def _save(self, path, name, ext):
        self.fig.save(os.path.join(path, name + '.' + ext))
