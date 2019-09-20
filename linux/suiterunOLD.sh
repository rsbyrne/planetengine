#!/bin/bash
umask 0000
SCRIPT=${1:-localscript.py}
CHUNKS=${2:-1}
CORESPERCHUNK=${3:-1}
CHUNKNO=0
rm -rf logs
mkdir -p logs
while [ $CHUNKNO -lt $CHUNKS ]
do
    touch logs/job$CHUNKNO.out
    touch logs/job$CHUNKNO.error
    sudo docker run -v $PWD:/workspace/user_data -it underworldcode/uw2cylindrical:cylindrical \
        mpirun -np $CORESPERCHUNK python /workspace/user_data/$SCRIPT $CHUNKS $CHUNKNO \
        > logs/job$CHUNKNO.out 2> logs/job$CHUNKNO.error &
    echo "Submitted chunk " $CHUNKNO
    CHUNKNO=$(($CHUNKNO+1))
done
