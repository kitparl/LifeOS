import { createHash } from 'node:crypto';
import { existsSync, mkdirSync, readFileSync, renameSync, rmSync, writeFileSync } from 'node:fs';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { spawnSync } from 'node:child_process';
import { tmpdir } from 'node:os';

// Bump DRAWIO_VERSION in drawio-version.ts and WAR_SHA256 together.
const WAR_SHA256 = 'a57b06b3b6a876a351dacfe65d027d9509319cd030e9bacf6ae04a034d66a38f';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const versionSource = readFileSync(resolve(root, 'src/app/features/planner/drawio-version.ts'), 'utf8');
const version = versionSource.match(/DRAWIO_VERSION\s*=\s*'([^']+)'/)?.[1];
if (!version) {
  throw new Error('DRAWIO_VERSION not found in drawio-version.ts');
}

// The version dir only ever appears via the final rename below, so its presence means a complete extract.
const target = resolve(root, 'drawio-dist', version);
if (existsSync(target)) {
  process.exit(0);
}
const staging = `${target}.partial`;

const url = `https://github.com/jgraph/drawio/releases/download/v${version}/draw.war`;
console.log(`Fetching draw.io ${version} ...`);
const response = await fetch(url);
if (!response.ok) {
  throw new Error(`Download failed: ${response.status} ${url}`);
}
const war = Buffer.from(await response.arrayBuffer());
const actual = createHash('sha256').update(war).digest('hex');
if (actual !== WAR_SHA256) {
  throw new Error(`draw.war SHA-256 mismatch: expected ${WAR_SHA256}, got ${actual}`);
}

rmSync(staging, { recursive: true, force: true });
mkdirSync(staging, { recursive: true });
const warPath = resolve(tmpdir(), `drawio-${version}.war`);
writeFileSync(warPath, war);
const unzip = spawnSync('unzip', ['-q', '-o', warPath, '-d', staging], { stdio: 'inherit' });
rmSync(warPath, { force: true });
if (unzip.status !== 0) {
  rmSync(staging, { recursive: true, force: true });
  throw new Error('unzip of draw.war failed');
}
rmSync(resolve(staging, 'WEB-INF'), { recursive: true, force: true });
rmSync(resolve(staging, 'META-INF'), { recursive: true, force: true });
renameSync(staging, target);
console.log(`draw.io ${version} ready in drawio-dist/${version}`);
