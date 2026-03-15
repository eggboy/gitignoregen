# gitignoregen

Auto-generate `.gitignore` based on detected project type.

Scans your project directory for marker files (e.g. `pom.xml`, `pyproject.toml`, `package.json`), detects the project type, and pulls matching templates from [gitignore.io](https://www.toptal.com/developers/gitignore). Editor (VSCode, JetBrains) and OS files are always included.

## Always Included

Every generated `.gitignore` includes templates for:

- **Editors** — VS Code, JetBrains (IntelliJ, PyCharm, WebStorm, etc.)
- **OS files** — macOS (`.DS_Store`), Windows (`Thumbs.db`), Linux

## Supported Project Types

| Type | Detected By | Templates |
|------|-------------|-----------|
| Java | `pom.xml`, `build.gradle`, `*.java` | Java, Maven, Gradle |
| Python | `pyproject.toml`, `requirements.txt`, `setup.py`, `*.py` | Python, Jupyter Notebooks, virtualenv |
| Node.js | `package.json`, `yarn.lock`, `*.ts` | Node |
| .NET | `*.csproj`, `*.sln`, `*.fsproj` | .NET Core, Visual Studio |

## Installation

Requires Python 3.11+.

```bash
uv tool install gitignoregen
```

This installs `gitignoregen` as a standalone CLI available globally, independent of any project virtual environment.

To install from a local checkout:

```bash
uv tool install --editable .
```

To upgrade:

```bash
uv tool upgrade gitignoregen
```

To uninstall:

```bash
uv tool uninstall gitignoregen
```

## Usage

```bash
# Auto-detect project type and generate .gitignore
gitignoregen

# Specify project type explicitly
gitignoregen -t python
gitignoregen -t java -t python

# Add extra gitignore.io templates (e.g. terraform, docker)
gitignoregen -e terraform,docker

# Preview without writing (prints to stdout)
gitignoregen --dry-run

# Append to an existing .gitignore instead of overwriting
gitignoregen --append

# Overwrite without confirmation
gitignoregen -y

# Scan a different directory
gitignoregen -d ../other-project
```

## Options

```
-t, --type TEXT     Project type(s): java, python, node, dotnet. Auto-detected if omitted.
-e, --extra TEXT    Comma-separated extra gitignore.io templates (e.g. terraform,docker).
-o, --output FILE   Output file (default: .gitignore).
-a, --append        Append instead of overwrite.
-n, --dry-run       Print to stdout; don't write file.
-y, --yes           Overwrite without confirmation.
-d, --dir DIR       Directory to scan (default: cwd).
    --version       Show version.
-h, --help          Show help.
```