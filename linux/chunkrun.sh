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
while [ $ITERNO -lt $MAXITER ]
do
    $SCRIPTSDIR/singlerun.sh $SCRIPT $CHUNKS $CHUNKNO $ITERNO $CORES
    ITERNO=$(($ITERNO+1))
done
