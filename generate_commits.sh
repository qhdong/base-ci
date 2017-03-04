#!/bin/bash

source run_or_fail.sh

run_or_fail "Repository folder not found!" pushd $1 1> /dev/null

while true
do
    run_or_fail "Can't touch file" date > file
    run_or_fail "Could not add commits" git add file
    run_or_fail "Could not add commits" git commit -m "`date`"
    sleep 1
done

popd 1> /dev/null
