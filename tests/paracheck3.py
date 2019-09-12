import underworld as uw

if uw.mpi.rank == 0:
    uw.mpi.barrier()
print("Done!")
