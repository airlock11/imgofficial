#!/usr/bin/env bash
set -euo pipefail

rm -rf www
mkdir -p www

rsync -a ./ www/ \
  --exclude='.git' \
  --exclude='.github' \
  --exclude='node_modules' \
  --exclude='www' \
  --exclude='android' \
  --exclude='package.json' \
  --exclude='package-lock.json' \
  --exclude='capacitor.config.json' \
  --exclude='.gitignore'

# Keep the bundled UI local while loading changing JSON sports/news data
# from the live IMG website.
while IFS= read -r -d '' file; do
  if ! grep -q 'native-data-bridge.js' "$file"; then
    sed -i 's#</head>#<script src="/native-data-bridge.js"></script></head>#' "$file"
  fi
done < <(find www -type f -name '*.html' -print0)

# The bridge itself must also be available at the app root.
cp native-data-bridge.js www/native-data-bridge.js

echo "Prepared IMG web bundle for Capacitor."
