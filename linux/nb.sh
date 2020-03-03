#!/bin/bash

MOUNTTO='/home/jovyan/workspace'
IMAGE='rsbyrne/planetengine:latest'
docker run -u 0 -v $PWD:$MOUNTTO -p 8888:8888 $IMAGE \
  jupyter notebook --no-browser --allow-root --ip='0.0.0.0'
