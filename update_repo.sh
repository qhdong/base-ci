#!/bin/bash

source run_or_fail.sh

# delete the old .commit_id
rm -f .commit_id

run_or_fail "Repository folder not found!" pushd $1 1> /dev/null
run_or_fail "Could not reset git" git reset --hard HEAD

# call git log and parse the output, find most recent commit ID
COMMIT=$(run_or_fail "Could not call 'git log' on repository" git log -n1)
if [ $? != 0 ]; then
    echo "Could not call 'git log' on repository"
    exit 1
fi
COMMIT_ID=`echo $COMMIT | awk '{ print $2 }'`

# pulls the repo, getting any recent changes
# then get the most recent commit ID

run_or_fail "Could not pull from repository" git pull

COMMIT=$(run_or_fail "Could not call 'git log' on repository" git log -n1)
if [ $? != 0 ]; then
    echo "Could not call 'git log' on repository"
    exit 1
fi
NEW_COMMIT_ID=`echo $COMMIT | awk '{ print $2 }'`

# if the id changed, then write it to a file
if [ $NEW_COMMIT_ID != $COMMIT_ID ]; then
    popd 1> /dev/null
    echo $NEW_COMMIT_ID > .commit_id
fi




