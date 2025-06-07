import { createWriteStream } from 'fs';
import { routes } from '../src/router/routes.js';
import { ENV_NODE } from '../src/config/env.node.js';
import { SitemapStream, streamToPromise } from 'sitemap';

const sitemap = new SitemapStream({ hostname: ENV_NODE.SITE_URL || 'http://localhost' });

routes.forEach(route => {
  sitemap.write({ url: route.path, changefreq: 'weekly', priority: 0.8 });
});
sitemap.end();

streamToPromise(sitemap).then(data => {
  createWriteStream('public/sitemap.xml').end(data);
});