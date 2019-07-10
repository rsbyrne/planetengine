#!/bin/bash
CORES=${2:-1}
SCRIPT=$2{1:-localscript.py}
docker run -v $PWD:/home/jovyan/workspace/ underworldcode/uw2cylindrical:cylindrical mpirun -np $CORES python user_data/$SCRIPT $3
