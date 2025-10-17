import http from 'node:http';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';
import handler from 'serve-handler';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const publicDir = join(__dirname, '..', 'public');

const port = Number.parseInt(process.env.PORT ?? '5173', 10);
const host = process.env.HOST ?? '0.0.0.0';

const server = http.createServer((request, response) => {
  return handler(request, response, {
    public: publicDir,
  });
});

server.listen(port, host, () => {
  const baseUrl = host === '0.0.0.0' ? 'localhost' : host;
  console.log(`Frontend available at http://${baseUrl}:${port}`);
});
