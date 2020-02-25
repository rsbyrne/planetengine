#!/bin/bash

MOUNTTO='/home/jovyan/workspace'
IMAGE='rsbyrne/planetengine:latest'
docker run -u 0 -v $PWD:$MOUNTTO -it -p 8888:8888 $IMAGE bash
