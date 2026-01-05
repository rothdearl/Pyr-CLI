#!/bin/bash

# Define colors.
bright_cyan="\x1b[96m"
bright_yellow="\x1b[93m"
reset="\x1b[0m"

# Copy scripts to ./local/bin.
declare -a scripts=("concat" "dupe" "match" "peek" "seek" "show" "tally" "track")

for script in "${scripts[@]}"
do
    printf "%b%s%b: Deploying Python script: %b%s%b\n" "${bright_yellow}" "$(basename "${0}")" "${reset}" "${bright_cyan}" "${script}" "${reset}"
    cp "${HOME}/GitHub/PyTools/scripts/${script}.sh" "${HOME}/.local/bin/${script}"
done
