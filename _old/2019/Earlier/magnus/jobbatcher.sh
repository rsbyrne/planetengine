#!/bin/bash

JOBSCRIPT=${1:-multijobscript.sh}
CHUNKS=${2:-1}
i=0
end=$(expr $CHUNKS - 1)
while [ $i -le $end ]
do
sbatch --export=CHUNKS=$CHUNKS,CHUNKNO=$i $JOBSCRIPT
i=$(($i+1))
done