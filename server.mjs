import express from 'express';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const app = express();
const staticDir = path.join(__dirname, 'frontend');

// НИКАКИХ ручных редиректов!
// app.get('/lufs', (req, res) => res.redirect(301, '/lufs/'));

// ВАЖНО: redirect:false, иначе будет 301
app.use('/lufs', express.static(staticDir, { index: 'index.html', redirect: false }));

// Можно оставить 127.0.0.1, чтобы ходить через Nginx reverse-proxy
const host = process.env.HOST || '127.0.0.1';
const port = Number(process.env.PORT) || 8211;

app.listen(port, host, () => {
  console.log(`[lufs] static server on http://${host}:${port}/lufs/ (cwd=${__dirname})`);
});
