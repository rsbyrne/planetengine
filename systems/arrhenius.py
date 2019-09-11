import underworld as uw
from underworld import function as fn
import math
import numpy as np

from planetengine.systems._system import System

def build(*args, name = None, **kwargs):
    built = Arrhenius(*args, **kwargs)
    if type(name) == str:
        built.name = name
    return built

class Arrhenius(System):

    name = "arrhenius"
    script = __file__

    def __init__(
        self,
        *args,
        res = 64,
        f = 0.54,
        aspect = 1.,
        Ra = 1e7,
        eta0 = 3e4,
        **kwargs
        ):

        ### HOUSEKEEPING: IMPORTANT! ###

        inputs = locals().copy()

        ### MESH & MESH VARIABLES ###

        maxf = 0.99999
        if f == 'max' or f == 1.:
            f = maxf
        else:
            assert f < maxf

        length = 1.
        outerRad = 1. / (1. - f)
        radii = (outerRad - length, outerRad)

        maxAspect = math.pi * sum(radii) / length
        if aspect == 'max':
            aspect = maxAspect
            periodic = True
        else:
            assert aspect < maxAspect
            periodic = False

        width = length**2 * aspect * 2. / (radii[1]**2 - radii[0]**2)
        midpoint = math.pi / 2.
        angExtentRaw = (midpoint - 0.5 * width, midpoint + 0.5 * width)
        angExtentDeg = [item * 180. / math.pi for item in angExtentRaw]
        angularExtent = [
            max(0., angExtentDeg[0]),
            min(360., angExtentDeg[1] + abs(min(0., angExtentDeg[0])))
            ]
        angLen = angExtentRaw[1] - angExtentRaw[0]

        assert res % 4 == 0
        radRes = res
        angRes = 4 * int(angLen * (int(radRes * radii[1] / length)) / 4)
        elementRes = (radRes, angRes)

        mesh = uw.mesh.FeMesh_Annulus(
            elementRes = elementRes,
            radialLengths = radii,
            angularExtent = angularExtent,
            periodic = [False, periodic]
            )

        temperatureField = uw.mesh.MeshVariable(mesh, 1)
        temperatureDotField = uw.mesh.MeshVariable(mesh, 1)
        pressureField = uw.mesh.MeshVariable(mesh.subMesh, 1)
        velocityField = uw.mesh.MeshVariable(mesh, 2)

        temperatureField.scales = [[0., 1.]]
        temperatureField.bounds = [[0., 1., '.', '.']]

        ### BOUNDARIES ###

        inner = mesh.specialSets["inner"]
        outer = mesh.specialSets["outer"]
        sides = mesh.specialSets["MaxJ_VertexSet"] + mesh.specialSets["MinJ_VertexSet"]

        if periodic:
            velBC = uw.conditions.RotatedDirichletCondition(
                variable = velocityField,
                indexSetsPerDof = (inner + outer, None),
                basis_vectors = (mesh.bnd_vec_normal, mesh.bnd_vec_tangent)
                )
        else:
            velBC = uw.conditions.RotatedDirichletCondition(
                variable = velocityField,
                indexSetsPerDof = (inner + outer, sides),
                basis_vectors = (mesh.bnd_vec_normal, mesh.bnd_vec_tangent)
                )

        tempBC = uw.conditions.DirichletCondition(
            variable = temperatureField,
            indexSetsPerDof = (inner + outer,)
            )

        ### FUNCTIONS ###

        vc = uw.mesh.MeshVariable(mesh = mesh, nodeDofCount = 2)
        vc_eqNum = uw.systems.sle.EqNumber(vc, False )
        vcVec = uw.systems.sle.SolutionVector(vc, vc_eqNum)

        buoyancyFn = Ra * temperatureField

        diffusivityFn = 1.

        heatingFn = 1.

        ### RHEOLOGY ###

        viscosityFn = fn.math.pow(
            eta0,
            1. - temperatureField
            )

        ### SYSTEMS ###

        stokes = uw.systems.Stokes(
            velocityField = velocityField,
            pressureField = pressureField,
            conditions = [velBC,],
            fn_viscosity = viscosityFn,
            fn_bodyforce = buoyancyFn * mesh.unitvec_r_Fn,
            _removeBCs = False,
            )

        solver = uw.systems.Solver(stokes)

        advDiff = uw.systems.AdvectionDiffusion(
            phiField = temperatureField,
            phiDotField = temperatureDotField,
            velocityField = vc,
            fn_diffusivity = diffusivityFn,
            fn_sourceTerm = heatingFn,
            conditions = [tempBC,]
            )

        ### SOLVING ###

        def postSolve():
            # realign solution using the rotation matrix on stokes
            uw.libUnderworld.Underworld.AXequalsY(
                stokes._rot._cself,
                stokes._velocitySol._cself,
                vcVec._cself,
                False
                )
            # remove null space - the solid body rotation velocity contribution
            uw.libUnderworld.StgFEM.SolutionVector_RemoveVectorSpace(
                stokes._velocitySol._cself,
                stokes._vnsVec._cself
                )

        def solve():
            velocityField.data[:] = 0.
            solver.solve(
                nonLinearIterate = False,
                callback_post_solve = postSolve,
                )
            uw.libUnderworld.Underworld.AXequalsX(
                stokes._rot._cself,
                stokes._velocitySol._cself,
                False
                )

        def update():
            solve()

        def integrate():
            dt = advDiff.get_max_dt()
            advDiff.integrate(dt)
            return dt

        super().__init__(
            varsOfState = {'temperatureField': temperatureField},
            obsVars = {
                'temperature': temperatureField,
                'velocity': velocityField,
                'stress': velocityField * viscosityFn
                },
            _update = update,
            _integrate = integrate,
            _locals = locals(),
            args = args,
            kwargs = kwargs,
            inputs = inputs,
            script = self.script
            )
