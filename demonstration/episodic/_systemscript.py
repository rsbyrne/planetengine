import underworld as uw
from underworld import function as fn
import math
from planetengine import Grouper

def build(
    res = 32,
    ratio = 1.83,
    isoviscous = False,
    Ra = 1e7,
    maxVisc = 3e4,
    tau0 = 4e5,
    tau1 = 1e7,
    ):

    ### HOUSEKEEPING: IMPORTANT! ###

    inputs = locals().copy()
    script = __file__

    ### MESH & MESH VARIABLES ###

    outerRad = ratio / (ratio - 1) 
    radii = (outerRad - 1., outerRad)
    length = 2. / (radii[1]**2 - radii[0]**2)
    midpoint = math.pi / 2.
    angEx = (midpoint - 0.5 * length, midpoint + 0.5 * length)
    radRes = res
    angLen = angEx[1] - angEx[0]

    mesh = uw.mesh.FeMesh_Annulus(
        elementRes = (radRes, (4*int(angLen*(int(radRes*radii[1]/(radii[1] - radii[0])))/4.))),
        radialLengths = radii,
        angularExtent = [item * 180. / math.pi for item in angEx],
        periodic = [False, False]
        )

    temperatureField = uw.mesh.MeshVariable(mesh, 1)
    temperatureDotField = uw.mesh.MeshVariable(mesh, 1)
    pressureField = uw.mesh.MeshVariable(mesh.subMesh, 1)
    velocityField = uw.mesh.MeshVariable(mesh, 2)

    varsOfState = [((("temperatureField", temperatureField),), ("mesh", mesh))]

    ### BOUNDARIES ###
    
    inner = mesh.specialSets["inner"]
    outer = mesh.specialSets["outer"]
    sides = mesh.specialSets["MaxJ_VertexSet"] + mesh.specialSets["MinJ_VertexSet"]

    velBC = uw.conditions.RotatedDirichletCondition(
        variable = velocityField,
        indexSetsPerDof= (inner + outer, sides),
        basis_vectors = (mesh.bnd_vec_normal, mesh.bnd_vec_tangent)
        )

    tempBC = uw.conditions.DirichletCondition(
        variable = temperatureField,
        indexSetsPerDof = (inner + outer,)
        )

    ### RHEOLOGY ###

    vc = uw.mesh.MeshVariable(mesh = mesh, nodeDofCount = 2)
    vc_eqNum = uw.systems.sle.EqNumber(vc, False )
    vcVec = uw.systems.sle.SolutionVector(vc, vc_eqNum)

    invDensityFn = temperatureField * Ra
    buoyancyFn = invDensityFn * mesh.unitvec_r_Fn

    if isoviscous:
        viscosityFn = creepViscFn = plasticViscFn = 1.
    else:
        magnitude = fn.math.sqrt(fn.coord()[0]**2 + fn.coord()[1]**2)
        depthFn = mesh.radialLengths[1] - magnitude
        yieldStressFn = tau0 + (tau1 * depthFn)
        secInvFn = fn.tensor.second_invariant(fn.tensor.symmetric(vc.fn_gradient))
        plasticViscFn = yieldStressFn / (2. * secInvFn + 1e-18)
        creepViscFn = fn.math.pow(fn.misc.constant(maxVisc), -1. * (temperatureField - 1.))
        viscosityFn = fn.misc.min(maxVisc, fn.misc.max(1., fn.misc.min(creepViscFn, plasticViscFn)))

    ### SYSTEMS ###

    stokes = uw.systems.Stokes(
        velocityField = velocityField,
        pressureField = pressureField,
        conditions = [velBC,],
        fn_viscosity = viscosityFn,
        fn_bodyforce = buoyancyFn,
        _removeBCs = False,
        )

    solver = uw.systems.Solver(stokes)

    advDiff = uw.systems.AdvectionDiffusion(
        phiField = temperatureField,
        phiDotField = temperatureDotField,
        velocityField = vc,
        fn_diffusivity = 1.,
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
            nonLinearIterate = not isoviscous,
            callback_post_solve = postSolve,
            )

    def integrate():
        dt = advDiff.get_max_dt()
        advDiff.integrate(dt)
        return dt

    def iterate():
        solve()
        return integrate()

    ### HOUSEKEEPING: IMPORTANT! ###
    return Grouper(locals())
