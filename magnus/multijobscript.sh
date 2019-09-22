#!/bin/bash

#SBATCH --time=1:00:00
#SBATCH --account=m18
#SBATCH --nodes=6
#SBATCH --partition=debugq

IMAGE=underworldcode/uw2cylindrical:cylindrical
SCRIPT=./localscript.py
CHUNKS=1
CHUNKNO=0
CHUNKSIZE=4
RESARR=( 32 )
ASPECTARR=( 1 )

module load shifter

for RES in ${RESARR[@]}
do
for ASPECT in ${ASPECTARR[@]}
do
CORES=$(expr $ASPECT \* $RES / 32 \* $RES / 32)
i=0
end=$(expr $CHUNKSIZE - 1)
while [ $i -le $end ]
do
srun --export=all -n $CORES shifter run --mpi $IMAGE python $SCRIPT $CHUNKS $CHUNKNO $i $RES $ASPECT &
i=$(($i+1))
done
done
done

wait