import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { mkdtemp, readFile, readdir, rm, writeFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join, resolve } from 'node:path';
import { test } from 'node:test';
import { parseArgs } from '../lib/cli.mjs';
import { cacheHome, packageRoot, withSetupLock } from '../lib/runtime.mjs';

test('review defaults and preview paths preserve argument boundaries', () => {
  assert.equal(parseArgs([]).command, 'review');
  assert.equal(parseArgs(['--provider', 'claude']).options.provider, 'claude');
  const parsed = parseArgs(['preview', '/tmp/My Resume $(example).md', '--layout', 'two-column-left', '--no-open']);
  assert.equal(parsed.resume, '/tmp/My Resume $(example).md');
  assert.equal(parsed.options.layout, 'two-column-left');
  assert.equal(parsed.options['no-open'], true);
  assert.equal(parseArgs(['setup', '--pdf']).options.pdf, true);
});

test('invalid inputs fail before any downloads or environment changes', () => {
  for (const args of [
    ['unknown'], ['preview'], ['preview', 'resume.docx'], ['review', '--provider', 'invalid'],
    ['review', '--port', '-1'], ['review', '--port', '65536'], ['review', '--port', 'abc'],
    ['review', '--provider'], ['setup', '--port', '3000'], ['preview', 'resume.md', '--layout', 'invalid'],
  ]) assert.throws(() => parseArgs(args), Error, JSON.stringify(args));
});

test('help, version, and missing files never bootstrap Python', async () => {
  const home = await mkdtemp(join(tmpdir(), 'resume-cli-test-'));
  try {
    for (const [args, expected] of [[['--help'], 0], [['--version'], 0], [['preview', join(home, 'missing.md')], 1]]) {
      const result = spawnSync(process.execPath, [join(packageRoot, 'bin/resume-writer.mjs'), ...args], {
        env: { ...process.env, RESUME_WRITER_HOME: home }, encoding: 'utf8',
      });
      assert.equal(result.status, expected, result.stderr);
    }
    assert.deepEqual(await readdir(home), []);
  } finally { await rm(home, { recursive: true, force: true }); }
});

test('cache locations are user-writable and can be overridden', () => {
  assert.equal(cacheHome({ RESUME_WRITER_HOME: '/tmp/resume-custom' }), resolve('/tmp/resume-custom'));
  assert.equal(cacheHome({ XDG_CACHE_HOME: '/tmp/xdg' }, 'linux'), join('/tmp/xdg', 'resume-writer'));
});

test('setup is serialized and failed setup releases its lock for retry', async () => {
  const home = await mkdtemp(join(tmpdir(), 'resume-lock-test-'));
  try {
    const events = [];
    await Promise.all([1, 2].map(id => withSetupLock(home, async () => {
      events.push(`start${id}`);
      await new Promise(resolve => setTimeout(resolve, 20));
      events.push(`end${id}`);
    })));
    assert.match(events.join(','), /^(start1,end1,start2,end2|start2,end2,start1,end1)$/);
    await assert.rejects(withSetupLock(home, () => { throw new Error('download failed'); }), /download failed/);
    await withSetupLock(home, () => writeFile(join(home, 'retried'), 'ok'));
    assert.equal(await readFile(join(home, 'retried'), 'utf8'), 'ok');
    assert.deepEqual(await readdir(home), ['retried']);
  } finally { await rm(home, { recursive: true, force: true }); }
});

test('npm bundle includes runtime assets and excludes personal resumes, uploads, and caches', async () => {
  const cache = await mkdtemp(join(tmpdir(), 'resume-pack-test-'));
  try {
    // npm test supplies npm_execpath, including on Windows where npm is a .cmd launcher.
    const result = spawnSync(process.execPath, [process.env.npm_execpath, 'pack', '--dry-run', '--json', '--ignore-scripts', '--cache', cache], {
      cwd: packageRoot, encoding: 'utf8',
    });
    assert.equal(result.status, 0, result.stderr);
    const files = JSON.parse(result.stdout)[0].files.map(file => file.path);
    for (const path of [
      'bin/resume-writer.mjs', 'lib/runtime.mjs', 'requirements.txt',
      '.github/skills/resume-review/scripts/review_app.py',
      '.github/skills/resume-review/templates/review-start.html',
      '.github/skills/resume-review/references/review-rubric.md',
      '.github/skills/resume-writing/scripts/serve_resume.py',
      '.github/skills/resume-writing/scripts/to_docx_editorial.py',
      '.github/skills/resume-writing/scripts/to_pdf_editorial.py',
      '.github/skills/resume-writing/templates/editorial-right.html',
    ]) assert.ok(files.includes(path), `Missing ${path}`);
    for (const file of files) {
      assert.doesNotMatch(file, /Jennifer|^output\/|\.docx$|\.venv|__pycache__|^test\/|test_.*\.py$|\.npmrc/);
    }
  } finally { await rm(cache, { recursive: true, force: true }); }
});
