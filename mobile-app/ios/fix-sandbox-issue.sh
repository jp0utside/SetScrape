#!/bin/bash

# Script to fix sandbox permission issues in React Native iOS builds
# This script disables the problematic parts of the Pods resources script

echo "Fixing sandbox permission issues..."

# Find the resources script
RESOURCES_SCRIPT=$(find Pods/Target\ Support\ Files/Pods-InternetArchiveMusicPlayer/ -name "*resources.sh" 2>/dev/null | head -1)

if [ -z "$RESOURCES_SCRIPT" ]; then
    echo "Resources script not found. Skipping sandbox fix."
    exit 0
fi

echo "Found resources script: $RESOURCES_SCRIPT"

# Create backup if it doesn't exist
if [ ! -f "${RESOURCES_SCRIPT}.backup" ]; then
    cp "$RESOURCES_SCRIPT" "${RESOURCES_SCRIPT}.backup"
    echo "Created backup: ${RESOURCES_SCRIPT}.backup"
fi

# Comment out the problematic lines
sed -i '' 's/^> "$RESOURCES_TO_COPY"$/# > "$RESOURCES_TO_COPY"/' "$RESOURCES_SCRIPT"
sed -i '' 's/^      echo "$RESOURCE_PATH" >> "$RESOURCES_TO_COPY"$/#      echo "$RESOURCE_PATH" >> "$RESOURCES_TO_COPY"/' "$RESOURCES_SCRIPT"

# Comment out the rsync commands
sed -i '' 's/^rsync -avr --copy-links --no-relative --exclude/# rsync -avr --copy-links --no-relative --exclude/' "$RESOURCES_SCRIPT"
sed -i '' 's/^if \[\[ "${ACTION}" == "install" \]\].*rsync/# if [[ "${ACTION}" == "install" ]] && [[ "${SKIP_INSTALL}" == "NO" ]]; then\n#   mkdir -p "${INSTALL_DIR}/${UNLOCALIZED_RESOURCES_FOLDER_PATH}"\n#   rsync/' "$RESOURCES_SCRIPT"
sed -i '' 's/^rm -f "$RESOURCES_TO_COPY"$/# rm -f "$RESOURCES_TO_COPY"/' "$RESOURCES_SCRIPT"

echo "Sandbox permission issues fixed in: $RESOURCES_SCRIPT"
