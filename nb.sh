#!/bin/bash
MOUNTFROM=$PWD
MOUNTTO='/home/jovyan/workspace'
IMAGE='rsbyrne/planetengine:latest'
SOCK='/var/run/docker.sock'
docker run -v $MOUNTFROM:$MOUNTTO -v $SOCK:$SOCK --shm-size 2g -p 8888:8888 $IMAGE \
  jupyter notebook --no-browser --allow-root --port=8888 --ip='0.0.0.0'
