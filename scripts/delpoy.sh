#!/bin/bash

# Define colors.
bright_cyan="\x1b[96m"
bright_yellow="\x1b[93m"
reset="\x1b[0m"

# Define scripts to deploy to ./local/bin.
declare -a scripts=(
"dupe"
"glue"
"order"
"peek"
"scan"
"seek"
"show"
"slice"
"subs"
"tally"
"track"
"when"
)

# Check OS.
system="$(uname -s)"

# Deploy scripts.
for script in "${scripts[@]}"; do
    printf "%b%s%b: Deploying Python script: %b%s%b\n" "${bright_yellow}" "$(basename "${0}")" "${reset}" "${bright_cyan}" "${script}" "${reset}"

    # Copy generic POSIX script, renaming it to the script name.
    cp "${HOME}/GitHub/PyTools/scripts/posix.sh" "${HOME}/.local/bin/${script}"

    # Replace generic script name with the actual script name.
    if [ "${system}" = "Linux" ]; then
        sed -i "s/python-script/${script}/g" "${HOME}/.local/bin/${script}"
    elif [ "${system}" = "Darwin" ]; then
        sed -i '' "s/python-script/${script}/g" "${HOME}/.local/bin/${script}"
    else
        printf "%s: system not supported\n" "${0}" >&2
        exit 1
    fi
done
