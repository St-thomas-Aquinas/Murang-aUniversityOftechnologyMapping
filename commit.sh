#!/bin/bash

# Directory containing the files
TARGET_DIR="React App/src/assets/MuT 2 photos"

# Change to the target directory
cd "$TARGET_DIR" || { echo "Directory not found"; exit 1; }

# Get a list of files (excluding directories)
files=(*)
total=${#files[@]}

# Go back to the project root (assumes .git is there)
cd - >/dev/null

# Commit 2 files at a time
i=0
while [ $i -lt $total ]; do
    file1="${TARGET_DIR}/${files[$i]}"
    file2=""
    if [ $((i+1)) -lt $total ]; then
        file2="${TARGET_DIR}/${files[$((i+1))]}"
        git add "$file1" "$file2"
        git commit -m "Add files: ${files[$i]} and ${files[$((i+1))]}"
        git push
        i=$((i+2))
    else
        git add "$file1"
        git commit -m "Add file: ${files[$i]}"
        git push
        i=$((i+1))
    fi
done