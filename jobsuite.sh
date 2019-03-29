#!/bin/bash

#SBATCH --array=0-3
#SBATCH --nodes=1
#SBATCH --time=1:00:00
#SBATCH --account=m18

IMAGE=underworldcode/uw2cylindrical:cylindrical
SCRIPT=./localscript.py
CORESPERTASK=16
NODESPERTASK=1
CHUNKS=0

module load shifter
srun -N $NODESPERTASK -n $CORESPERTASK shifter run --mpi $IMAGE python $SCRIPT $CHUNKS $SLURM_ARRAY_TASK_ID

