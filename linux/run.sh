#!/bin/bash
DIR=$(dirname "$(readlink -f "$0")")
MOUNTFROM=$(dirname "$DIR")/
CAMPAIGNDIR=$(basename "$DIR")/
MOUNTTO="/home/jovyan/workspace/"
SCRIPT='run.py'
IMAGE='underworldcode/uw2cylindrical:cylindrical'
INTERPRETER='python'
LOGSDIR=$MOUNTFROM
JOBNAME="test"
OUTFILE=$LOGSDIR"/"$JOBNAME".out"
ERRORFILE=$LOGSDIR"/"$JOBNAME".error"
touch $OUTFILE
touch $ERRORFILE
docker run -v $MOUNTFROM:$MOUNTTO $IMAGE $INTERPRETER $MOUNTTO$CAMPAIGNDIR$SCRIPT "$@" > $OUTFILE 2> $ERRORFILE &
