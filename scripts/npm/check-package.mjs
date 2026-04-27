#!/usr/bin/env node

import { spawnSync } from "node:child_process";
import fs from "node:fs";
import path from "node:path";
import process from "node:process";

const repoRoot = path.resolve(path.dirname(new URL(import.meta.url).pathname), "..", "..");

function fail(message) {
  process.stderr.write(`ERROR: ${message}\n`);
  process.exit(1);
}

function run(cmd, args, options = {}) {
  const result = spawnSync(cmd, args, {
    cwd: repoRoot,
    encoding: "utf8",
    stdio: ["inherit", "pipe", "pipe"],
    ...options,
  });
  if (result.stdout) process.stdout.write(result.stdout);
  if (result.stderr) process.stderr.write(result.stderr);
  if (result.status !== 0) {
    fail(`${cmd} ${args.join(" ")} failed`);
  }
}

for (const relPath of [
  "package.json",
  "bin/dev-assets.js",
  "lib/ui-server.js",
  "lib/ui-app.html",
  "lib/assets/tidy_review.html",
  "lib/dev_asset_common.py",
  "lib/dev_asset_context.py",
  "lib/dev_asset_capture.py",
  "lib/dev_asset_setup.py",
  "lib/dev_asset_graduate.py",
  "lib/dev_asset_tidy.py",
  "hooks/hooks.json",
  "hooks/codex-hooks.json",
  "suite-manifest.json",
  "scripts/hooks/session_start.py",
  "scripts/hooks/pre_compact.py",
  "scripts/hooks/stop.py",
  "scripts/hooks/session_end.py",
]) {
  if (!fs.existsSync(path.join(repoRoot, relPath))) {
    fail(`missing required file: ${relPath}`);
  }
}

run("node", ["--check", "bin/dev-assets.js"]);
run("node", ["--check", "lib/ui-server.js"]);
run("python3", [
  "-m",
  "py_compile",
  "lib/dev_asset_common.py",
  "lib/dev_asset_context.py",
  "lib/dev_asset_capture.py",
  "lib/dev_asset_setup.py",
  "lib/dev_asset_graduate.py",
  "lib/dev_asset_tidy.py",
  "scripts/hooks/_common.py",
  "scripts/hooks/session_start.py",
  "scripts/hooks/pre_compact.py",
  "scripts/hooks/stop.py",
  "scripts/hooks/session_end.py",
]);

JSON.parse(fs.readFileSync(path.join(repoRoot, "hooks/hooks.json"), "utf8"));
JSON.parse(fs.readFileSync(path.join(repoRoot, "hooks/codex-hooks.json"), "utf8"));
JSON.parse(fs.readFileSync(path.join(repoRoot, "suite-manifest.json"), "utf8"));

process.stdout.write("Package checks passed.\n");
