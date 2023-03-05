#!/bin/bash

# Initialize an empty array
commits=()

# Get the commit history with the desired format
log=$(git log --graph --pretty=format:'commit:%H,Author:%an,Description:%s,Date:%cd,Parents:%p%nChanged Files:%n' --name-status)

# Iterate over the commit history and extract the information into a dict
while IFS= read -r line; do
  if [[ $line == commit* ]]; then
    # Initialize a new commit dict
    commit=()
    commit['commit_ref']=$(echo "$line" | awk -F: '{print $2}')
    commit['author']=$(echo "$line" | awk -F: '{print $4}')
    commit['description']=$(echo "$line" | awk -F: '{print $6}')
    commit['date']=$(echo "$line" | awk -F: '{print $8}')
    commit['parents']=$(echo "$line" | awk -F: '{print $10}')
  elif [[ $line == [A-Z]* ]]; then
    # Add the changed files to the commit dict
    commit['changed_files']+="${line}"$'\n'
  else
    # Add the completed commit dict to the array
    commits+=("$commit")
  fi
done <<< "$log"

# Print the array of commits
printf '%s\n' "${commits[@]}"
