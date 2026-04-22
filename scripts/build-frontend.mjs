import { cpSync, mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import { dirname } from 'node:path';
import { gzipSync } from 'node:zlib';

const source = 'frontend/herald-card.js';
const target = 'custom_components/herald/frontend/herald-card.js';
const targetGzip = 'custom_components/herald/frontend/herald-card.js.gz';

mkdirSync(dirname(target), { recursive: true });
cpSync(source, target);
writeFileSync(targetGzip, gzipSync(readFileSync(source)));
