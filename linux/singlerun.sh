#!/bin/bash
umask 0000
SCRIPT=${1:-localscript.py}
CHUNKS=${2:-1}
CHUNKNO=${3:-0}
ITERNO=${4:-0}
CORES=${5:-1}
mpirun -np $CORES python $SCRIPT $CHUNKS $CHUNKNO $ITERNO > logs/job$CHUNKNO.out 2> logs/job$CHUNKNO.error
