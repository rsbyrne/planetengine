#!/bin/bash
umask 0000
SCRIPT=${1:-localscript.py}
CHUNKS=${2:-1}
CHUNKNO=${3:-0}
JOBSPERCHUNK=${4:-1}
CORES=${5:-1}
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
    echo "Starting chunk " $CHUNKNO " job " $ITERNO
    $SCRIPTSDIR/singlerun.sh $SCRIPT $CHUNKS $CHUNKNO $ITERNO $CORES >> $OUTFILE 2>> $ERRORFILE
    ITERNO=$(($ITERNO+1))
    echo "Finishing chunk " $CHUNKNO " job " $ITERNO
done
echo "Finished chunk " $CHUNKNO
