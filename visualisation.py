import underworld as uw
import glucifer
import numpy as np
import os

from .utilities import message
from .functions import get_planetVar
from .meshutils import get_meshUtils

def quickShow(*args, **kwargs):

    quickFig = QuickFig(*args, **kwargs)
    quickFig.show()

class QuickFig:

    def __init__(self, *args, figname = 'default', **kwargs):

        self.fig = glucifer.Figure(**kwargs)
        self.figname = figname
        self.features = set()
        self.planetVars = []
        self.fittedvars = []
        self.updateFuncs = []

        self.vars = []
        for arg in args:
            if hasattr(arg, 'subMesh'):
                self.add_grid(arg)
            elif hasattr(arg, 'particleCoordinates'):
                self.add_swarm(arg)
            else:
                self.planetVars.append(get_planetVar(arg))

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
                self.fittedvars.append(planetVar.var)
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
        allCoords = get_meshUtils(planetVar.mesh).cartesianScope
        for coord in allCoords:
            try:
                val = planetVar.var.evaluate(np.array([coord]))
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
                planetVar.var,
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
                planetVar.var,
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
                planetVar.var,
                **kwargs
                )
            )

    def add_points(self, planetVar, **kwargs):
        if not planetVar.varType in {'swarmVar' or 'swarmFn'}:
            raise Exception
        if not planetVar.varDim == 1:
            raise Exception
        self.fig.append(
            glucifer.objects.Points(
                planetVar.substrate,
                fn_colour = planetVar.var,
                fn_mask = planetVar.var,
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
        self.fig.show()

    def save(self, path = '', name = None):
        self.update()
        if name is None:
            name = self.figname
        if uw.mpi.rank == 0:
            if not os.path.isdir(path):
                os.mkdir(path)
        self.fig.save(os.path.join(path, name))
