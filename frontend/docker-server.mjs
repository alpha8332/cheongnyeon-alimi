import { createReadStream, existsSync, statSync } from 'node:fs';
import { createServer } from 'node:http';
import { extname, join, normalize } from 'node:path';

const root = '/app/dist';
const port = Number.parseInt(process.env.PORT || '3000', 10);
const contentTypes = new Map([
  ['.css', 'text/css; charset=utf-8'],
  ['.html', 'text/html; charset=utf-8'],
  ['.ico', 'image/x-icon'],
  ['.js', 'text/javascript; charset=utf-8'],
  ['.json', 'application/json; charset=utf-8'],
  ['.map', 'application/json; charset=utf-8'],
  ['.png', 'image/png'],
  ['.svg', 'image/svg+xml'],
  ['.webp', 'image/webp'],
]);

createServer((request, response) => {
  const requestPath = decodeURIComponent(new URL(request.url || '/', 'http://localhost').pathname);
  if (requestPath === '/health') {
    response.writeHead(200, { 'content-type': 'application/json; charset=utf-8' });
    response.end('{"status":"ok"}');
    return;
  }

  const relativePath = normalize(requestPath).replace(/^(\.\.(\/|\\|$))+/, '').replace(/^[/\\]+/, '');
  let target = join(root, relativePath || 'index.html');
  if (!target.startsWith(root) || !existsSync(target) || statSync(target).isDirectory()) {
    target = join(root, 'index.html');
  }

  response.writeHead(200, {
    'content-type': contentTypes.get(extname(target)) || 'application/octet-stream',
    'x-content-type-options': 'nosniff',
  });
  createReadStream(target).pipe(response);
}).listen(port, '0.0.0.0');

