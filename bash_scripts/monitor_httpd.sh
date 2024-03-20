#!/bin/bash
# Monitoring script for webservers
# Dan Leroux
# Block Height 834701

# Modify the following variables so they work with your environment
# EDA=<FULLY_QUALIFIED_HOST_NAME_OF_YOUR_EDA_CONTROLLER>
# SITES=List of servers you'll monitor the httpd response

# EDA CONTROLLER 
EDA=eda.nleroux.ca

# LIST OF LINUX HTTPD SERVERS THIS BASH SCRIPT WILL MONITOR
SITES=("servera" "serverd" "r7a")

# Spinner
spinner="/|\\-/|\\-"
total_cycles=38 # Total number of cycles to achieve approximately 60 seconds

# Loop forever every two minutes
while true ; do

  # Loop through each site
  for SITE in "${SITES[@]}"; do
    # Use curl to get the HTTP status code
    STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$SITE")

    # Check if the status is not 200
    if [ "$STATUS" -ne 200 ]; then
        echo "Site $SITE is not responding with status 200. Response code: $STATUS"
        curl -H 'Content-Type: application/json' -d "{\"payload\": \"$SITE down\"}" eda.nleroux.ca:5000/endpoint
    fi
  done

  # Spin the wheel for approx 60 seconds
  for (( cycle=1; cycle<=total_cycles; cycle++ )); do
    for i in {0..7}; do
      echo -ne "${spinner:i:1}" "\r"
      sleep 0.2
    done
  done

done

