#!/bin/bash

source venv/bin/activate
flask db init
revision=`flask db migrate 2>&1 | tail -n1 | cut -f9 -d ' ' | tr -d "'"`
if [  -z "$revision" ]
then
    flask db upgrade
else
    echo -e "revision='$revision'\r\ndown_revision=None" > migrations/versions/${revision}_.py
    revision=`flask db migrate | tail -n1 | cut -f4 -d" "`
    grep -v drop ${revision} > tmp
    mv tmp ${revision}
    flask db upgrade
fi
