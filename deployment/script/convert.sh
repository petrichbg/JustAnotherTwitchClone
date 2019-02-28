#!/bin/bash

#cd to dir where script is located
if ! cd /var/www/stream/streampreview; then
    exit 1
fi

#please someone do this correctly
prefix="./http%3A%2F%2F"
suffix="_RECORDED*"
outputName=$2
outputName=${outputName#$prefix}
outputName=${outputName%%$suffix}

ffmpeg -y -i $1 -s 196x110 $outputName.png
rm $1