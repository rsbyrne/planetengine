#!/bin/bash
umask 0000
SCRIPT=${1:-localscript.py}
JOBS=${2:-1}
CHUNKS=${3:-1}
CORESPERCHUNK=${4:-1}
SCRIPTSDIR=/home/jovyan/workspace/planetengine/linux
echo "Commissioning suite..."
$SCRIPTSDIR/suiterun.sh $SCRIPT $JOBS $CHUNKS $CORESPERCHUNK
echo "Suite commissioned."
