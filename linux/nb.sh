#!/bin/bash
WORKDIR='/home/jovyan/workspace/'
IMAGE='underworldcode/uw2cylindrical:cylindrical'
# IMAGE='rsbyrne/phd:latest'
docker run -v $PWD:$WORKDIR -p 8888:8888 $IMAGE
