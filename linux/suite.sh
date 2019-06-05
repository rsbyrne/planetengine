#!/bin/bash
umask 0000
CHUNKS=${2:-100}
CORESPERCHUNK=${3:-1}
SCRIPT=${1:-localscript.py}
i=0
end=$CHUNKS
while [ $i -le $end ]; do
    touch job$i.out
    touch job$i.error
    mpirun -np $CORESPERCHUNK python $SCRIPT $CHUNKS $i > job$i.out 2> job$i.error &
    i=$(($i+1))
done