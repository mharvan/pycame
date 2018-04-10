#!/bin/bash
#
# Schedule actions to happen 10 minutes before sunrise.
# Actions: Open various blinds.
#

# Fail on errors.
set -e

# Read in open weather map settings
SRCDIR=`dirname $0`
source $SRCDIR/owm.sh

BEFORE=600

# Retrieve sunset time from openweathermap.
# Time is a unix timestamp (seconds since epoch).
SUNRISE=`http "http://api.openweathermap.org/data/2.5/weather?lat=$LAT&lon=$LON&units=metric&APPID=$APPID" | jq -r '.sys.sunrise' `
# Add delay.
ACTIONTIMEUNIX=$((SUNRISE-BEFORE))
# Convert unix timestamp to a format accepted by command "at": hour and minute.
ACTIONTIME=`date '+%H:%M' -d @$ACTIONTIMEUNIX`

# Schedule action.
at $ACTIONTIME <<EOF
/usr/bin/python3 /home/mharvan/pycame/domo.py blinds kitchen angle 1
/usr/bin/python3 /home/mharvan/pycame/domo.py blinds streck angle 1
/usr/bin/python3 /home/mharvan/pycame/domo.py blinds living up
EOF
