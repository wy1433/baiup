#!/usr/bin/bash


installDir=~/.baiup

mkdir -p $installDir

cp -r bin src script $installDir

binDir=$installDir/bin

echo "export PATH" >> ~/.bash_profile
echo "export PATH=$binDir:\$PATH" >> ~/.bash_profile
source ~/.bash_profile

echo "install succ!"
