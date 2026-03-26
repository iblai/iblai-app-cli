# Build Dependencies — Windows

## Quick install

```powershell
# 1. Install Python from https://www.python.org/downloads/
#    Check "Add Python to PATH" during installation

# 2. Install Rust
winget install Rustlang.Rustup
# or download from https://rustup.rs

# 3. Install Visual Studio Build Tools
winget install Microsoft.VisualStudio.2022.BuildTools
# Select "Desktop development with C++" workload

# 4. Install Node.js
winget install OpenJS.NodeJS.LTS
npm install -g pnpm
```

## CLI binary build (PyInstaller)

| Requirement | How to install |
|-------------|---------------|
| Python 3.11+ | [python.org](https://www.python.org/downloads/) or `winget install Python.Python.3.12` |
| pip | Included with Python |

After installing Python:

```powershell
python --version
pip --version
```

Build the binary:

```powershell
pwsh scripts/build-binary.ps1
```

## Generated app Tauri build

| Requirement | How to install |
|-------------|---------------|
| Rust toolchain | [rustup.rs](https://rustup.rs) or `winget install Rustlang.Rustup` |
| Visual Studio Build Tools | [visualstudio.com](https://visualstudio.microsoft.com/visual-cpp-build-tools/) — select "Desktop development with C++" |
| WebView2 Runtime | Pre-installed on Windows 10 (1803+) and Windows 11 |

```powershell
rustup default stable
rustc --version
cargo --version
```

## Node.js (for generated apps)

```powershell
winget install OpenJS.NodeJS.LTS
npm install -g pnpm
```

## Verification

```powershell
python --version      # 3.11+
rustc --version       # 1.70+
cargo --version
node --version        # 20+
pnpm --version
```
