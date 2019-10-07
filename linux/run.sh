#!/bin/bash
umask 0000
CORES=${1:-1}
DIR=${2:-$(dirname "$(readlink -f "$0")")}
RUNSCRIPT=${3:-$DIR"/run.py"}
JOBDIR=$DIR"/job/"
LOGSDIR=$DIR"/logs/"
# RUNNINGDIR=$JOBSDIR"/running"
# DONEDIR=$JOBSDIR"/done"
mkdir -p $JOBDIR
mkdir -p $LOGSDIR
# mkdir -p $RUNNINGDIR
# mkdir -p $DONEDIR
chmod -R 777 $JOBDIR
chmod -R 777 $LOGSDIR
# chmod -R 777 $RUNNINGDIR
# chmod -R 777 $DONEDIR
OUTFILE=$LOGSDIR"/run.out"
ERRORFILE=$LOGSDIR"/run.error"
SCRIPTSDIR="/home/jovyan/workspace/planetengine/_runsh"
SINGLERUNSH=$SCRIPTSDIR"/singlerun.sh"
if [ "$(ls -A $JOBDIR)" ]; then
  JOBFILE=$(ls $JOBDIR"job"*".json" | sort -n | head -1)
  sh $SINGLERUNSH $RUNSCRIPT $JOBFILE $CORES >> $OUTFILE 2>> $ERRORFILE &
else
  echo "No jobs to do!"
fi
