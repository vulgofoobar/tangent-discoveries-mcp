#!/bin/bash
set -e

if [ -f .env ]; then
    while IFS='=' read -r key value; do
        [[ "$key" =~ ^#.*$ ]] && continue
        [ -z "$key" ] && continue

        key=$(echo "$key" | xargs)
        value=$(echo "$value" | xargs)

        export "$key=$value"
    done < .env
else
    echo "⚠ .env file not found. Copy .env.example and customize it:"
    echo "  cp .env.example .env"
    exit 1
fi

OBSIDIAN_PATH="${OBSIDIAN_ROUGH_NOTES:-$HOME/Library/Mobile Documents/iCloud~md~obsidian/Documents/Vault 32/01. rough notes}"

if [[ "$OBSIDIAN_PATH" == ~* ]]; then
    OBSIDIAN_PATH="${OBSIDIAN_PATH/#\~/$HOME}"
fi

if [ -d rough-notes ] && [ ! -L rough-notes ]; then
    rm -rf rough-notes
    echo "✓ Removed old folder"
fi

if [ -L rough-notes ]; then
    echo "✓ rough-notes symlink already exists"
else
    if [ -d "$OBSIDIAN_PATH" ]; then
        ln -s "$OBSIDIAN_PATH" rough-notes
        echo "✓ Created symlink: rough-notes → $OBSIDIAN_PATH"
    else
        echo "✗ Obsidian path not found: $OBSIDIAN_PATH"
        echo "Update OBSIDIAN_ROUGH_NOTES in .env to your rough notes path and try again."
        exit 1
    fi
fi

echo "✓ Setup complete"
