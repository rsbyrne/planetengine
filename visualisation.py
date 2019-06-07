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

import planetengine

def quickShow(*args, **kwargs):

    quickFig = planetengine.visualisation.QuickFig(*args, **kwargs)
    quickFig.show()

class QuickFig:

    def __init__(self, *args, **kwargs):

        self.fig = glucifer.Figure(**kwargs)
        self.features = set()
        self.pevars = []

        for arg in args:
            if hasattr(arg, 'subMesh'):
                self.add_grid(arg)
            elif hasattr(arg, 'particleCoordinates'):
                self.add_swarm(arg)
            else:
                pevar = planetengine.standards.make_pevar(arg)
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
                variables_fitted += 1

        planetengine.message(
            "Fitted " + str(variables_fitted) + " variables to the figure."
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
        data = inFn.evaluate(pevar.mesh)
        inScales = planetengine.mapping.get_scales(data)[0]
        rescaledFn = (inFn - inScales[0]) / (inScales[1] - inScales[0])
        self.fig.append(
            glucifer.objects.Contours(
                pevar.mesh,
                fn.math.log10(rescaledFn * 1e5 + 1.),
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

    def show(self):
        self.fig.show()

    def save(self, path):
        if rank == 0:
            directory = os.path.dirname(path)
            if not os.path.isdir(directory):
                os.mkdir(directory)
        self.fig.save(path)