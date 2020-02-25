#!/bin/bash
MOUNTTO='/workspace/mount'
IMAGE='rsbyrne/planetengine:latest'
docker run --init -v $PWD:$MOUNTTO -it $IMAGE bash
