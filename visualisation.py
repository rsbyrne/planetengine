import underworld as uw
from underworld import function as fn
import glucifer
import numpy as np
import math
import os

from mpi4py import MPI
comm = MPI.COMM_WORLD
rank = comm.Get_rank()
nProcs = comm.Get_size()

from . import standards
from .utilities import message

def quickShow(*args, **kwargs):

    quickFig = QuickFig(*args, **kwargs)
    quickFig.show()

class QuickFig:

    def __init__(self, *args, figname = 'default', **kwargs):

        self.fig = glucifer.Figure(**kwargs)
        self.figname = figname
        self.features = set()
        self.pevars = []
        self.fittedvars = []

        for arg in args:
            if type(arg) is tuple:
                argname, arg = arg
            if hasattr(arg, 'subMesh'):
                self.add_grid(arg)
            elif hasattr(arg, 'particleCoordinates'):
                self.add_swarm(arg)
            else:
                pevar = standards.make_pevar(arg)
                self.pevars.append(pevar)

        self.inventory = [
            self.add_surface,
            self.add_contours,
            self.add_arrows,
            self.add_points,
            self.add_stipple
            ]

        variables_fitted = 0
        functions_used = []
        for pevar in self.pevars:
            found = False
            for function in self.inventory:
                if not function in functions_used:
                    if not found:
                        try:
                            function(pevar, **kwargs)
                            found = True
                            functions_used.append(function)
                        except:
                            continue
            if found:
                self.fittedvars.append(pevar)
        self.notfittedvars = [var for var in self.pevars if not var in self.fittedvars]

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

    def add_stipple(self, pevar, **kwargs):
        assert pevar.discrete or pevar.boolean
        assert not pevar.vector
        drawing = glucifer.objects.Drawing(
            pointsize = 3.,
            )
        allCoords = pevar.pemesh.cartesianScope
        for coord in allCoords:
            try:
                val = pevar.meshVar.evaluate(np.array([coord]))
                if bool(val):
                    drawing.point(coord)
            except:
                pass
        self.fig.append(drawing)

    def add_surface(self, pevar, **kwargs):
        assert not pevar.discrete
        assert not pevar.vector
        self.fig.append(
            glucifer.objects.Surface(
                pevar.mesh,
                pevar.meshVar,
                **kwargs
                )
            )

    def add_contours(self, pevar, **kwargs):
        assert not pevar.discrete
        assert not pevar.vector
        inFn = pevar.meshVar
#         data = inFn.evaluate(pevar.mesh)
#         inScales = planetengine.mapping.get_scales(data)[0]
#         rescaledFn = (inFn - inScales[0]) / (inScales[1] - inScales[0])
        self.fig.append(
            glucifer.objects.Contours(
                pevar.mesh,
                fn.math.log10(inFn),
#                 fn.math.log10(rescaledFn * 1e5 + 1.),
                colours = "red black",
                interval = 0.5,
                **kwargs
                )
            )

    def add_arrows(self, pevar, **kwargs):
        assert not pevar.discrete
        assert pevar.vector
        self.fig.append(
            glucifer.objects.VectorArrows(
                pevar.mesh,
                pevar.meshVar,
                **kwargs
                )
            )

    def add_points(self, pevar, **kwargs):
        assert pevar.particles
        assert not pevar.vector
        self.fig.append(
            glucifer.objects.Points(
                pevar.substrate,
                fn_colour = pevar.var,
                fn_mask = pevar.var,
                opacity = 0.5,
                fn_size = 1e3 / float(pevar.substrate.particleGlobalCount)**0.5,
                colours = "purple green brown pink red",
                **kwargs
                )
            )

    def update(self):
        for pevar in self.pevars:
            pevar.update()

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