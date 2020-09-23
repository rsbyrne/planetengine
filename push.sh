#!/bin/bash
currentDir=$PWD
cd "$(dirname "$0")"
sudo chown -R ubuntu $PWD/.git
sudo chgrp -R ubuntu $PWD/.git
chmod 700 $PWD/.ssh/*
eval `ssh-agent -s`
ssh-add $PWD/.ssh/*.key
git remote set-url origin git+ssh://git@github.com/rsbyrne/planetengine
git add .
git commit -m "Automatic push."
git fetch
git merge -m "Automatic merge."
git push
sudo chown -R ubuntu $PWD/.git
sudo chgrp -R ubuntu $PWD/.git
cd $currentDir
