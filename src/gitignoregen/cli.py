"""
Auto-generate .gitignore based on detected project type.

Usage:
    gitignoregen
    gitignoregen --type python
    gitignoregen --type java --type python
    gitignoregen --extra terraform,docker
    gitignoregen --dry-run
"""

from __future__ import annotations

import os
import signal
import sys
from pathlib import Path

import click
import httpx

GITIGNORE_API = "https://www.toptal.com/developers/gitignore/api"

# Always included: VSCode, JetBrains (IntelliJ etc.), macOS, Windows, Linux
DEFAULTS = ["visualstudiocode", "jetbrains+all", "macos", "windows", "linux"]

# Project type → detection markers + gitignore.io template names
PROJECT_TYPES: dict[str, dict] = {
    "java": {
        "markers": ["pom.xml", "build.gradle", "build.gradle.kts"],
        "globs": ["*.java"],
        "templates": ["java", "maven", "gradle"],
    },
    "python": {
        "markers": ["pyproject.toml", "requirements.txt", "setup.py", "setup.cfg", "Pipfile", "tox.ini"],
        "globs": ["*.py"],
        "templates": ["python", "jupyternotebooks", "virtualenv"],
    },
    "node": {
        "markers": ["package.json", "yarn.lock", "pnpm-lock.yaml", ".nvmrc", ".node-version"],
        "globs": ["*.ts", "*.tsx", "*.mjs"],
        "templates": ["node"],
    },
    "dotnet": {
        "markers": [],
        "globs": ["*.csproj", "*.sln", "*.fsproj", "*.vbproj"],
        "templates": ["dotnetcore", "visualstudio"],
    },
}


def detect_project_types(directory: Path) -> list[str]:
    """Detect project types by scanning for marker files and extensions."""
    detected: list[str] = []

    if not directory.exists():
        return detected

    filenames = {entry.name for entry in directory.iterdir()}
    extensions = {entry.suffix for entry in directory.iterdir() if entry.is_file()}

    for ptype, cfg in PROJECT_TYPES.items():
        # Check for known marker files (pom.xml, package.json, etc.)
        if any(m in filenames for m in cfg["markers"]):
            detected.append(ptype)
            continue
        # Check for file-extension globs (*.java, *.csproj, etc.)
        if any(g.replace("*", "") in extensions for g in cfg["globs"]):
            detected.append(ptype)

    return detected


def fetch_gitignore(templates: list[str]) -> str:
    """Fetch .gitignore content from gitignore.io (Toptal) API."""
    url = f"{GITIGNORE_API}/{','.join(templates)}"
    resp = httpx.get(url, follow_redirects=True, timeout=15)
    resp.raise_for_status()
    return resp.text


def dedupe(items: list[str]) -> list[str]:
    """Deduplicate while preserving order."""
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        key = item.lower()
        if key not in seen:
            seen.add(key)
            result.append(item)
    return result


def _use_emoji() -> bool:
    """Return True if emoji should be used (TTY and NO_COLOR not set)."""
    return sys.stderr.isatty() and not os.environ.get("NO_COLOR")


def _icon(emoji: str, fallback: str) -> str:
    return emoji if _use_emoji() else fallback


def _sigint_handler(sig: int, frame: object) -> None:
    click.echo("\nInterrupted.", err=True)
    sys.exit(130)


@click.command(context_settings={"help_option_names": ["-h", "--help"]})
@click.version_option(package_name="gitignoregen")
@click.option(
    "--type",
    "-t",
    "project_types",
    multiple=True,
    type=click.Choice(list(PROJECT_TYPES.keys()), case_sensitive=False),
    help="Project type(s). Auto-detected if omitted.",
)
@click.option(
    "--extra",
    "-e",
    default="",
    help="Comma-separated extra gitignore.io templates (e.g. terraform,docker).",
)
@click.option("--output", "-o", default=".gitignore", help="Output file (default: .gitignore).")
@click.option("--dry-run", "-n", is_flag=True, help="Print to stdout; don't write file.")
@click.option("--dir", "-d", "directory", default=".", help="Directory to scan (default: cwd).")
def main(
    project_types: tuple[str, ...],
    extra: str,
    output: str,
    dry_run: bool,
    directory: str,
) -> None:
    """Auto-generate .gitignore for your project.

    Detects Java, Python, Node.js, and .NET projects, then pulls
    matching templates from gitignore.io.  VSCode, JetBrains IDEs,
    and OS files (.DS_Store, Thumbs.db, etc.) are always included.

    \b
    Examples
    --------
      gitignoregen              # auto-detect & generate
      gitignoregen -t python    # force Python templates
      gitignoregen -e docker -n # add Docker, dry-run
    """
    signal.signal(signal.SIGINT, _sigint_handler)

    target = Path(directory).resolve()

    # --- Resolve project types -------------------------------------------
    if project_types:
        types = list(project_types)
        click.echo(f"{_icon('📌', '[*]')} Using specified type(s): {', '.join(types)}", err=True)
    else:
        types = detect_project_types(target)
        if types:
            click.echo(f"{_icon('🔍', '[i]')} Detected: {', '.join(types)}", err=True)
        else:
            click.echo(f"{_icon('⚠️', '[!]')}  No project type detected — using defaults only.", err=True)

    # --- Build template list ---------------------------------------------
    templates: list[str] = list(DEFAULTS)
    for t in types:
        templates.extend(PROJECT_TYPES[t]["templates"])
    if extra:
        templates.extend(x.strip() for x in extra.split(",") if x.strip())
    templates = dedupe(templates)

    click.echo(f"{_icon('📦', '[+]')} Templates: {', '.join(templates)}", err=True)

    # --- Fetch -----------------------------------------------------------
    try:
        content = fetch_gitignore(templates)
    except httpx.HTTPError as exc:
        click.echo(f"{_icon('❌', '[E]')} gitignore.io request failed: {exc}", err=True)
        click.echo("Check your network connection or try again with --dry-run.", err=True)
        sys.exit(1)

    # --- Output ----------------------------------------------------------
    if dry_run:
        click.echo(content)
        return

    out_path = target / output

    append = out_path.exists()
    if append:
        click.echo(f"{_icon('📎', '[i]')} {output} exists — appending.", err=True)

    mode = "a" if append else "w"
    with open(out_path, mode) as fh:
        if append:
            fh.write("\n\n# --- Auto-generated additions ---\n")
        fh.write(content)
        fh.write("\n")

    verb = "Appended to" if append else "Generated"
    click.echo(f"{_icon('✅', '[ok]')} {verb} {out_path}", err=True)
    click.echo(f"Next: git add {output}", err=True)


if __name__ == "__main__":
    main()
