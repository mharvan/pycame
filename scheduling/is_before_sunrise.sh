#!/bin/bash
#
# Script to check whether sunrise already happened.
#
# Return 0 if script is called before sunrise.
# Return 1 if called after or at sunrise.
# Return non-zero on errors.
#

# Fail on errors.
set -e

# Read in open weather map settings
SRCDIR=`dirname $0`
source $SRCDIR/owm.sh

# Retrieve sunset time from openweathermap.
# Time is a unix timestamp (seconds since epoch).
SUNRISE=`http "http://api.openweathermap.org/data/2.5/weather?lat=$LAT&lon=$LON&units=metric&APPID=$APPID" | jq -r '.sys.sunrise' `

# Current time
TIME=`date '+%s'`

# Bash arithmetic expression
(( SUNRISE > TIME ))

# POSIX shells
#[ "$SUNRISE" -gt "$TIME" ]
