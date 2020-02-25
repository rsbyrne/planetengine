#!/bin/bash

# MOUNTTO='/workspace/mount'
# IMAGE='rsbyrne/planetengine:latest'
# docker run --init -v $PWD:$MOUNTTO -p 8888:8888 $IMAGE

MOUNTTO='/home/jovyan/workspace'
IMAGE='underworldcode/uw2cylindrical:cylindrical'
docker run -u 0 -v $PWD:$MOUNTTO -p 8888:8888 $IMAGE
