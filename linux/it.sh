#!/bin/bash
MOUNTTO='/workspace/mount'
IMAGE='rsbyrne/planetengine:latest'
# docker run --init --user $(id -u):$(id -g) -v $PWD:$MOUNTTO -it $IMAGE bash
docker run --init -v $PWD:$MOUNTTO -it $IMAGE bash
