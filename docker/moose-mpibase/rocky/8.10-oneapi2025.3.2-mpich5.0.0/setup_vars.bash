#!/bin/bash
set -x
set -e

source /opt/intel/oneapi/setvars.sh

TO_FILE="$1"
if [ -z "$TO_FILE" ]; then
    echo "Must provide command line argument with the file to save to"
    exit 1
fi
echo "#/bin/sh" > "$TO_FILE"

# Search for the variables that have "oneapi" in the value
load_vars=()
for var in $(env | cut -d= -f1); do
    if [[ "${!var}" == **oneapi** ]]; then
        load_vars+=("$var")
    fi
done

# Extract the oneapi components from each variable
# and add to the script to be exported
for var in "${load_vars[@]}"; do
    add_values=()
    IFS=':' read -ra values <<< "${!var}"
    for value in "${values[@]}"; do
        if [[ $value == /opt/intel/oneapi** ]]; then
            add_values+=("$value")
        fi
    done
    if [ ${#add_values} -gt 0 ]; then
        values_combined=$(IFS=: ; echo "${add_values[*]}")
        if [[ $var == **ROOT ]]; then
            echo "export ${var}=${values_combined}" >> "$1"
        else
            echo "export ${var}=$values_combined:\${${var}}" >> "$1"
        fi
    else
        echo "Did not capture anything from variable ${var}"
        exit 1
    fi
done
