# Build Dependencies — Arch Linux

## Quick install

```bash
# CLI binary build (PyInstaller)
sudo pacman -S python python-pip

# Generated app Tauri build
sudo pacman -S rust webkit2gtk-4.1 base-devel openssl
```

## CLI binary build (PyInstaller)

These are needed to run `make binary` or `scripts/build-binary.sh`.

| Package | Purpose |
|---------|---------|
| `python` | Python 3.11+ runtime |
| `python-pip` | pip package manager |

```bash
sudo pacman -S python python-pip
```

## Generated app Tauri build

These are needed to run `iblai builds build` on a generated app.

| Package | Purpose |
|---------|---------|
| `rust` | Rust toolchain (rustc + cargo) |
| `webkit2gtk-4.1` | WebView2 library for Tauri |
| `base-devel` | Build essentials (gcc, make, etc.) |
| `openssl` | TLS support |

```bash
sudo pacman -S rust webkit2gtk-4.1 base-devel openssl
```

## Node.js (for generated apps)

```bash
sudo pacman -S nodejs-lts-iron pnpm
# or via nvm:
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash
nvm install 20
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
