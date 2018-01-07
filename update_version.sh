#!/bin/bash
/bin/echo -e "\x1B[01;93m -= Updating version file =- \x1B[0m"
version=$(git describe --tags --long|awk -F  "-" '{print $1"-"$2}')
date=$(date "+%d/%m/%Y %H:%M")
echo "$version ($date)"> _version_.txt
