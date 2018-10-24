
# coding: utf-8

# In[ ]:


import underworld as uw
from underworld import function as fn
import glucifer
import numpy as np
import math
import planetengine
from planetengine import InitialConditions
from planetengine import Analysis


# In[ ]:


radii = (1.2, 2.2) #(1.2, 2.2)
radRes = 128
angPi = 1. / 3.
offsetPi = 1. / 3.

mesh = uw.mesh._FeMesh_Annulus(
    elementRes = (radRes, (4*int(angPi*math.pi*(int(radRes*radii[1]/(radii[1] - radii[0])))/4.))),
    radialLengths = (radii[0], radii[1]),
    angularExtent = (offsetPi * 180., (angPi + offsetPi) * 180.)
    )


# In[ ]:


temperatureField = uw.mesh.MeshVariable(mesh = mesh, nodeDofCount = 1)
temperatureDotField = uw.mesh.MeshVariable(mesh = mesh, nodeDofCount = 1)
pressureField = uw.mesh.MeshVariable(mesh = mesh.subMesh, nodeDofCount = 1)
velocityField = uw.mesh.MeshVariable(mesh = mesh, nodeDofCount = 2)


# In[ ]:


curvedBox = planetengine.CoordSystems.Radial(
    mesh.radialLengths,
    mesh.angularExtent,
    boxDims = ((0., angPi * 6.), (0., 1.))
    ).curved_box


# In[ ]:


initialConditions = InitialConditions.Group([
    #InitialConditions.Sinusoidal(temperatureField.data, curvedBox(mesh.data)),
    InitialConditions.LoadField(temperatureField, "isovisc_Ra1e5res64temperatureField_00010000.h5"),
    InitialConditions.Indices(
        temperatureField.data[:],
        [(mesh.specialSets["outer"].data, 0.),
        (mesh.specialSets["inner"].data, 1.)]
        ),
    InitialConditions.SetVal([velocityField.data, pressureField.data, temperatureDotField.data], 0.),
    ])


# In[ ]:


initialConditions.apply_condition()


# In[ ]:


inner = mesh.specialSets["inner"]
outer = mesh.specialSets["outer"]

velBC = uw.conditions.RotatedDirichletCondition(
    variable = velocityField,
    indexSetsPerDof= (inner + outer, None),
    basis_vectors = (mesh.bnd_vec_normal, mesh.bnd_vec_tangent)
    )

tempBC = uw.conditions.DirichletCondition(
    variable = temperatureField,
    indexSetsPerDof = (inner + outer,)
    )


# In[ ]:


stokes = uw.systems.Stokes(
    velocityField = velocityField,
    pressureField = pressureField,
    conditions = [velBC,],
    fn_viscosity = 1.,
    fn_bodyforce = temperatureField * 1e7 * mesh.fn_unitvec_radial(),
    _removeBCs = False,
    )

solver = uw.systems.Solver(stokes)

advDiff = uw.systems.AdvectionDiffusion(
    phiField = temperatureField,
    phiDotField = temperatureDotField,
    velocityField = velocityField,
    fn_diffusivity = fn.misc.constant(1.),
    conditions = [tempBC,]
    )


# In[ ]:


solver.solve(nonLinearIterate = False)


# In[ ]:


fig = glucifer.Figure(edgecolour = "", quality = 2)
figTempComponent = fig.Surface(mesh, temperatureField, colourBar = True)
figVelComponent = fig.VectorArrows(mesh, velocityField)


# In[ ]:


def postSolve():
    # realign solution using the rotation matrix on stokes
    uw.libUnderworld.Underworld.AXequalsX(
        stokesSLE._rot._cself,
        stokesSLE._velocitySol._cself,
        False
        )
    # remove null space - the solid body rotation velocity contribution
    uw.libUnderworld.StgFEM.SolutionVector_RemoveVectorSpace(
        stokesSLE._velocitySol._cself,
        stokesSLE._vnsVec._cself
        )


# In[ ]:


def update():
    solver.solve(nonLinearIterate = False, callback_post_solve = postSolve)
    dt = 0.5 * advDiff.get_max_dt()
    advDiff.integrate(dt)
    return dt


# In[ ]:


formatDict = {
    'Nu': "{:.1f}",
    'avTemp': "{:.2f}",
    'VRMS': "{:.2f}",
    'surfVRMS': "{:.2f}",
    'modeltime': "{:.1E}",
    'step': "{:.0f}",
    }


# In[ ]:


step, modeltime = fn.misc.constant(0), fn.misc.constant(0.)


# In[ ]:


analyser = Analysis.Analyser('zerodData', {
    'Nu': Analysis.Analyse.DimensionlessGradient(temperatureField, mesh,
        surfIndexSet = mesh.specialSets["outer"], baseIndexSet = mesh.specialSets["inner"]
        ),
    'avTemp': Analysis.Analyse.ScalarFieldAverage(temperatureField, mesh),
    'VRMS': Analysis.Analyse.VectorFieldVolRMS(velocityField, mesh),
    'surfVRMS': Analysis.Analyse.VectorFieldSurfRMS(
        velocityField, mesh, outer
        ),
    'step': Analysis.Analyse.ArrayStripper(step, (0, 0)),
    'modeltime': Analysis.Analyse.ArrayStripper(modeltime, (0, 0)),
    })


# In[ ]:


dataCollector = Analysis.DataCollector([analyser])


# In[ ]:


checkpointer = planetengine.Checkpointer(
    outputPath = "isovisc2_Ra1e7res128_", #"Output\\",
    figs = [("fig", fig)],
    varsOfState = [
        (((temperatureField, "temperatureField"),), (mesh, "mesh")),
        ],
    dataCollector = dataCollector,
    step = step
    )


# In[ ]:


reporter = Analysis.Report(analyser.dataDict, formatDict, fig)


# In[ ]:


analyser.update()
dataCollector.update()
#reporter.report()
checkpointer.checkpoint()


# In[ ]:


while step.value < 100000:
    step.value += 1
    modeltime.value += update()
    if step.value % 10 == 0:
        analyser.update()
        dataCollector.update()
    if step.value % 1000 == 0:
        #reporter.report()
        checkpointer.checkpoint()


# In[ ]:


#testobj = np.loadtxt('testingzerodData.csv', delimiter = ",")
