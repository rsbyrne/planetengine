#!/bin/bash
SCRIPT=${1:-localscript.py}
CHUNKS=${2:-1}
CORESPERCHUNK=${3:-1}
CHUNKSTART=${4:-0}
CHUNKSTOP=${5:$CHUNKS}
CHUNKNO=$CHUNKSTART
while [ $CHUNKNO -le $CHUNKSTOP ]; do
    mpirun -np $CORESPERCHUNK python $SCRIPT $CHUNKS $i &
    CHUNKNO=$(($CHUNKNO+1))
done
