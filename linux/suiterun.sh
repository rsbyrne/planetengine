#!/bin/bash
umask 0000
SCRIPT=${1:-localscript.py}
JOBS=${2:-1}
CHUNKS=${3:-1}
CORESPERCHUNK=${4:-1}
CHUNKNO=0
JOBSPERCHUNK=$((($JOBS+$CHUNKS-1)/$CHUNKS))
rm -rf logs
mkdir -p logs
# SCRIPTSDIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
SCRIPTSDIR=/home/jovyan/workspace/planetengine/linux
while [ $CHUNKNO -lt $CHUNKS ]
do
    touch logs/job$CHUNKNO.out
    touch logs/job$CHUNKNO.error
    $SCRIPTSDIR/chunkrun.sh $SCRIPT $CHUNKS $CHUNKNO $JOBSPERCHUNK $CORESPERCHUNK &
    echo "Submitted chunk " $CHUNKNO
    CHUNKNO=$(($CHUNKNO+1))
done
