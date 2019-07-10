#!/bin/bash
CORES=${2:-1}
SCRIPT=${1:-localscript.py}
docker run -v $PWD:/home/jovyan/workspace/ rsbyrne/rsbphd:latest mpirun -np $CORES python user_data/$SCRIPT $3
