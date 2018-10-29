#!/bin/bash
#
# Schedule actions to happen 15 minutes after sunrise.
# Actions: Close blinds in the kitchen.
#

# Fail on errors.
set -e

# Read in open weather map settings
SRCDIR=`dirname $0`
source $SRCDIR/owm.sh

AFTER=900

# Retrieve sunset time from openweathermap.
# Time is a unix timestamp (seconds since epoch).
SUNSET=`http "http://api.openweathermap.org/data/2.5/weather?lat=$LAT&lon=$LON&units=metric&APPID=$APPID" | jq -r '.sys.sunset' `
# Add delay.
ACTIONTIMEUNIX=$((SUNSET+AFTER))
# Convert unix timestamp to a format accepted by command "at": hour and minute.
ACTIONTIME=`date '+%H:%M' -d @$ACTIONTIMEUNIX`

# Schedule action.
at $ACTIONTIME <<EOF
/usr/bin/python3 /home/mharvan/pycame/domo.py blinds kitchen down
/usr/bin/python3 /home/mharvan/pycame/domo.py blinds living down
EOF
