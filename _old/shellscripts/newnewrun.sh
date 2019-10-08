#!/bin/bash
umask 0000
SCRIPT=${1:-'run.py'}
JOBFILENAME=${2:-'None'}
CORES=${3:-1}
DIR=$(dirname "$(readlink -f "$0")")
LOGSDIR=$DIR"/logs"
mkdir -p $LOGSDIR
chmod -R 777 $LOGSDIR
filename=$(basename -- "$JOBFILENAME")
extension="${filename##*.}"
JOBNAME="${filename%.*}"
OUTFILE=$LOGSDIR"/"$JOBNAME".out"
ERRORFILE=$LOGSDIR"/"$JOBNAME".error"
touch $OUTFILE
touch $ERRORFILE
echo $DIR
echo "Started job " $JOBNAME
mpirun -np $CORES python $SCRIPT $JOBNAME > $OUTFILE 2> $ERRORFILE
echo "$(tail -1000 $OUTFILE)" > $OUTFILE
echo "$(tail -1000 $ERRORFILE)" > $ERRORFILE
echo "Finished job " $JOBNAME
