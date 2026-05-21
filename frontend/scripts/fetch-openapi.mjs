#!/usr/bin/env node
import { writeFileSync } from 'node:fs';

const url = process.env.OPENAPI_URL ?? 'http://localhost:8080/openapi.json';
const outputPath = 'openapi.json';

// Sort keys recursively so the committed snapshot diffs cleanly when the
// backend regenerates the schema with a different insertion order.
function sortKeys(value) {
  if (Array.isArray(value)) return value.map(sortKeys);
  if (value !== null && typeof value === 'object') {
    return Object.fromEntries(
      Object.keys(value)
        .sort()
        .map((k) => [k, sortKeys(value[k])])
    );
  }
  return value;
}

let res;
try {
  res = await fetch(url);
} catch (err) {
  console.error(`✘ Could not reach ${url}`);
  console.error(`  Is the backend running? Try: docker-compose up -d backend`);
  console.error(`  Underlying error: ${err.message}`);
  process.exit(1);
}

if (!res.ok) {
  console.error(`✘ ${url} returned ${res.status} ${res.statusText}`);
  process.exit(1);
}

const schema = sortKeys(await res.json());
writeFileSync(outputPath, JSON.stringify(schema, null, 2) + '\n');
console.log(`✔ Wrote ${outputPath} from ${url}`);
