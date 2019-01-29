#!/bin/bash
CORES=${2:-1}
SCRIPT=${1:-localscript.py}
i=0
end=100
DIR="$(cd "$(dirname "$0")" && pwd)"
while [ $i -le $end ]; do
    sudo sh $DIR/uw_ann_run.sh $SCRIPT $CORES $i > /dev/null 2> /dev/null &
    echo $i
    i=$(($i+1))
done
