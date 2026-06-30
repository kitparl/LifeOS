import { readFileSync, existsSync } from 'node:fs';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { spawnSync } from 'node:child_process';

const __dirname = dirname(fileURLToPath(import.meta.url));
const envPath = resolve(__dirname, '../../backend/.env');

function readAppEnv() {
  if (!existsSync(envPath)) {
    return 'production';
  }
  const content = readFileSync(envPath, 'utf8');
  const match = content.match(/^ENV\s*=\s*(\S+)/m);
  return match ? match[1].toLowerCase() : 'production';
}

const appEnv = readAppEnv();
const isDev = ['dev', 'development', 'local'].includes(appEnv);
const configuration = isDev ? 'development' : 'production';

console.log(`LifeOS frontend: ENV=${appEnv} → production=${!isDev} (ng ${configuration})`);

const result = spawnSync(
  'npx',
  ['ng', 'serve', `--configuration=${configuration}`],
  { stdio: 'inherit', shell: true, cwd: resolve(__dirname, '..') },
);

process.exit(result.status ?? 1);
