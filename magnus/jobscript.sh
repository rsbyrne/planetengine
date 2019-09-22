#!/bin/bash

#SBATCH --time=1:00:00
#SBATCH --account=m18
#SBATCH --nodes=6
#SBATCH --partition=debugq

IMAGE=underworldcode/uw2cylindrical:cylindrical
SCRIPT=./localscript.py
CHUNKS=1
CHUNKNO=0
JOBNO=0
RES=32
ASPECT=1

CORES=$(expr $ASPECT \* $RES / 32 \* $RES / 32)

module load shifter

srun -n $CORES shifter run --mpi $IMAGE python $SCRIPT $CHUNKS $CHUNKNO $JOBNO $RES $ASPECT