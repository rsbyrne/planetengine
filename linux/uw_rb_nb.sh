#!/bin/bash
docker run -u 0 -v $PWD:/workspace/user_data -p 8888:8888 -it rsbyrne/rsbphd:latest bash
