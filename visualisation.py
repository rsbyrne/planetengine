import underworld as uw
from underworld import function as fn
import glucifer
import numpy as np
import math

import planetengine

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
                            function(pevar)
                            found = True
                            functions_used.append(function)
                        except:
                            continue
            if found:
                variables_fitted += 1

        planetengine.message(
            "Fitted " + str(variables_fitted) + " variables to the figure."
            )

    def add_grid(self, arg):
        self.fig.append(
            glucifer.objects.Mesh(
                arg
                )
            )

    def add_swarm(self, arg):
        self.fig.append(
            glucifer.objects.Points(
                arg,
                fn_size = 1e3 / float(arg.particleGlobalCount)**0.5,
                colourBar = False
                )
            )

    def add_stipple(self, pevar):
        assert pevar.discrete or pevar.boolean
        assert not pevar.vector
        drawing = glucifer.objects.Drawing()
        allCoords = pevar.pemesh.cartesianScope
#         allCoords = variable.mesh.data
        for coord in allCoords:
            try:
                val = pevar.meshVar.evaluate(np.array([coord]))
                if bool(val):
                    drawing.point(coord)
            except:
                pass
        self.fig.append(drawing)

    def add_surface(self, pevar):
        assert not pevar.discrete
        assert not pevar.vector
        self.fig.append(
            glucifer.objects.Surface(
                pevar.mesh,
                pevar.meshVar,
                colourBar = False
                )
            )

    def add_contours(self, pevar):
        assert not pevar.discrete
        assert not pevar.vector
        self.fig.append(
            glucifer.objects.Contours(
                pevar.mesh,
                fn.math.log10(pevar.meshVar),
                colours = "red black",
                interval = 0.5,
                colourBar = False
                )
            )

    def add_arrows(self, pevar):
        assert not pevar.discrete
        assert pevar.vector
        self.fig.append(
            glucifer.objects.VectorArrows(
                pevar.mesh,
                pevar.meshVar,
                )
            )

    def add_points(self, pevar):
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
                colourBar = False
                )
            )

    def show(self):
        self.fig.show()