import { spawn } from 'node:child_process';
import { createHash } from 'node:crypto';
import { access, mkdir, mkdtemp, readFile, rm, stat, writeFile } from 'node:fs/promises';
import { homedir, tmpdir } from 'node:os';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { setTimeout as delay } from 'node:timers/promises';

export const packageRoot = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const windows = process.platform === 'win32';
const exists = path => access(path).then(() => true, () => false);

export function cacheHome(env = process.env, platform = process.platform) {
  if (env.RESUME_WRITER_HOME) return resolve(env.RESUME_WRITER_HOME);
  const base = platform === 'win32' ? (env.LOCALAPPDATA || join(homedir(), 'AppData', 'Local'))
    : platform === 'darwin' ? join(homedir(), 'Library', 'Caches')
    : (env.XDG_CACHE_HOME || join(homedir(), '.cache'));
  return join(base, 'resume-writer');
}

export function run(command, args, { env = process.env, quiet = false } = {}) {
  return new Promise((resolveRun, reject) => {
    const child = spawn(command, args, { env, stdio: quiet ? 'ignore' : 'inherit', windowsHide: true });
    const interrupt = () => { if (!child.killed) child.kill('SIGINT'); };
    const terminate = () => { if (!child.killed) child.kill('SIGTERM'); };
    process.on('SIGINT', interrupt);
    process.on('SIGTERM', terminate);
    const cleanup = () => {
      process.off('SIGINT', interrupt);
      process.off('SIGTERM', terminate);
    };
    child.once('error', error => { cleanup(); reject(error); });
    child.once('exit', (code, signal) => {
      cleanup();
      if (signal === 'SIGINT' || signal === 'SIGTERM') {
        const error = new Error('Stopped.');
        error.code = signal;
        reject(error);
      } else if (code === 0) resolveRun();
      else reject(new Error(`${command} exited with code ${code}. See the message above, then retry.`));
    });
  });
}

async function installUv(home, env) {
  const binary = join(home, 'uv', windows ? 'uv.exe' : 'uv');
  if (await exists(binary)) return binary;
  console.log('Preparing the Python installer (uv from astral.sh)…');
  const directory = await mkdtemp(join(tmpdir(), 'resume-writer-'));
  try {
    const script = join(directory, windows ? 'install.ps1' : 'install.sh');
    const response = await fetch(`https://astral.sh/uv/install.${windows ? 'ps1' : 'sh'}`, {
      signal: AbortSignal.timeout(60000),
    });
    if (!response.ok) throw new Error(`Could not download uv: HTTP ${response.status}.`);
    await writeFile(script, await response.text(), { mode: 0o600 });
    const installerEnv = { ...env, UV_UNMANAGED_INSTALL: join(home, 'uv'), UV_NO_MODIFY_PATH: '1' };
    await run(windows ? 'powershell.exe' : 'sh', windows
      ? ['-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', script]
      : [script], { env: installerEnv });
    if (!await exists(binary)) throw new Error('The uv installer did not create its executable. Please retry setup.');
    return binary;
  } finally {
    await rm(directory, { recursive: true, force: true });
  }
}

// Serialize first-run setup so simultaneous launches cannot alter the same environment.
export async function withSetupLock(home, task) {
  await mkdir(home, { recursive: true });
  const lock = join(home, 'setup.lock');
  const deadline = Date.now() + 10 * 60 * 1000;
  let announced = false;
  while (true) {
    try {
      await mkdir(lock);
      await writeFile(join(lock, 'pid'), String(process.pid));
      break;
    } catch (error) {
      if (error.code !== 'EEXIST') throw error;
      const pid = Number(await readFile(join(lock, 'pid'), 'utf8').catch(() => ''));
      let stale = false;
      if (Number.isInteger(pid) && pid > 0) {
        try { process.kill(pid, 0); } catch (error) { stale = error.code === 'ESRCH'; }
      } else {
        const info = await stat(lock).catch(() => null);
        stale = info && Date.now() - info.mtimeMs > 30000;
      }
      if (stale) { await rm(lock, { recursive: true, force: true }); continue; }
      if (Date.now() > deadline) throw new Error('Another setup is still running. Let it finish and retry.');
      if (!announced) { console.log('Waiting for the other Resume Writer setup…'); announced = true; }
      await delay(500);
    }
  }
  try { return await task(); }
  finally { await rm(lock, { recursive: true, force: true }); }
}

export async function ensureRuntime({ pdf = false } = {}) {
  const home = cacheHome();
  const baseRequirements = join(packageRoot, 'requirements.txt');
  const pdfRequirements = join(packageRoot, '.github', 'skills', 'resume-writing', 'requirements-pdf.txt');
  const requirements = await Promise.all([baseRequirements, pdfRequirements].map(path => readFile(path)));
  const version = createHash('sha256').update('python3.12-v1').update(Buffer.concat(requirements)).digest('hex').slice(0, 12);
  const directory = join(home, `runtime-${process.platform}-${process.arch}-${version}`);
  const python = join(directory, windows ? 'Scripts' : 'bin', windows ? 'python.exe' : 'python');
  const env = {
    ...process.env,
    UV_PYTHON_INSTALL_DIR: join(home, 'python'),
    UV_CACHE_DIR: join(home, 'downloads'),
    PLAYWRIGHT_BROWSERS_PATH: join(home, 'browsers'),
    PYTHONUNBUFFERED: '1',
    PYTHONDONTWRITEBYTECODE: '1',
  };
  const ready = join(directory, 'base-ready');
  const pdfReady = join(directory, 'pdf-ready');
  return withSetupLock(home, async () => {
    const uv = await installUv(home, env);
    if (!await exists(python)) {
      console.log('Setting up a private Python 3.12 environment…');
      await run(uv, ['venv', '--no-config', '--python', '3.12', '--managed-python', directory], { env });
    }
    if (!await exists(ready)) {
      console.log('Installing resume dependencies…');
      await run(uv, ['pip', 'install', '--no-config', '--python', python, '-r', baseRequirements], { env });
      await writeFile(ready, 'ready\n');
    }
    if (pdf && !await exists(pdfReady)) {
      console.log('Preparing Word and PDF exports (including Chromium)…');
      await run(uv, ['pip', 'install', '--no-config', '--python', python, '-r', pdfRequirements], { env });
      await run(python, ['-m', 'playwright', 'install', 'chromium'], { env });
      // Verify that downloaded Chromium can launch, especially on Linux.
      await run(python, ['-c', 'from playwright.sync_api import sync_playwright\nwith sync_playwright() as p:\n b = p.chromium.launch()\n b.close()'], { env });
      await writeFile(pdfReady, 'ready\n');
    }
    return { python, env };
  });
}
