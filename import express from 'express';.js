import express from 'express';
import fs from 'fs';
import path from 'path';
import process from 'process';

const app = express();
const PORT = process.env.PORT || 3000;

const EXPORT_FILE = path.join(process.cwd(), '..', 'backend', 'data', 'exports', 'categorized_prompts.json');

app.get('/health', (_, res) => {
  res.json({ status: 'ok' });
});

app.get('/prompts', (req, res) => {
  if (!fs.existsSync(EXPORT_FILE)) {
    return res.status(503).json({ error: 'No export file yet. Run classifier.' });
  }
  const raw = fs.readFileSync(EXPORT_FILE, 'utf-8');
  const data = JSON.parse(raw);

  const { category, limit = 50 } = req.query;
  let filtered = data;
  if (category) {
    filtered = data.filter(r => r.categories.includes(category));
  }
  res.json(filtered.slice(0, Number(limit)));
});

app.listen(PORT, () => {
  console.log(`API running: http://localhost:${PORT}`);
});