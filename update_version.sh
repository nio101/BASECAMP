#!/bin/bash
version=$(git describe --tags --long|awk -F  "-" '{print $1"-"$2}')
date=$(date "+%d/%m/%Y %H:%M")
echo "$version ($date)"> _version_.txt
