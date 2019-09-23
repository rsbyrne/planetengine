#!/bin/bash
umask 0000
SCRIPT=${1:-localscript.py}
CHUNKS=${2:-1}
CHUNKNO=${3:-0}
ITERNO=${4:-0}
CORES=${5:-1}
OUTFILE="logs/job"$CHUNKNO"_"$ITERNO".out"
ERRORFILE="logs/job"$CHUNKNO"_"$ITERNO".error"
touch $OUTFILE
touch $ERRORFILE
echo "Starting chunk " $CHUNKNO " job " $ITERNO
mpirun -np $CORES python $SCRIPT $CHUNKS $CHUNKNO $ITERNO > $OUTFILE 2> $ERRORFILE
echo "Finished chunk " $CHUNKNO " job " $ITERNO
