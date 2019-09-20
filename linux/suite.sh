#!/bin/bash
umask 0000
SCRIPT=${1:-localscript.py}
CHUNKS=${2:-1}
CORESPERCHUNK=${3:-1}
CHUNKNO=0
rm -rf logs
mkdir -p logs
# SCRIPTSDIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
SCRIPTSDIR=/home/jovyan/workspace/planetengine/linux
while [ $CHUNKNO -lt $CHUNKS ]
do
    touch logs/job$CHUNKNO.out
    touch logs/job$CHUNKNO.error
    sh $SCRIPTSDIR/chunkrun.sh $SCRIPT $CHUNKS $CHUNKNO $CORESPERCHUNK &
    echo "Submitted chunk " $CHUNKNO
    CHUNKNO=$(($CHUNKNO+1))
done
