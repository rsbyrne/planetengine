import math

import underworld as uw
fn, cd = uw.function, uw.conditions

from planetengine.systems import System
from planetengine.initials.sinusoidal import Sinusoidal
from planetengine.initials.constant import Constant

class Viscoplastic(System):

    optionsKeys = {
        'res', 'courant', 'innerMethod', 'innerTol', 'outerTol', 'penalty',
        'mgLevels'
        }
    paramsKeys = {
        'alpha', 'aspect', 'eta0', 'f', 'flux', 'H', 'kappa', 'tau0', 'tau1'
        }
    configsKeys = {
        'temperatureField', 'temperatureDotField'
        }

    def __init__(self,
            # OPTIONS
            res = 64,
            courant = 1.,
            innerMethod = 'mg',
            innerTol = 1e-6,
            outerTol = 1e-5,
            penalty = None,
            mgLevels = None,
            # PARAMS
            alpha = 1e7,
            aspect = 1.,
            eta0 = 3e4,
            f = 0.54,
            flux = None,
            H = 0.,
            kappa = 1.,
            tau0 = 4e5,
            tau1 = 1e7,
            # CONFIGS
            temperatureField = Sinusoidal(),
            temperatureDotField = None,
            # META
            **kwargs
            ):

        ### MESH ###

        if f == 1. and aspect == 'max':
            raise ValueError
        maxf = 0.999
        if f == 'max' or f == 1.:
            f = maxf
        else:
            assert f <= maxf

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

        ### VARIABLES ###

        temperatureField = mesh.add_variable(1)
        temperatureDotField = mesh.add_variable(1)
        conductionField = mesh.add_variable(1)
        pressureField = mesh.subMesh.add_variable(1)
        velocityField = mesh.add_variable(2)
        vc = mesh.add_variable(2)

        ### BOUNDARIES ###

        specSets = mesh.specialSets
        inner, outer = specSets['inner'], specSets['outer']
        left, right = specSets['MaxJ_VertexSet'], specSets['MinJ_VertexSet']

        if mesh.periodic[1]: bounded = (inner + outer, None)
        else: bounded = (inner + outer, left + right)
        bndVecs = (mesh.bnd_vec_normal, mesh.bnd_vec_tangent)
        velBC = cd.RotatedDirichletCondition(velocityField, bounded, bndVecs)
        velBCs = [velBC,]

        if flux is None:
            scales, bounds = [[0., 1.]], [[0., 1., '.', '.']]
            temperatureField.scales, temperatureField.bounds = scales, bounds
            conductionField.data[outer], conductionField.data[inner] = 0., 1.
            tempBC = cd.DirichletCondition(temperatureField, (inner + outer,))
            condBC = cd.DirichletCondition(conductionField, (inner + outer,))
            tempBCs, condBCs = [tempBC,], [condBC,]
        else:
            scales, bounds = [[0., None]], [[0., '.', '.', '.']]
            temperatureField.scales, temperatureField.bounds = scales, bounds
            conductionField.data[outer] = 1.
            tempBC = cd.DirichletCondition(temperatureField, (outer,))
            condBC = cd.DirichletCondition(conductionField, (outer,))
            tempFluxBC = cd.NeumannCondition(temperatureField, (inner,), flux)
            condFluxBC = cd.NeumannCondition(conductionField, (inner,), flux)
            tempBCs, condBCs = [tempBC, tempFluxBC], [condBC, condFluxBC]

        ### FUNCTIONS ###

        buoyancyFn = alpha * temperatureField
        diffusivityFn = kappa
        heatingFn = H

        ### RHEOLOGY ###

        if eta0 == 1.:
            creepViscFn = 1.
        else:
            creepViscFn = fn.math.pow(eta0, 1. - temperatureField)

        if tau1 == 0.:
            nonLinear = False
            plasticViscFn = tau0
        else:
            nonLinear = True
            depthFn = mesh.radialLengths[1] - mesh.radiusFn
            tau = tau0 + depthFn * tau1
            symmetric = fn.tensor.symmetric(vc.fn_gradient)
            secInvFn = fn.tensor.second_invariant(symmetric)
            plasticViscFn = tau / (2. * secInvFn + 1e-18)

        viscosityFn = fn.misc.min(creepViscFn, plasticViscFn)
        viscosityFn = fn.misc.min(eta0, fn.misc.max(viscosityFn, 1.))
        if nonLinear:
            viscosityFn = viscosityFn + 0. * velocityField[0]

        ### SYSTEMS ###

        conductive = uw.systems.SteadyStateHeat(
            temperatureField = conductionField,
            fn_diffusivity = diffusivityFn,
            fn_heating = heatingFn,
            conditions = condBCs
            )
        conductiveSolver = uw.systems.Solver(conductive)

        stokes = uw.systems.Stokes(
            velocityField = velocityField,
            pressureField = pressureField,
            conditions = velBCs,
            fn_viscosity = viscosityFn,
            fn_bodyforce = buoyancyFn * mesh.unitvec_r_Fn,
            _removeBCs = False,
            )
        solver = uw.systems.Solver(stokes)
        solver.set_inner_method(innerMethod)
        solver.set_inner_rtol(innerTol)
        solver.set_outer_rtol(outerTol)
        if not penalty is None: solver.set_penalty(penalty)
        if not mgLevels is None: solver.set_mg_levels(mgLevels)

        advDiff = uw.systems.AdvectionDiffusion(
            phiField = temperatureField,
            phiDotField = temperatureDotField,
            velocityField = vc,
            fn_diffusivity = diffusivityFn,
            fn_sourceTerm = heatingFn,
            conditions = tempBCs
            )

        ### SOLVING ###

        conductiveSolver.solve()

        vc_eqNum = uw.systems.sle.EqNumber(vc, False)
        vcVec = uw.systems.sle.SolutionVector(vc, vc_eqNum)

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

        def update():
            velocityField.data[:] = 0.
            solver.solve(
                nonLinearIterate = nonLinear,
                callback_post_solve = postSolve,
                )
            uw.libUnderworld.Underworld.AXequalsX(
                stokes._rot._cself,
                stokes._velocitySol._cself,
                False
                )

        def integrate():
            dt = courant * advDiff.get_max_dt()
            advDiff.integrate(dt)
            return dt

        super().__init__(locals(), **kwargs)

### ATTRIBUTES ###
CLASS = Viscoplastic