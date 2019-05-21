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
                variable = planetengine.pevar.make_pevar(arg)
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

    def add_stipple(self, variable):
        assert variable.discrete
        assert variable.binary
        assert not variable.vector
        drawing = glucifer.objects.Drawing()
#         allCoords = variable.meshUtils.cartesianScope
        allCoords = stInp.mesh.data
        for coord in allCoords:
            try:
                if variable.meshVar().evaluate(np.array([coord])):
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

    def add_surface(self, variable):
        assert not variable.discrete
        assert not variable.vector
        self.fig.append(
            glucifer.objects.Surface(
                variable.mesh,
                variable.meshVar(),
                colourBar = False
                )
            )

    def add_contours(self, variable):
        assert not variable.discrete
        assert not variable.vector
        self.fig.append(
            glucifer.objects.Contours(
                variable.mesh,
                fn.math.log10(variable.meshVar()),
                colours = "red black",
                interval = 0.5,
                colourBar = False
                )
            )

    def add_arrows(self, variable):
        assert not variable.discrete
        assert not variable.vector
        self.fig.append(
            glucifer.objects.VectorArrows(
                variable.mesh,
                variable.meshVar(),
                )
            )

    def add_points(self, variable):
        assert variable.varType in ('swarmVar', 'swarmFn')
        assert not variable.vector
        self.fig.append(
            glucifer.objects.Points(
                variable.swarm,
                fn_colour = variable.var,
                fn_mask = variable.var,
                opacity = 1.,
                fn_size = 1e3 / float(variable.swarm.particleGlobalCount)**0.5,
                colours = "purple green brown pink red",
                colourBar = False
                )
            )

    def show(self):
        self.fig.show()