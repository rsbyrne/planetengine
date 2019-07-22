import underworld as uw
from underworld import function as fn
import glucifer
import numpy as np
import math
import os

from .utilities import message
from .functions import unpack_var
from .meshutils import get_meshUtils

def quickShow(*args, **kwargs):

    quickFig = QuickFig(*args, **kwargs)
    quickFig.show()

class QuickFig:

    def __init__(self, *args, figname = 'default', **kwargs):

        self.fig = glucifer.Figure(**kwargs)
        self.figname = figname
        self.features = set()
        self.vars = []
        self.varDicts = {}
        self.fittedvars = []
        self.updateFuncs = []

        self.vars = []
        for arg in args:
            if hasattr(arg, 'subMesh'):
                self.add_grid(arg)
            elif hasattr(arg, 'particleCoordinates'):
                self.add_swarm(arg)
            else:
                var, varDict = unpack_var(arg, detailed = True, return_var = True)
                self.varDicts[var] = varDict
                self.vars.append(var)

        self.inventory = [
            self.add_surface,
            self.add_contours,
            self.add_arrows,
            self.add_points,
            self.add_stipple
            ]

        variables_fitted = 0
        functions_used = []
        for var in self.vars:
            varDict = self.varDicts[var]
            found = False
            for function in self.inventory:
                if not function in functions_used:
                    if not found:
                        try:
                            function(var, varDict, **kwargs)
                            found = True
                            functions_used.append(function)
                        except:
                            continue
            if found:
                self.fittedvars.append(var)
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

    def add_stipple(self, var, varDict, **kwargs):
        if not varDict['valSets'] == [{0., 1.}]:
            raise Exception
        if not varDict['varDim'] == 1:
            raise Exception
        drawing = glucifer.objects.Drawing(
            pointsize = 3.,
            )
        allCoords = get_meshUtils(varDict['mesh']).cartesianScope
        for coord in allCoords:
            try:
                val = var.evaluate(np.array([coord]))
                if bool(val):
                    drawing.point(coord)
            except:
                pass
        self.fig.append(drawing)

    def add_surface(self, var, varDict, **kwargs):
        if not varDict['varDim'] == 1:
            raise Exception
        self.fig.append(
            glucifer.objects.Surface(
                varDict['mesh'],
                var,
                **kwargs
                )
            )

    def add_contours(self, var, varDict, **kwargs):
        if 0. in varDict['valSets']:
            raise Exception
        if not varDict['varDim'] == 1:
            raise Exception
        self.fig.append(
            glucifer.objects.Contours(
                varDict['mesh'],
                var,
                colours = "red black",
                interval = varDict['ranges'][0] / 10.,
                **kwargs
                )
            )

    def add_arrows(self, var, varDict, **kwargs):
        if not varDict['varDim'] == varDict['mesh'].dim:
            raise Exception
        self.fig.append(
            glucifer.objects.VectorArrows(
                varDict['mesh'],
                var,
                **kwargs
                )
            )

    def add_points(self, var, varDict, **kwargs):
        if not varDict['varType'] in {'swarmVar' or 'swarmFn'}:
            raise Exception
        if not varDict['varDim'] == 1:
            raise Exception
        self.fig.append(
            glucifer.objects.Points(
                varDict['substrate'],
                fn_colour = var,
                fn_mask = var,
                opacity = 0.5,
                fn_size = 1e3 / float(varDict['substrate'].particleGlobalCount)**0.5,
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
        if rank == 0:
            if not os.path.isdir(path):
                os.mkdir(path)
        self.fig.save(os.path.join(path, name))
