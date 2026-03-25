#!/usr/bin/env node

"use strict";

const { execFileSync } = require("child_process");
const os = require("os");
const path = require("path");

const PLATFORMS = {
  "linux-x64": { pkg: "@iblai/cli-linux-x64", bin: "bin/iblai" },
  "linux-arm64": { pkg: "@iblai/cli-linux-arm64", bin: "bin/iblai" },
  "darwin-arm64": { pkg: "@iblai/cli-darwin-arm64", bin: "bin/iblai" },
  "win32-x64": { pkg: "@iblai/cli-win32-x64", bin: "bin/iblai.exe" },
};

function getBinaryPath() {
  const key = `${process.platform}-${os.arch()}`;
  const entry = PLATFORMS[key];

  if (!entry) {
    console.error(
      `Error: Unsupported platform ${process.platform}-${os.arch()}.`,
    );
    console.error(
      `@iblai/cli supports: ${Object.keys(PLATFORMS).join(", ")}`,
    );
    console.error(
      "\nYou can install the Python package directly instead:",
    );
    console.error("  pip install iblai-app-cli");
    process.exit(1);
  }

  try {
    const pkgDir = path.dirname(
      require.resolve(`${entry.pkg}/package.json`),
    );
    return path.join(pkgDir, entry.bin);
  } catch {
    console.error(
      `Error: Platform package ${entry.pkg} is not installed.`,
    );
    console.error(
      "\nThis usually means the optional dependency was not installed",
    );
    console.error("for your platform. Try reinstalling:");
    console.error("  npm install -g @iblai/cli");
    console.error(
      "\nOr install the Python package directly:",
    );
    console.error("  pip install iblai-app-cli");
    process.exit(1);
  }
}

const binPath = getBinaryPath();

try {
  execFileSync(binPath, process.argv.slice(2), { stdio: "inherit" });
} catch (e) {
  if (e.status !== null && e.status !== undefined) {
    process.exit(e.status);
  }
  // If execFileSync throws without a status (e.g., ENOENT), report it
  console.error(`Error: Failed to execute ${binPath}`);
  console.error(e.message);
  process.exit(1);
}
