from .utilities import unpack_var
from .utilities import hash_var
import underworld as uw

# Registries of projector objects
projections = {} # key = uw obj, val = projection meshvar
projectors = {} # key = projection meshvar, val = projector
projectFuncs = {} # key = projection meshvar, val = projectFunc
lasthashes = {}

def get_meshVar(*args):
    var, varType, mesh, substrate, dType, varDim = unpack_var(args)
    if varType == 'meshVar':
        return var, lambda: None
    else:
        if var in projection.projections:
            meshVar = projection.projections[var]
            updateFunc = projection.projectFuncs[meshVar]
        else:
            meshVar, updateFunc = projection.make_projector(var)
        return meshVar, updateFunc

def make_projector(*args):

    var, varType, mesh, substrate, dType, varDim = unpack_var(args)

    projection = uw.mesh.MeshVariable(
        mesh,
        varDim,
        )
    projector = uw.utils.MeshVariable_Projection(
        projection,
        var,
        )

    inherited_proj = []
    for subVar in var._underlyingDataItems:
        if subVar in projectFuncs:
            inherited_proj.append(projectFuncs[subVar])

    lasthashes[projection] = 0

    def projectFunc():
        currenthash = hash_var(var)
        if not lasthashes[projection] == currenthash:
            for inheritedProj in inherited_proj:
                inheritedProj()
            projector.solve()
            if dType in ('int', 'boolean'):
                projection.data[:] = np.round(
                    projection.data
                    )
            lasthashes[projection] = currenthash

    projections[var] = projection
    projectors[projection] = projector
    projectFuncs[projection] = projectFunc

    return projection, projectFunc