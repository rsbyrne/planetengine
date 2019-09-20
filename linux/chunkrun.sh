#!/bin/bash
umask 0000
SCRIPT=${1:-localscript.py}
CHUNKS=${2:-1}
CHUNKNO=${3:-0}
CORES=${4:-1}
ITERNO=0
MAXITER=999
while [ $ITERNO -lt $MAXITER ]
do
    # echo "Started job " $CHUNKNO $ITERNO
    mpirun -np $CORES python $SCRIPT $CHUNKS $CHUNKNO $ITERNO > logs/job$CHUNKNO.out 2> logs/job$CHUNKNO.error
    # echo "Finished job " $CHUNKNO $ITERNO
    ITERNO=$(($ITERNO+1))
done
