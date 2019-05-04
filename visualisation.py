import underworld as uw
from underworld import function as fn
import glucifer
import numpy as np
import math

import planetengine

def quickShow(*args, **kwargs):

    quickFig = QuickFig(*args, **kwargs)
    quickFig.show()

class QuickFig:

    def __init__(self, *args, **kwargs):

        self.fig = glucifer.Figure(**kwargs)
        self.features = set()
        self.variables = []

        for arg in args:
            if hasattr(arg, 'subMesh'):
                self.add_grid(arg)
            elif hasattr(arg, 'particleCoordinates'):
                self.add_swarm(arg)
            else:
                variable = planetengine.standards.standardise(arg)
                variable.update()
                self.variables.append(variable)

        self.inventory = [
            self.add_surface,
            self.add_contours,
            self.add_arrows,
            self.add_points,
            self.add_stipple
            ]

        variables_fitted = 0
        functions_used = []
        for variable in self.variables:
            found = False
            for function in self.inventory:
                if not function in functions_used:
                    if not found:
                        try:
                            function(variable)
                            found = True
                            functions_used.append(function)
                        except:
                            continue
            if found:
                variables_fitted += 1

        planetengine.message(
            "Fitted " + str(variables_fitted) + " variables to the figure."
            )

    def add_stipple(self, stInp):
        assert 'discrete' in stInp.types
        assert 'binary' in stInp.types
        assert 'scalar' in stInp.types
        drawing = glucifer.objects.Drawing()
        for coord in stInp.meshUtils.cartesianScope:
            try:
                if stInp.meshVar.evaluate(np.array([coord])):
                    drawing.point(coord)
            except:
                pass
        self.fig.append(drawing)

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

    def add_surface(self, stInp):
        assert 'continuous' in stInp.types
        assert 'scalar' in stInp.types
        self.fig.append(
            glucifer.objects.Surface(
                stInp.mesh,
                stInp.meshVar,
                colourBar = False
                )
            )

    def add_contours(self, stInp):
        assert 'continuous' in stInp.types
        assert 'scalar' in stInp.types
        self.fig.append(
            glucifer.objects.Contours(
                stInp.mesh,
                fn.math.log10(stInp.meshVar),
                colours = "red black",
                interval = 0.5,
                colourBar = False
                )
            )

    def add_arrows(self, stInp):
        assert 'continuous' in stInp.types
        assert 'vector' in stInp.types
        self.fig.append(
            glucifer.objects.VectorArrows(
                stInp.mesh,
                stInp.meshVar,
                )
            )

    def add_points(self, stInp):
        assert 'swarm' in stInp.types
        assert 'scalar' in stInp.types
        self.fig.append(
            glucifer.objects.Points(
                stInp.swarm,
                fn_colour = stInp.var,
                fn_mask = stInp.var,
                opacity = 1.,
                fn_size = 1e3 / float(stInp.swarm.particleGlobalCount)**0.5,
                colours = "purple green brown pink red",
                colourBar = False
                )
            )

    def show(self):
        self.fig.show()