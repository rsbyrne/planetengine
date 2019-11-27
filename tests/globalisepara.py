import planetengine

system = planetengine.systems.isovisc.build(f = 1., res = 4)
temperature = system.obsVars['temperature']

outArray = planetengine.utilities.globalise_array(
    temperature.data,
    [int(node) for node in temperature.mesh.data_nodegId]
    )

assert len(outArray) == temperature.mesh.nodesGlobal
