from pathlib import Path
import subprocess
import sys

UI_FILES = [
    "f60_ui_shell.html",
    "f62_ui_app.js",
    "f63_ui_api.js",
    "f64_ui_components.js",
    "f65_ui_theme.js",
    "f67_ui_artifacts.js",
    "f68_ui_pets.js",
    "f69_ui_motion.js",
]

CHAR_REPLACEMENTS = {
    "\u201c": '"',   # left double smart quote
    "\u201d": '"',   # right double smart quote
    "\u2018": "'",   # left single smart quote
    "\u2019": "'",   # right single smart quote
    "\u00a0": " ",   # non-breaking space
}

TEXT_REPLACEMENTS = {
    # Common breakages from copy/paste or markdown pollution
    "replaceAll(\"&\", \"&\")": 'replaceAll("&", "&amp;")',
    'replaceAll("<", "<")': 'replaceAll("<", "&lt;")',
    'replaceAll(">", ">")': 'replaceAll(">", "&gt;")',
    'replaceAll(\'"\', \'"\')': 'replaceAll(\'"\', "&quot;")',

    # Repair broken regex/code-fence handlers if they were mangled
    '/`([a-zA-Z0-9_-]+)?\\n([\\s\\S]*?)`/g': r'/```([a-zA-Z0-9_-]+)?\n([\s\S]*?)```/g',
    '.replace(g, "<strong>$1</strong>")': r'.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")',

    # Minor text cleanup
    "level ${pet.level} . ${pet.xp} xp": "level ${pet.level} · ${pet.xp} xp",
}

CSS_ALIAS_SNIPPET = """
  --text-2: var(--t2);
  --text-3: var(--t3);
  --f-mono: var(--f-m);
  --f-display: var(--f-d);
""".strip("\n")


def clean_text(file_name: str, text: str) -> str:
    for bad, good in CHAR_REPLACEMENTS.items():
        text = text.replace(bad, good)

    for bad, good in TEXT_REPLACEMENTS.items():
        text = text.replace(bad, good)

    if file_name == "f60_ui_shell.html":
        lines = [line for line in text.splitlines() if line.strip() != "```"]
        text = "\n".join(lines).rstrip() + "\n"

    if file_name == "f61_ui_styles.css":
        if "--text-2:" not in text and ":root" in text:
            text = text.replace(
                ":root {",
                ":root {\n" + CSS_ALIAS_SNIPPET + "\n",
                1,
            )

    return text


def backup_and_write(path: Path, content: str) -> None:
    backup = path.with_suffix(path.suffix + ".bak")
    if not backup.exists():
        backup.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
    path.write_text(content, encoding="utf-8")


def check_js(file_name: str) -> bool:
    result = subprocess.run(
        ["node", "--check", file_name],
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        print(f"[ok] {file_name}")
        return True

    print(f"[fail] {file_name}")
    if result.stderr.strip():
        print(result.stderr.strip())
    return False


def main() -> int:
    changed = []

    for file_name in UI_FILES:
        path = Path(file_name)
        if not path.exists():
            print(f"[skip] missing: {file_name}")
            continue

        original = path.read_text(encoding="utf-8")
        cleaned = clean_text(file_name, original)

        if cleaned != original:
            backup_and_write(path, cleaned)
            changed.append(file_name)
            print(f"[fixed] {file_name}")
        else:
            print(f"[clean] {file_name}")

    print("\nValidating JS...\n")
    js_files = [f for f in UI_FILES if f.endswith(".js")]
    all_ok = all(check_js(f) for f in js_files if Path(f).exists())

    print("\nDone.")
    if changed:
        print("Changed files:")
        for name in changed:
            print(f" - {name}")
    else:
        print("No file changes were needed.")

    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())