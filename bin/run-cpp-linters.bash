#!/usr/bin/env bash

set -euo pipefail

EXCLUDE_DIRS=("src/kuka_kr210_support")

ABS_EXCLUDES=()
for dir in "${EXCLUDE_DIRS[@]}"; do
    ABS_EXCLUDES+=("$(realpath "$dir")")
done

changed=0

while IFS= read -r -d '' file; do
    skip=false
    FILE_PATH=$(realpath "$file")
    for excl in "${ABS_EXCLUDES[@]}"; do
        if [[ "$FILE_PATH" == "$excl"* ]]; then
            skip=true
            break
        fi
    done

    if [ "$skip" = false ]; then
        original_hash=$(sha256sum "$file" | awk '{ print $1 }')
        clang-format -i "$file"
        new_hash=$(sha256sum "$file" | awk '{ print $1 }')
        if [[ "$original_hash" != "$new_hash" ]]; then
            echo "Formatted: $file"
            changed=1
        fi
    fi
done < <(find src -type f \( -name "*.cpp" -o -name "*.h" -o -name "*.cc" -o -name "*.hpp" \) -print0)

exit "$changed"

