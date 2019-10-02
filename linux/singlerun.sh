#!/bin/bash
umask 0000
SCRIPT=${1:-localscript.py}
CHUNKS=${2:-1}
SHUFFLESEED=${3:-0}
CHUNKNO=${4:-0}
ITERNO=${5:-0}
CORES=${6:-1}
OUTFILE="logs/job"$CHUNKNO"_"$ITERNO".out"
ERRORFILE="logs/job"$CHUNKNO"_"$ITERNO".error"
touch $OUTFILE
touch $ERRORFILE
echo "Started job " $ITERNO
mpirun -np $CORES python $SCRIPT $CHUNKS $SHUFFLESEED $CHUNKNO $ITERNO > $OUTFILE 2> $ERRORFILE
echo "Finished job " $ITERNO
