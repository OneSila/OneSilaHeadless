#!/bin/bash

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd $DIR


if [ -d venv ]
then
    source venv/bin/activate
else
    source ../venv/bin/activate
fi


cd OneSila
./manage.py run_huey --huey-verbose
