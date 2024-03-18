#!/bin/bash
# Monitoring script for webservers
# Dan Leroux
# Block Height 834701

# Spinner
spinner="/|\\-/|\\-"
total_cycles=40 # Total number of cycles to achieve approximately 60 seconds

EDA=eda.nleroux.ca

# List of websites to check
SITES=("servera" "serverd" "r7a")

# Loop forever every two minutes
while true ; do

  # Loop through each site
  for SITE in "${SITES[@]}"; do
    # Use curl to get the HTTP status code
    STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$SITE")

    # Check if the status is not 200
    if [ "$STATUS" -ne 200 ]; then
        echo "Site $SITE is not responding with status 200. Response code: $STATUS"
        curl -H 'Content-Type: application/json' -d "{\"payload\": \"$SITE down\"}" localhost:5000/endpoint
    fi
  done

  # Spin the wheel for approx 80 seconds
  for (( cycle=1; cycle<=total_cycles; cycle++ )); do
    for i in {0..7}; do
      echo -ne "${spinner:i:1}" "\r"
      sleep 0.2
    done
  done

done

