#!/bin/sh
npm install
npm run generate-sitemap

if [ -w /app ]; then
    chown -R 1000:1000 /app
    echo "Changed ownership of /app to UID 1000"
else
    echo "Warning: Cannot change ownership - insufficient permissions or /app is not writable"
fi

npm run dev