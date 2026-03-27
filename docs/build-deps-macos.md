# Build Dependencies — macOS

## Quick install

```bash
# Xcode command line tools (required for compilation)
xcode-select --install

# Rust
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh

# Python (if not using system Python)
brew install python@3.11

# Node.js
brew install node pnpm
```

## CLI binary build (PyInstaller)

| Requirement | How to install |
|-------------|---------------|
| Python 3.11+ | `brew install python@3.11` or [python.org](https://www.python.org/downloads/) |
| Xcode CLI tools | `xcode-select --install` |

macOS ships with Python 3 on recent versions, but Homebrew's version is recommended for development.

```bash
python3 --version
pip3 --version
```

Build the binary:

```bash
./scripts/build-binary.sh
```

## Generated app Tauri build (desktop)

| Requirement | How to install |
|-------------|---------------|
| Xcode CLI tools | `xcode-select --install` |
| Rust toolchain | [rustup.rs](https://rustup.rs) |

macOS does not require additional WebView libraries — Tauri uses the system WebView (WKWebView) which ships with macOS.

```bash
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
source "$HOME/.cargo/env"
```

## Generated app Tauri build (iOS)

For iOS builds, you need the full Xcode (not just CLI tools):

| Requirement | How to install |
|-------------|---------------|
| Xcode (full) | Mac App Store |
| iOS Simulator | Included with Xcode |
| Rust iOS targets | `rustup target add aarch64-apple-ios aarch64-apple-ios-sim` |

```bash
# Install iOS Rust targets
rustup target add aarch64-apple-ios aarch64-apple-ios-sim

# Initialize iOS project
iblai builds ios init

# Run in simulator
iblai builds ios dev
```

## Node.js (for generated apps)

```bash
brew install node pnpm
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
xcodebuild -version   # for iOS builds
```
