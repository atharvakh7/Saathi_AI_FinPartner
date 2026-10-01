#!/usr/bin/env node
/**
 * Checks src/i18n/{en,hi,mr,ta}.json (spec §4.10, step 31):
 *  - identical key sets (English is the source)
 *  - identical {{placeholders}} per key
 *  - no empty strings
 * Optional: --used scans src/ and app/ for t('…') keys that are missing from en.json.
 * Exit code 1 on any problem.
 */
const fs = require('fs');
const path = require('path');

const dir = path.join(__dirname, '..', 'src', 'i18n');
const langs = ['en', 'hi', 'mr', 'ta'];

function flatten(obj, prefix = '', out = {}) {
  for (const [k, v] of Object.entries(obj)) {
    const key = prefix ? `${prefix}.${k}` : k;
    if (v && typeof v === 'object') flatten(v, key, out);
    else out[key] = v;
  }
  return out;
}

const placeholders = (s) => new Set((String(s).match(/{{\s*\w+\s*}}/g) || []).map((p) => p.replace(/\s/g, '')));
const files = Object.fromEntries(
  langs.map((l) => [l, flatten(JSON.parse(fs.readFileSync(path.join(dir, `${l}.json`), 'utf8')))]),
);
const problems = [];
const en = files.en;

for (const lang of langs) {
  const f = files[lang];
  for (const key of Object.keys(en)) {
    if (!(key in f)) problems.push(`${lang}: missing ${key}`);
  }
  for (const [key, value] of Object.entries(f)) {
    if (!(key in en)) problems.push(`${lang}: extra key ${key}`);
    if (typeof value !== 'string' || !value.trim()) problems.push(`${lang}: empty ${key}`);
    if (key in en) {
      const a = [...placeholders(en[key])].sort().join(',');
      const b = [...placeholders(value)].sort().join(',');
      if (a !== b) problems.push(`${lang}: ${key} placeholders {${b}} != en {${a}}`);
    }
  }
}

if (process.argv.includes('--used')) {
  const root = path.join(__dirname, '..');
  const used = new Set();
  const walk = (d) => {
    for (const name of fs.readdirSync(d)) {
      const p = path.join(d, name);
      if (name === 'node_modules' || name.startsWith('.')) continue;
      if (fs.statSync(p).isDirectory()) walk(p);
      else if (/\.(tsx?|jsx?)$/.test(name)) {
        const src = fs.readFileSync(p, 'utf8');
        for (const m of src.matchAll(/\bt\(\s*['"`]([a-zA-Z0-9_.-]+)['"`]/g)) used.add(m[1]);
      }
    }
  };
  for (const d of ['src', 'app']) if (fs.existsSync(path.join(root, d))) walk(path.join(root, d));
  for (const key of used) {
    // a key ending in '.' was built dynamically (`language.greeting.${lang}`): it only needs a matching prefix
    const prefix = key.endsWith('.') ? key : `${key}.`;
    const isPrefix = Object.keys(en).some((k) => k.startsWith(prefix));
    if (!(key in en) && !isPrefix) problems.push(`code uses missing key ${key}`);
  }
}

if (problems.length) {
  console.error(`i18n check failed (${problems.length}):\n  ` + problems.join('\n  '));
  process.exit(1);
}
console.log(`i18n OK: ${Object.keys(en).length} keys x ${langs.length} languages`);
