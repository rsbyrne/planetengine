#!/bin/bash
MOUNTFROM=$PWD
MOUNTTO='/home/jovyan/workspace'
IMAGE='rsbyrne/planetengine:latest'
SOCK='/var/run/docker.sock'
docker run -v $MOUNTFROM:$MOUNTTO -v $SOCK:$SOCK -it --shm-size 2g $IMAGE bash
