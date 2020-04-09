import numpy as np

import underworld as uw
fn, cd = uw.function, uw.conditions

from planetengine.systems import System
from planetengine.initials import Sinusoidal
from planetengine.initials import Constant
from planetengine.initials import Extents
from planetengine.shapes import trapezoid
from planetengine.meshes import Annulus

defaultExtents = Extents([(1., trapezoid(longwidth = 0.5)),], 0.)

class ViscoplasticMaterial(System):

    optionsKeys = {
        'res', 'courant', 'innerMethod', 'innerTol', 'outerTol', 'penalty',
        'mgLevels', 'meshClass'
        }
    paramsKeys = {
        'alpha', 'aspect', 'buoyRef', 'etaDelta', 'etaRef', 'f', 'flux', 'H',
        'kappa', 'length', 'tempDelta', 'tempRef', 'tauDelta', 'tauRef'
        }
    configsKeys = {
        'temperatureField', 'temperatureDotField', 'materialField'
        }

    def __init__(self,
            # OPTIONS
            res = 64,
            courant = 0.5,
            innerMethod = 'superludist',
            innerTol = None,
            outerTol = None,
            penalty = None,
            mgLevels = None,
            meshClass = Annulus,
            nonLinearTolerance = 1e-2,
            nonLinearMaxIterations = 100,
            # PARAMS
            alpha = 1e7,
            aspect = 1.,
            buoyRef = 0.,
            etaDelta = 3e4,
            etaRef = 1.,
            f = 1.,
            flux = None,
            H = 0.,
            kappa = 1.,
            length = 1.,
            tempDelta = 1.,
            tempRef = 0.,
            tauDelta = 1e7,
            tauRef = 4e5,
            # CONFIGS
            temperatureField = Sinusoidal(),
            temperatureDotField = None,
            materialField = Extents([(1., trapezoid(longwidth = 0.5)),], 0.),
            # META
            **kwargs
            ):

        tempMin, tempMax = tempRef, tempRef + tempDelta

        ### MESH ###

        mesh = meshClass.make(
            res = res,
            aspect = aspect,
            f = f,
            length = length
            )
        meshFine = meshClass.make(
            res = res * 8,
            aspect = aspect,
            f = f,
            length = length
            )

        ### VARIABLES ###

        temperatureField = mesh.add_variable(1)
        temperatureDotField = mesh.add_variable(1)
        pressureField = mesh.subMesh.add_variable(1)
        velocityField = mesh.add_variable(2)
        vc = mesh.add_variable(2)

        dimlessTempFn = (temperatureField - tempMin) / tempDelta

        materialField = meshFine.add_variable(1)

        ### SWARM ###

        swarm = uw.swarm.Swarm(mesh, particleEscape = True)
        materialSwarm = swarm.add_variable(
            dataType = "int",
            count = 1
            )
        swarmLayout = uw.swarm.layouts.PerCellSpaceFillerLayout(
            swarm = swarm,
            particlesPerCell = 20
            )

        ### BOUNDARIES ###

        specSets = mesh.specialSets
        inner, outer = specSets['inner'], specSets['outer']
        left, right = specSets['MaxJ_VertexSet'], specSets['MinJ_VertexSet']

        if mesh.periodic[1]: bounded = (inner + outer, None)
        else: bounded = (inner + outer, left + right)
        bndVecs = (mesh.bnd_vec_normal, mesh.bnd_vec_tangent)
        velBC = cd.RotatedDirichletCondition(velocityField, bounded, bndVecs)
        velBCs = [velBC,]

        if flux is None and H == 0.:
            temperatureField.scales = [[tempMin, tempMax]]
            temperatureField.bounds = [[tempMin, tempMax, '.', '.']]
        else:
            temperatureField.scales = [[tempMin, None]]
            temperatureField.bounds = [[tempMin, '.', '.', '.']]

        if flux is None:
            tempBC = cd.DirichletCondition(temperatureField, (inner + outer,))
            tempBCs = [tempBC,]
        else:
            tempBC = cd.DirichletCondition(temperatureField, (outer,))
            tempFluxBC = cd.NeumannCondition(temperatureField, (inner,), flux)
            tempBCs = [tempBC, tempFluxBC]

        ### FUNCTIONS ###

        buoyancyFn = alpha * dimlessTempFn + buoyRef
        heatingFn = fn.misc.constant(H)
        diffusivityFn = fn.misc.constant(kappa)

        ### RHEOLOGY ###

        surfEta = etaRef + etaDelta
        creepViscFn = etaRef + fn.math.pow(etaDelta, 1. - temperatureField)

        depthFn = mesh.radialLengths[1] - mesh.radiusFn
        tau = tauRef + depthFn * tauDelta
        symmetric = fn.tensor.symmetric(vc.fn_gradient)
        secInvFn = fn.tensor.second_invariant(symmetric)
        plasticViscFn = tau / (2. * secInvFn + 1e-18)

        viscosityFn = fn.misc.min(creepViscFn, plasticViscFn)
        viscosityFn = fn.misc.min(surfEta, fn.misc.max(viscosityFn, etaRef))
        viscosityFn = viscosityFn + 0. * velocityField[0]

        ### SYSTEMS ###

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
        if not innerTol is None: solver.set_inner_rtol(innerTol)
        if not outerTol is None: solver.set_outer_rtol(outerTol)
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

        advector = uw.systems.SwarmAdvector(
            swarm = swarm,
            velocityField = vc,
            order = 2
            )

        ### SOLVING ###

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

        def update_swarm():
            if swarm.particleGlobalCount:
                swarmData = materialSwarm.evaluate(meshFine)
                materialField.data[...] = np.round(1. * swarmData)
                with swarm.deform_swarm():
                    swarm.data[...] = [0., 0.]
            swarm.populate_using_layout(swarmLayout)
            materialSwarm.data[...] = np.round(materialField.evaluate(swarm))

        def update():
            update_swarm()
            velocityField.data[:] = 0.
            solver.solve(
                nonLinearIterate = True,
                nonLinearTolerance = nonLinearTolerance,
                nonLinearMaxIterations = nonLinearMaxIterations,
                callback_post_solve = postSolve,
                )
            uw.libUnderworld.Underworld.AXequalsX(
                stokes._rot._cself,
                stokes._velocitySol._cself,
                False
                )

        def integrate():
            dt = courant * min(advDiff.get_max_dt(), advector.get_max_dt())
            advector.integrate(dt)
            advDiff.integrate(dt)
            return dt

        super().__init__(locals(), **kwargs)

### ATTRIBUTES ###
CLASS = ViscoplasticMaterial
