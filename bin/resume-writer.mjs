#!/usr/bin/env node
import { main } from '../lib/cli.mjs';

main().catch(error => {
  console.error(`Resume Writer: ${error.message}`);
  process.exitCode = 1;
});
