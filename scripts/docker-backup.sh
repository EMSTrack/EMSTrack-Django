#!/bin/bash

if [ $# -eq 0 ]
  then
    echo "error: please provide the name of the container"
    exit 1
fi

echo "> Copying fixtures"
docker cp -a $1:/etc/emstrack/fixtures etc/emstrack/

echo "> Copying letsencrypt certificates"
docker cp -a $1:/etc/emstrack/letsencrypt etc/emstrack/
