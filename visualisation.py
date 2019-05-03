import underworld as uw
from underworld import function as fn
import glucifer
import numpy as np
import math

import planetengine

def quickFig(*args, **kwargs):

    fig = glucifer.Figure(**kwargs)

    features = []
    stInps = []
    for inVar in args:
        stInps.append(planetengine.standards.standardise(inVar))

    for stInp in stInps:
        if stInp.varType == 'mesh':
            if not 'grid' in features:
                fig.Mesh(
                    stInp.var
                    )
                features.append('grid')
            else:
                raise Exception("Can't draw more than one grid.")
        elif stInp.varType in {'meshVar', 'meshFn', 'swarmFn'}:
            if stInp.dim == 1:
                if not 'surface' in features:
                    figSurfaceComponent = fig.Surface(
                        stInp.mesh,
                        stInp.meshVar,
                        colourBar = False
                        )
                    features.append('surface')
                elif not 'contour' in features:
                    figContourComponent = fig.Contours(
                        stInp.mesh,
                        fn.math.log10(stInp.meshVar),
                        colours = "red black",
                        interval = 0.5,
                        colourBar = False
                        )
                    features.append('contour')
                else:
                    raise Exception("No more room for scalar mesh-like objects on the fig.")
            else:
                if not 'arrows' in features:
                    figArrowComponent = fig.VectorArrows(
                        stInp.mesh,
                        stInp.meshVar,
                        )
                    features.append('arrows')
                else:
                    raise Exception("No more room for vector-like objects on the fig.")
        elif stInp.varType == 'swarmVar':
            if not 'points' in features:
                figPointComponent = fig.Points(
                    stInp.swarm,
                    fn_colour = stInp.var,
                    fn_mask = stInp.var,
                    opacity = 0.5,
                    fn_size = 1e3 / float(stInp.swarm.particleGlobalCount)**0.5,
                    colours = "purple green brown pink red",
                    colourBar = False
                    )
                features.append('points')
        else:
            raise Exception("Tried everything and couldn't make it work!")

    return fig

def quickShow(*args, **kwargs):

    fig = quickFig(*args, **kwargs)
    fig.show()

def OLDquickShow(*args,
        figArgs = {
            'edgecolour': 'white',
            'facecolour': 'white',
            'quality': 2,
            }
        ):

    fig = glucifer.Figure(**figArgs)
    features = []
    for invar in args:
        try:
            if not 'mesh' in features:
                var = invar
                fig.Mesh(var)
                features.append('mesh')
            else:
                raise
        except:
            try:
                try:
                    mesh = invar.mesh
                    var = invar
                except:
                    try:
                        var, mesh = invar
                    except:
                        raise Exception("")
                try:
                    if not 'arrows' in features:
                        fig.VectorArrows(mesh, var)
                        features.append('arrows')
                    else:
                        raise
                except:
                    if not 'surface' in features:
                        fig.Surface(mesh, var)
                        features.append('surface')
                    else:
                        if not 'contours' in features:
                            fig.Contours(
                                mesh,
                                fn.math.log10(var),
                                colours = "red black",
                                interval = 0.5,
                                colourBar = False 
                                )
                            features.append('contours')
                        else:
                            raise Exception("Got to end of mesh-based options.")
            except:
                try:
                    var = invar
                    swarm = var.swarm
                except:
                    var, swarm = invar
                try:
                    if not 'points' in features:
                        fig.Points(
                            swarm,
                            fn_colour = var,
                            fn_mask = var,
                            opacity = 0.5,
                            fn_size = 1e3 / float(swarm.particleGlobalCount)**0.5,
                            colours = "purple green brown pink red",
                            colourBar = True,
                            )
                    else:
                        raise Exception("Got to end of swarm-based options.")
                except:
                    raise Exception("Tried everything but couldn't make it work!")

    fig.show()