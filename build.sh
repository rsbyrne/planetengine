#!/bin/bash
currentDir=$PWD
cd "$(dirname "$0")"
# sh push.sh
docker build -t rsbyrne/planetengine:latest .
docker push rsbyrne/planetengine:latest
cd $currentDir
