#!/bin/bash
umask 0000
SCRIPT=${1:-localscript.py}
CHUNKS=${2:-100}
CORESPERCHUNK=${3:-1}
i=0
end=$CHUNKS
mkdir logs
while [ $i -le $end ]
do
    touch logs/job$i.out
    touch logs/job$i.error
    mpirun -np $CORESPERCHUNK python $SCRIPT $CHUNKS $i > logs/job$i.out 2> logs/job$i.error &
    i=$(($i+1))
done