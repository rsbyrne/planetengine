#!/bin/bash
MOUNTTO='/workspace/mount'
IMAGE='rsbyrne/planetengine:latest'
docker run --init -v $PWD:$MOUNTTO -p 8888:8888 $IMAGE
