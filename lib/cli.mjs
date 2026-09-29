import { readFile, stat } from 'node:fs/promises';
import { resolve, join } from 'node:path';
import { ensureRuntime, packageRoot, run } from './runtime.mjs';

const help = `Resume Writer & Review

Usage:
  resume-writer                              Open Resume Review
  resume-writer review [options]             Review a .md, .docx, or searchable .pdf upload
  resume-writer preview <resume.md> [options] Edit a resume and export Word/PDF
  resume-writer setup [--pdf]                Prepare dependencies without opening the app

Options:
  --provider codex|claude|cursor|copilot      AI tool for review (otherwise auto-detect)
  --layout <name>                            Preview layout (default: single-column)
  --port <number>                            Local server port (default: automatic)
  --no-open                                  Print the URL without opening a browser
  --help                                    Show this help
  --version                                 Show the package version

Python and dependencies are downloaded to a private cache on first use.
Preview also installs Chromium for PDF export. No administrator access is needed
on macOS or Windows; Linux may require Chromium system libraries.
Review requires an installed, signed-in AI CLI. Press Ctrl+C to stop the server.
Set RESUME_WRITER_HOME to choose a different runtime cache directory.
`;

export function parseArgs(input) {
  const args = [...input];
  if (args.includes('--help') || args.includes('-h')) return { command: 'help' };
  if (args.length === 1 && args[0] === '--version') return { command: 'version' };
  const command = args[0] && !args[0].startsWith('-') ? args.shift() : 'review';
  if (!['review', 'preview', 'setup'].includes(command)) {
    throw new Error(`Unknown command "${command}". Run resume-writer --help.`);
  }
  let resume;
  if (command === 'preview') {
    resume = args.shift();
    if (!resume || resume.startsWith('-') || !resume.toLowerCase().endsWith('.md')) {
      throw new Error('Use resume-writer preview <resume.md>.');
    }
  }
  const options = {};
  const values = command === 'review' ? ['provider', 'port'] : command === 'preview' ? ['layout', 'port'] : [];
  const flags = command === 'setup' ? ['pdf'] : ['no-open', 'open'];
  while (args.length) {
    const flag = args.shift();
    const key = flag.slice(2);
    if (!flag.startsWith('--') || (!values.includes(key) && !flags.includes(key))) {
      throw new Error(`Unknown option "${flag}" for ${command}. Run resume-writer --help.`);
    }
    if (flags.includes(key)) options[key] = true;
    else {
      const value = args.shift();
      if (!value || value.startsWith('--')) throw new Error(`${flag} needs a value.`);
      options[key] = value;
    }
  }
  if (options.provider && !['auto', 'codex', 'claude', 'cursor', 'copilot'].includes(options.provider)) {
    throw new Error('Choose provider codex, claude, cursor, or copilot.');
  }
  if (options.layout && !['single-column', 'two-column-left', 'two-column-right', 'two-column-right-refined', 'editorial-html'].includes(options.layout)) {
    throw new Error(`Unknown layout "${options.layout}".`);
  }
  if (options.port !== undefined && (!/^\d+$/.test(options.port) || Number(options.port) > 65535)) {
    throw new Error('Port must be a number from 0 to 65535.');
  }
  return { command, resume, options };
}

export async function main(input = process.argv.slice(2)) {
  const { command, resume, options } = parseArgs(input);
  if (command === 'help') return console.log(help);
  if (command === 'version') {
    return console.log(JSON.parse(await readFile(join(packageRoot, 'package.json'), 'utf8')).version);
  }
  if (resume && !(await stat(resolve(resume)).catch(() => null))?.isFile()) {
    throw new Error(`Resume file not found: ${resume}`);
  }
  const { python, env } = await ensureRuntime({ pdf: command === 'preview' || options.pdf });
  if (command === 'setup') return console.log('Resume Writer is ready.');
  const scripts = join(packageRoot, '.github', 'skills');
  const args = command === 'review'
    ? [join(scripts, 'resume-review', 'scripts', 'render_review.py')]
    : [join(scripts, 'resume-writing', 'scripts', 'serve_resume.py'), resolve(resume), '--layout', options.layout || 'single-column'];
  if (options.provider) args.push('--provider', options.provider);
  if (options.port !== undefined) args.push('--port', options.port);
  if (!options['no-open']) args.push('--open');
  // Keep the caller's directory: uploads and generated previews belong beside their work.
  await run(python, args, { env });
}
