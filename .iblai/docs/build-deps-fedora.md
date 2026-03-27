# Build Dependencies — Fedora / RHEL

## Quick install

```bash
# CLI binary build (PyInstaller)
sudo dnf install python3 python3-pip

# Generated app Tauri build
sudo dnf install rust cargo webkit2gtk4.1-devel openssl-devel gcc-c++
```

## CLI binary build (PyInstaller)

| Package | Purpose |
|---------|---------|
| `python3` | Python 3.11+ runtime |
| `python3-pip` | pip package manager |

```bash
sudo dnf install python3 python3-pip
```

## Generated app Tauri build

| Package | Purpose |
|---------|---------|
| `rust` / `cargo` | Rust toolchain |
| `webkit2gtk4.1-devel` | WebView2 development library for Tauri |
| `openssl-devel` | TLS development headers |
| `gcc-c++` | C++ compiler |

```bash
sudo dnf install rust cargo webkit2gtk4.1-devel openssl-devel gcc-c++
```

On RHEL 8/9, enable EPEL first:

```bash
sudo dnf install epel-release
```

Alternatively, install Rust via rustup (recommended for latest version):

```bash
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
```

## Node.js (for generated apps)

```bash
sudo dnf install nodejs
npm install -g pnpm
```

## Verification

```bash
python3 --version     # 3.11+
rustc --version       # 1.70+
cargo --version
node --version        # 20+
pnpm --version
```
