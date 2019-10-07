#!/bin/bash
umask 0000
SCRIPT=${1:-'run.py'}
JOBID=${2:-'None'}
CORES=${3:-1}
DIR=$(dirname "$(readlink -f "$0")")
LOGSDIR=$DIR"/logs"
mkdir -p $LOGSDIR
chmod -R 777 $LOGSDIR
OUTFILE=$LOGSDIR"/"$JOBID".out"
ERRORFILE=$LOGSDIR"/"$JOBID".error"
touch $OUTFILE
touch $ERRORFILE
echo $DIR
echo "Started job " $JOBID
mpirun -np $CORES python $SCRIPT $JOBID > $OUTFILE 2> $ERRORFILE
echo "$(tail -1000 $OUTFILE)" > $OUTFILE
echo "$(tail -1000 $ERRORFILE)" > $ERRORFILE
echo "Finished job " $JOBID
