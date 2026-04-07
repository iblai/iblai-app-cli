/**
 * Prepare dev-fe for Android: detect host IP, write redirect HTML to ../out/,
 * and add the host IP to allowedDevOrigins in next.config.ts.
 *
 * Usage: node src-tauri/dev-fe/setup-android.js
 */
const fs = require("fs");
const http = require("http");
const os = require("os");
const path = require("path");

function getHostIP() {
  return new Promise((resolve) => {
    // Make an outbound connection to determine the real source IP.
    // No data is sent — we just inspect the local address the OS chose.
    const req = http.get("http://clients3.google.com/generate_204", (res) => {
      res.resume();
      const addr = req.socket?.localAddress;
      req.destroy();
      resolve(addr && addr !== "::1" && addr !== "127.0.0.1" ? addr : fallbackIP());
    });
    req.on("error", () => resolve(fallbackIP()));
    req.setTimeout(3000, () => {
      req.destroy();
      resolve(fallbackIP());
    });
  });
}

function fallbackIP() {
  const interfaces = os.networkInterfaces();
  for (const name of Object.keys(interfaces)) {
    for (const iface of interfaces[name]) {
      if (iface.family === "IPv4" && !iface.internal) {
        return iface.address;
      }
    }
  }
  return "localhost";
}

(async () => {
  const hostIP = await getHostIP();
  const devUrl = `http://${hostIP}:3000`;

  // 1. Recreate out/ with redirect HTML pointing at host IP
  const devFe = path.join(__dirname, "index.html");
  const outDir = path.join(__dirname, "..", "..", "out");
  fs.rmSync(outDir, { recursive: true, force: true });
  fs.mkdirSync(outDir, { recursive: true });

  let html = fs.readFileSync(devFe, "utf-8");
  html = html.replace("http://localhost:3000", devUrl);
  fs.writeFileSync(path.join(outDir, "index.html"), html);

  // 2. Ensure host IP is in allowedDevOrigins in next.config.ts
  const configPath = path.join(__dirname, "..", "..", "next.config.ts");
  if (fs.existsSync(configPath)) {
    let config = fs.readFileSync(configPath, "utf-8");
    const origin = `"${hostIP}"`;
    // Remove any previously injected IP (from a prior run with a different IP)
    config = config.replace(
      /allowedDevOrigins:\s*\[([^\]]*)\]/,
      (match, inner) => {
        // Strip IPs we previously added (bare IPv4 strings)
        const cleaned = inner
          .split(",")
          .map((s) => s.trim())
          .filter((s) => s && !/^"\d+\.\d+\.\d+\.\d+"$/.test(s))
          .join(", ");
        return `allowedDevOrigins: [${cleaned}]`;
      }
    );
    // Add current host IP
    config = config.replace(
      /allowedDevOrigins:\s*\[/,
      `allowedDevOrigins: [${origin}, `
    );
    fs.writeFileSync(configPath, config);
  }

  console.log(`[ibl.ai] Android dev: host IP = ${hostIP}, redirect URL = ${devUrl}`);
})();
