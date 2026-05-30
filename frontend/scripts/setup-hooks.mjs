#!/usr/bin/env node
// Enable the repo's git hooks on `pnpm install` (runs via the `prepare` script).
//
// Best-effort and silent on failure: skips when there's no git repo or no git
// binary — e.g. inside the frontend Docker build, which runs `pnpm install`
// after copying only package.json (no .git, no git installed). This must never
// break an install, so every git call is guarded.
import { execSync } from 'node:child_process';

try {
  // Throws if git is missing or we're not inside a work tree (Docker build).
  execSync('git rev-parse --is-inside-work-tree', { stdio: 'ignore' });
} catch {
  process.exit(0);
}

try {
  execSync('git config core.hooksPath scripts/git-hooks', { stdio: 'ignore' });
  console.log('✔ git hooks enabled (core.hooksPath=scripts/git-hooks)');
} catch {
  // Non-fatal: leave hooks unconfigured rather than failing the install.
}
