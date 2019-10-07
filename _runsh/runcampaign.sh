#!/bin/bash
umask 0000
SCRIPT=${1:-"run.py"}
NAME=${2:-"test"}
THREADS=${2:-1}
CORESPERTHREAD=${3:-3}
SCRIPTSDIR=/home/jovyan/workspace/planetengine/linux
OUTDIR="/home/jovyan/workspace/out"
touch $OUTDIR
chmod -R 777 $OUTDIR
cp $SCRIPT $OUTDIR"run.py"
python $SCRIPT
