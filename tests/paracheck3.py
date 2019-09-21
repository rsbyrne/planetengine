from .. import mpi

if mpi.rank == 0:
    mpi.barrier()
print("Done!")
