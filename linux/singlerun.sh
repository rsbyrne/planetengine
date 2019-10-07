#!/bin/bash
umask 0000
SCRIPT=${1:-'localscript.py'}
JOBFILE=${2:-'None'}
CORES=${3:-1}
LOGSDIR=$(dirname $JOBFILE)"/logs"
mkdir -p $LOGSDIR
chmod -R 777 $LOGSDIR
JOBNAME=$(basename $JOBFILE ".json")
OUTFILE=$LOGSDIR"/"$JOBNAME".out"
ERRORFILE=$LOGSDIR"/"$JOBNAME".error"
touch $OUTFILE
touch $ERRORFILE
echo "Started job " $JOBNAME
mpirun -np $CORES python $SCRIPT $JOBFILE > $OUTFILE 2> $ERRORFILE
echo "$(tail -1000 $OUTFILE)" > $OUTFILE
echo "$(tail -1000 $ERRORFILE)" > $ERRORFILE
echo "Finished job " $JOBNAME
