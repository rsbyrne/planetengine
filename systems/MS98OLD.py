import numpy as np

import underworld as uw
fn = uw.function

from planetengine.systems import System
from planetengine.initials import sinusoidal

default_IC = sinusoidal.get()

class MS98(System):

    species = "ms98"

    def __init__(
        self,
        res = 64,
        f = 1.,
        aspect = 1.,
        Ra = 1e7,
        urey = 0.,
        eta0 = 3e4,
        tau0 = 4e5,
        tau1 = 1e7,
        _initial_temperatureField = default_IC,
        **kwargs
        ):

        ### MESH & MESH VARIABLES ###

        maxf = 0.999
        if f == 'max' or f == 1.:
            f = maxf
        else:
            assert f <= maxf

        length = 1.
        outerRad = 1. / (1. - f)
        radii = (outerRad - length, outerRad)

        maxAspect = np.pi * sum(radii) / length
        if aspect == 'max':
            aspect = maxAspect
            periodic = True
        else:
            assert aspect < maxAspect
            periodic = False

        width = length**2 * aspect * 2. / (radii[1]**2 - radii[0]**2)
        midpoint = np.pi / 2.
        angExtentRaw = (midpoint - 0.5 * width, midpoint + 0.5 * width)
        angExtentDeg = [item * 180. / np.pi for item in angExtentRaw]
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

        heatingFn = urey * Ra ** (1. / 3.)

        ### RHEOLOGY ###

        creepViscFn = fn.math.pow(
            eta0,
            1. - temperatureField
            )

        depthFn = mesh.radialLengths[1] - mesh.radiusFn
        yieldStressFn = tau0 + depthFn * tau1
        vc = uw.mesh.MeshVariable(
            mesh = mesh,
            nodeDofCount = 2
            )
        vc_eqNum = uw.systems.sle.EqNumber(
            vc,
            False
            )
        vcVec = uw.systems.sle.SolutionVector(
            vc,
            vc_eqNum
            )
        secInvFn = fn.tensor.second_invariant(
            fn.tensor.symmetric(
                vc.fn_gradient
                )
            )
        plasticViscFn = yieldStressFn / (2. * secInvFn + 1e-18)

        viscosityFn = fn.misc.min(
            creepViscFn,
            plasticViscFn
            ) + 0. * velocityField[0]

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
                nonLinearIterate = True,
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
            varsOfState = {
                'temperatureField': temperatureField,
                'temperatureDotField': temperatureDotField
                },
            obsVars = {
                'temperature': temperatureField,
                'velocity': velocityField,
                'viscosity': viscosityFn,
                'plasticity': viscosityFn / creepViscFn
                },
            update = update,
            integrate = integrate,
            localsDict = locals()
            )

CLASS = MS98
