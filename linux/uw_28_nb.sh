#!/bin/bash
docker run -v $PWD:/home/jovyan/workspace/ -p 8888:8888 underworldcode/underworld2:v2.8_release
