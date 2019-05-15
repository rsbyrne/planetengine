#!/bin/bash
CHUNKS=${2:-100}
CORESPERCHUNK=${3:-1}
SCRIPT=${1:-localscript.py}
i=0
end=$CHUNKS
while [ $i -le $end ]; do
    mpirun -np $CORESPERCHUNK python $SCRIPT $i &
    i=$(($i+1))
done
