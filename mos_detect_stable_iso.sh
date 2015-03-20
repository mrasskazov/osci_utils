#!/bin/bash -e
set LANG=C

JENKINS_JOB="6.1.all"
JENKINS_PROT="http"
JENKINS_HOST="jenkins-product.srt.mirantis.net"
JENKINS_PORT="8080"

JENKINS_URL="$JENKINS_PROT://$JENKINS_HOST:$JENKINS_PORT"
JENKINS_JOB_URL="$JENKINS_URL/job/$JENKINS_JOB"

lastBuildNumber=$(curl -sS $JENKINS_JOB_URL/lastSuccessfulBuild/api/json \
    | python -c 'import json, sys; obj = json.load(sys.stdin); print obj["number"]')

while [ -z "$SUCCESSFULL_ISO_NUMBER" ]; do

    DOWNSTREAM_RESULTS=$(curl -sS "$JENKINS_JOB_URL/$lastBuildNumber/downstreambuildview/" \
        | grep -Eo '<a class="model-link".*?$' \
        | sed -e 's|</\?a[^>]*>||g')

    echo -n "$lastBuildNumber: "
    if echo -e "$DOWNSTREAM_RESULTS" | grep -v 'SUCCESS)$'; then
        ((lastBuildNumber--))
    else
        echo SUCCESSFULL
        export SUCCESSFULL_ISO_NUMBER="$lastBuildNumber"
    fi
done
