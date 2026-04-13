#!/usr/bin/env node

import { spawnSync } from "node:child_process";
import fs from "node:fs";
import path from "node:path";
import process from "node:process";

const repoRoot = path.resolve(path.dirname(new URL(import.meta.url).pathname), "..", "..");
const distDir = path.join(repoRoot, "dist", "npm");

function fail(message) {
  process.stderr.write(`ERROR: ${message}\n`);
  process.exit(1);
}

function run(cmd, args) {
  const result = spawnSync(cmd, args, {
    cwd: repoRoot,
    encoding: "utf8",
    stdio: ["inherit", "pipe", "pipe"],
  });
  if (result.stdout) process.stdout.write(result.stdout);
  if (result.stderr) process.stderr.write(result.stderr);
  if (result.status !== 0) {
    fail(`${cmd} ${args.join(" ")} failed`);
  }
}

fs.mkdirSync(distDir, { recursive: true });

run("node", ["scripts/npm/check-package.mjs"]);
run("npm", ["pack", "--pack-destination", distDir]);

process.stdout.write(`Package tarball written to ${distDir}\n`);
