#!/bin/bash
docker run -u 0 -v $PWD:/home/jovyan/workspace/ -p 8888:8888 -it rsbyrne/rsbphd:latest bash
