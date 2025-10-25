// server.mjs — простой сервер статики под /lufs
import express from 'express';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname  = path.dirname(__filename);

const app  = express();
const port = process.env.PORT || 3002;

const publicDir = path.join(__dirname, 'public');

app.set('trust proxy', true);

// Статика под /lufs
app.use('/lufs', express.static(publicDir, {
  etag: true,
  lastModified: true,
  maxAge: 0,
}));

// SPA fallback
app.get('/lufs/*', (_req, res) => {
  res.sendFile(path.join(publicDir, 'index.html'));
});

// Health фронта
app.get('/lufs/health', (_req, res) => res.type('text').send('OK\n'));

// 404 на прочее
app.use((_req, res) => res.status(404).send('Not Found'));

app.listen(port, '127.0.0.1', () => {
  console.log(`LUFS web listening on http://127.0.0.1:${port}/lufs/`);
});
