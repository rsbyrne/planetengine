#!/bin/bash
umask 0000
SCRIPT=${1:-localscript.py}
JOBS=${2:-1}
CHUNKS=${3:-1}
CORESPERCHUNK=${4:-1}
SHUFFLESEED=${5:-0}
CHUNKNO=0
JOBSPERCHUNK=$((($JOBS+$CHUNKS-1)/$CHUNKS))
rm -rf logs
mkdir -p logs
# SCRIPTSDIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
SCRIPTSDIR=/home/jovyan/workspace/planetengine/linux
echo "Dispatching chunks..."
OUTFILE="logs/suite.out"
ERRORFILE="logs/suite.error"
touch $OUTFILE
touch $ERRORFILE
while [ $CHUNKNO -lt $CHUNKS ]
do
    $SCRIPTSDIR/chunkrun.sh $SCRIPT $CHUNKS $SHUFFLESEED $CHUNKNO $JOBSPERCHUNK $CORESPERCHUNK >> $OUTFILE 2>> $ERRORFILE &
    echo "Submitted chunk " $CHUNKNO
    CHUNKNO=$(($CHUNKNO+1))
done
echo "All chunks dispatched."
