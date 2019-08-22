import underworld as uw
import glucifer
import numpy as np
import os

from .utilities import message
from .planetvar import get_planetVar
from .meshutils import get_meshUtils

def quickShow(*args, **kwargs):

    quickFig = QuickFig(*args, **kwargs)
    quickFig.show()

class QuickFig:

    def __init__(self, *args, figname = 'default', **kwargs):

        self.fig = glucifer.Figure(**kwargs)
        self.figname = figname
        self.features = set()
        self.fittedvars = []
        self.updateFuncs = []

        self.vars = []
        args = list(args)
        for arg in args:
            if hasattr(arg, 'subMesh'):
                args.remove(arg)
                self.add_grid(arg)
            elif hasattr(arg, 'particleCoordinates'):
                args.remove(arg)
                self.add_swarm(arg)
        if len(args) > 0:
            self.planetVars = list(
                get_planetVar(
                    *args,
                    return_tuple = True
                    )
                )
        else:
            self.planetVars = []

        for planetVar in self.planetVars:
            planetVar.update()

        self.inventory = [
            self.add_surface,
            self.add_contours,
            self.add_arrows,
            self.add_points,
            self.add_stipple
            ]

        variables_fitted = 0
        functions_used = []
        for planetVar in self.planetVars:
            found = False
            for function in self.inventory:
                if not function in functions_used:
                    if not found:
                        try:
                            function(planetVar, **kwargs)
                            found = True
                            functions_used.append(function)
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

    def add_stipple(self, planetVar, **kwargs):
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

    def add_surface(self, planetVar, **kwargs):
        if not planetVar.varDim == 1:
            raise Exception
        self.fig.append(
            glucifer.objects.Surface(
                planetVar.mesh,
                planetVar,
                **kwargs
                )
            )

    def add_contours(self, planetVar, **kwargs):
        if 0. in planetVar.valSets:
            raise Exception
        if not planetVar.varDim == 1:
            raise Exception
        self.fig.append(
            glucifer.objects.Contours(
                planetVar.mesh,
                planetVar,
                colours = "red black",
                interval = planetVar.ranges[0] / 10.,
                **kwargs
                )
            )

    def add_arrows(self, planetVar, **kwargs):
        if not planetVar.varDim == planetVar.mesh.dim:
            raise Exception
        self.fig.append(
            glucifer.objects.VectorArrows(
                planetVar.mesh,
                planetVar,
                **kwargs
                )
            )

    def add_points(self, planetVar, **kwargs):
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

    def show(self, **kwargs):
        self.update()
        for var in self.fittedvars:
            print(var.varName, var.ranges)
        self.fig.show(**kwargs)

    def save(self, path = '', name = None, **kwargs):
        self.update()
        if name is None:
            name = self.figname
        if uw.mpi.rank == 0:
            if not os.path.isdir(path):
                os.mkdir(path)
        self.fig.save(os.path.join(path, name), **kwargs)
