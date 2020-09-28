import underworld as uw
fn, cd = uw.function, uw.conditions

from planetengine.systems import System
from planetengine.initials import Sinusoidal
from planetengine.initials import Constant
from planetengine.meshes import Annulus

class Isovisc(System):

    def __init__(self,
            # OPTIONS
            res = 64,
            courant = 1.,
            innerMethod = 'lu',
            innerTol = None,
            outerTol = None,
            penalty = None,
            mgLevels = None,
            meshClass = Annulus,
            # PARAMS
            alpha = 1e7,
            aspect = 1.,
            buoyRef = 0.,
            eta = 1.,
            f = 1.,
            flux = None,
            H = 0.,
            kappa = 1.,
            length = 1.,
            tempDelta = 1.,
            tempRef = 0.,
            # CONFIGS
            temperatureField = Sinusoidal(),
            temperatureDotField = None,
            # META
            **kwargs
            ):
        super().__init__(**kwargs)

    def build_system(self, o, p, c):

        tempMin, tempMax = p.tempRef, p.tempRef + p.tempDelta

        ### MESH ###

        mesh = o.meshClass.make(
            res = o.res,
            aspect = p.aspect,
            f = p.f,
            length = p.length
            )

        ### VARIABLES ###

        temperatureField = mesh.add_variable(1)
        temperatureDotField = mesh.add_variable(1)
        pressureField = mesh.subMesh.add_variable(1)
        velocityField = mesh.add_variable(2)
        vc = mesh.add_variable(2)

        dimlessTempFn = (temperatureField - tempMin) / p.tempDelta

        ### BOUNDARIES ###

        specSets = mesh.specialSets
        inner, outer = specSets['inner'], specSets['outer']
        left, right = specSets['MaxJ_VertexSet'], specSets['MinJ_VertexSet']

        if mesh.periodic[1]: bounded = (inner + outer, None)
        else: bounded = (inner + outer, left + right)
        bndVecs = (mesh.bnd_vec_normal, mesh.bnd_vec_tangent)
        velBC = cd.RotatedDirichletCondition(velocityField, bounded, bndVecs)
        velBCs = [velBC,]

        if p.flux is None and p.H == 0.:
            temperatureField.scales = [[tempMin, tempMax]]
            temperatureField.bounds = [[tempMin, tempMax, '.', '.']]
        else:
            temperatureField.scales = [[tempMin, None]]
            temperatureField.bounds = [[tempMin, '.', '.', '.']]

        if p.flux is None:
            tempBC = cd.DirichletCondition(temperatureField, (inner + outer,))
            tempBCs = [tempBC,]
        else:
            tempBC = cd.DirichletCondition(temperatureField, (outer,))
            tempFluxBC = cd.NeumannCondition(temperatureField, (inner,), p.flux)
            tempBCs = [tempBC, tempFluxBC]

        ### FUNCTIONS ###

        buoyancyFn = p.alpha * dimlessTempFn + p.buoyRef
        heatingFn = fn.misc.constant(p.H)
        diffusivityFn = fn.misc.constant(p.kappa)

        ### RHEOLOGY ###

        viscosityFn = fn.misc.constant(p.eta)

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
        solver.set_inner_method(o.innerMethod)
        if not o.innerTol is None: solver.set_inner_rtol(o.innerTol)
        if not o.outerTol is None: solver.set_outer_rtol(o.outerTol)
        if not o.penalty is None: solver.set_penalty(o.penalty)
        if not o.mgLevels is None: solver.set_mg_levels(o.mgLevels)

        advDiff = uw.systems.AdvectionDiffusion(
            phiField = temperatureField,
            phiDotField = temperatureDotField,
            velocityField = vc,
            fn_diffusivity = diffusivityFn,
            fn_sourceTerm = heatingFn,
            conditions = tempBCs
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

        def update():
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

        def integrate():
            dt = o.courant * advDiff.get_max_dt()
            advDiff.integrate(dt)
            return dt

        return locals()

### ATTRIBUTES ###
CLASS = Isovisc
