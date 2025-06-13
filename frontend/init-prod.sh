#!/bin/sh
npm install --include=dev
npm run generate-sitemap
npm run build

# Keep container running
tail -f /dev/null