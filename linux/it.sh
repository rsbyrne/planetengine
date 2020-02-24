#!/bin/bash
WORKDIR='/home/jovyan/workspace/'
IMAGE='underworldcode/uw2cylindrical:cylindrical'
# IMAGE='rsbyrne/phd:latest'
docker run -u 0 -v $PWD:$WORKDIR -it $IMAGE bash
