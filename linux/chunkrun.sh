#!/bin/bash
umask 0000
SCRIPT=${1:-localscript.py}
CHUNKS=${2:-1}
SHUFFLESEED=${3:-0}
CHUNKNO=${4:-0}
JOBSPERCHUNK=${5:-1}
CORES=${6:-1}
ITERNO=0
MAXITER=$JOBSPERCHUNK
SCRIPTSDIR=/home/jovyan/workspace/planetengine/linux
echo "Starting chunk " $CHUNKNO
OUTFILE="logs/chunk"$CHUNKNO".out"
ERRORFILE="logs/chunk"$CHUNKNO".error"
touch $OUTFILE
touch $ERRORFILE
while [ $ITERNO -lt $MAXITER ]
do
    $SCRIPTSDIR/singlerun.sh $SCRIPT $CHUNKS $SHUFFLESEED $CHUNKNO $ITERNO $CORES >> $OUTFILE 2>> $ERRORFILE
    ITERNO=$(($ITERNO+1))
done
echo "Finished chunk " $CHUNKNO
