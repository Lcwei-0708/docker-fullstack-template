#!/bin/sh
npm install --include=dev
npm run generate-sitemap
npm run build
npm run preview