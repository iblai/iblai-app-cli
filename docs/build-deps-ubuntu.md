# Build Dependencies — Ubuntu / Debian

## Quick install

```bash
# CLI binary build (PyInstaller)
sudo apt update
sudo apt install python3 python3-pip python3-venv

# Generated app Tauri build
sudo apt install libwebkit2gtk-4.1-dev libappindicator3-dev \
  librsvg2-dev patchelf build-essential libssl-dev
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
```

## CLI binary build (PyInstaller)

| Package | Purpose |
|---------|---------|
| `python3` | Python 3.11+ runtime |
| `python3-pip` | pip package manager |
| `python3-venv` | Virtual environment support |

```bash
sudo apt install python3 python3-pip python3-venv
```

## Generated app Tauri build

| Package | Purpose |
|---------|---------|
| `libwebkit2gtk-4.1-dev` | WebView2 development library for Tauri |
| `libappindicator3-dev` | System tray / app indicator support |
| `librsvg2-dev` | SVG rendering (for icons) |
| `patchelf` | ELF binary patching (for AppImage) |
| `build-essential` | gcc, g++, make |
| `libssl-dev` | TLS development headers |

```bash
sudo apt install libwebkit2gtk-4.1-dev libappindicator3-dev \
  librsvg2-dev patchelf build-essential libssl-dev
```

Install Rust via rustup (Ubuntu's `rustc` package is often outdated):

```bash
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
source "$HOME/.cargo/env"
```

## Node.js (for generated apps)

```bash
# via NodeSource
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install nodejs
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
