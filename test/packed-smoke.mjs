import assert from 'node:assert/strict';
import { spawn, spawnSync } from 'node:child_process';
import { once } from 'node:events';
import { mkdtemp, mkdir, rm, writeFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { packageRoot } from '../lib/runtime.mjs';

// This integration check may download Python/Chromium on first run. npm test stays offline.
const directory = await mkdtemp(join(tmpdir(), 'resume-packed-'));
const npm = process.env.npm_execpath;
assert.ok(npm, 'Run this check with npm run test:packed.');
const cache = join(directory, 'npm-cache');
const cwd = join(directory, 'My resumes');
const env = { ...process.env, RESUME_WRITER_HOME: process.env.RESUME_WRITER_HOME || join(directory, 'runtime') };
const markdown = '# Package Test\n\nPortfolio: https://example.com | test@example.com\n\n## Summary\n\nDesigner improving complex workflows.\n';

async function checkServer(args, inspect) {
  const child = spawn(process.execPath, [npm, 'exec', '--offline', '--yes', '--cache', cache, '--package', tarball, '--', 'resume-writer', ...args, '--no-open'], {
    cwd, env, detached: process.platform !== 'win32', stdio: ['ignore', 'pipe', 'pipe'],
  });
  const exited = once(child, 'exit');
  let output = '';
  try {
    const url = await new Promise((resolve, reject) => {
      const timeout = setTimeout(() => reject(new Error(`Startup timed out:\n${output}`)), 10 * 60 * 1000);
      const capture = chunk => {
        output += chunk.toString();
        const match = output.match(/Resume (?:review|preview): (http:\/\/127\.0\.0\.1:\d+\/)/);
        if (match) { clearTimeout(timeout); resolve(match[1]); }
      };
      child.stdout.on('data', capture);
      child.stderr.on('data', capture);
      child.once('error', error => { clearTimeout(timeout); reject(error); });
      child.once('exit', code => { clearTimeout(timeout); reject(new Error(`Startup exited ${code}:\n${output}`)); });
    });
    await inspect(url);
  } finally {
    if (child.exitCode === null && child.signalCode === null) {
      if (process.platform === 'win32') spawnSync('taskkill', ['/PID', String(child.pid), '/T', '/F']);
      else process.kill(-child.pid, 'SIGTERM');
    }
    await exited;
  }
}

let tarball;
try {
  await mkdir(cwd);
  const packed = spawnSync(process.execPath, [npm, 'pack', '--json', '--ignore-scripts', '--cache', cache, '--pack-destination', directory], {
    cwd: packageRoot, encoding: 'utf8',
  });
  assert.equal(packed.status, 0, packed.stderr);
  tarball = join(directory, JSON.parse(packed.stdout)[0].filename);
  await writeFile(join(cwd, 'My Resume.md'), markdown);
  await checkServer(['review', '--provider', 'codex'], async url => {
    const response = await fetch(url);
    assert.equal(response.status, 200);
    assert.match(await response.text(), /Review my resume/);
    console.log('Packed npx review: upload page loaded outside the repository.');
  });
  await checkServer(['preview', 'My Resume.md'], async url => {
    const response = await fetch(url);
    assert.equal(response.status, 200);
    const html = await response.text();
    assert.match(html, /Package Test/);
    const token = html.match(/name="word-export-token" content="([^"]+)"/)?.[1];
    assert.ok(token);
    for (const format of ['word', 'pdf']) {
      const exported = await fetch(`${url}export-${format}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Origin: new URL(url).origin, 'X-Resume-Token': token },
        body: JSON.stringify({ markdown, layout: 'single-column' }),
      });
      assert.equal(exported.status, 200, `${format} export failed: ${await exported.clone().text()}`);
      const bytes = Buffer.from(await exported.arrayBuffer());
      assert.ok(bytes.length > 1000);
      assert.equal(bytes.subarray(0, format === 'pdf' ? 4 : 2).toString(), format === 'pdf' ? '%PDF' : 'PK');
    }
    console.log('Packed npx preview: local file opened; Word and PDF downloads passed.');
  });
} finally {
  await rm(directory, { recursive: true, force: true });
}
