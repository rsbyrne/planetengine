#!/bin/bash

# MOUNTTO='/workspace/mount'
# IMAGE='rsbyrne/planetengine:latest'
# docker run --init -v $PWD:$MOUNTTO -it $IMAGE bash

MOUNTTO='/home/jovyan/workspace'
IMAGE='underworldcode/uw2cylindrical:cylindrical'
docker run -u 0 -v $PWD:$MOUNTTO -it $IMAGE bash
