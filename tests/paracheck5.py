import planetengine

system = planetengine.tests.testsystems.arrhenius()

stress = system.viscosityFn * system.velocityField
print("Pre-iterate", planetengine.mpi.rank, planetengine.utilities.var_check_hash(stress))
print("Pre-iterate", planetengine.mpi.rank, planetengine.utilities.var_check_hash(stress))
if planetengine.mpi.rank == 0:
    print("Iterating.")
system.iterate()
print("Post-iterate", planetengine.mpi.rank, planetengine.utilities.var_check_hash(stress))
print("Post-iterate", planetengine.mpi.rank, planetengine.utilities.var_check_hash(stress))
