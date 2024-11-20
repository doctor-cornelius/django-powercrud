#!/bin/bash

# Initialize an empty string to hold the command
update_command="poetry add"

# Use process substitution to avoid creating a subshell
while read -r package
do
    # Append each package with @latest to the command string
    update_command="$update_command $package@latest"
done < <(awk '/^\[tool.poetry.dependencies\]/ {flag=1; next} /^\[/{flag=0} flag && /=/ {print $1}' pyproject.toml | sed 's/"//g' | grep -v "^python$")

# Execute the update command
echo "Running update command: $update_command"
# Uncomment the next line to actually execute the update command
$update_command

echo "All packages have been updated to their latest versions."
