#!/bin/bash
/bin/echo -e "\x1B[01;93m -= Updating git repo =- \x1B[0m"
git add . && git commit -m "$1" && git push
