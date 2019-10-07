#!/bin/bash
umask 0000
SCRIPT=${1:-"campaign.py"}
NAME=${2:-"test"}
THREADS=${2:-1}
CORESPERTHREAD=${3:-3}
SCRIPTSDIR=/home/jovyan/workspace/planetengine/linux
OUTDIR="/home/jovyan/workspace/out"
OUTPATH=$OUTDIR$NAME
CAMPAIGNFILE=$OUTPATH"_campaign.py"
touch $OUTDIR
chmod -R 777 $OUTDIR
touch $OUTPATH
chmod -R 777 $OUTPATH
cp $SCRIPT $CAMPAIGNFILE
python $SCRIPT

#for job in "job"*".json"; do sudo touch "NEW"$job; sudo cp $job "NEW"$job; done
