from pathlib import Path
import re

ROOT = Path(".")

NEW_VERSION = "303"

FILES = {
    "shell": ROOT / "f60_ui_shell.html",
    "components": ROOT / "f64_ui_components.js",
    "artifacts": ROOT / "f67_ui_artifacts.js",
    "replit": ROOT / ".replit",
}

PREVIEW_TEXT_REPLACEMENT = """function previewText(value, max = 220) {
  if (value == null) return "";

  let text = typeof value === "string" ? value : JSON.stringify(value, null, 2);

  text = text.replace(/```[\\s\\S]*?```/g, "[code block]");
  text = text.replace(/^#{1,6}\\s+/gm, "");
  text = text.replace(/\\*\\*(.+?)\\*\\*/g, "$1");
  text = text.replace(/\\*(.+?)\\*/g, "$1");
  text = text.replace(/`([^`]+)`/g, "$1");
  text = text.replace(/^\\s*[-*]\\s+/gm, "");
  text = text.replace(/\\|/g, " ");
  text = text.replace(/\\s+/g, " ").trim();

  return text.length <= max ? text : `${text.slice(0, max - 3)}...`;
}"""


def backup(path: Path):
    if not path.exists():
        return
    bak = path.with_suffix(path.suffix + ".bak")
    if not bak.exists():
        bak.write_text(path.read_text(encoding="utf-8", errors="replace"), encoding="utf-8")


def write(path: Path, text: str):
    backup(path)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def replace_preview_text_function(js: str) -> str:
    marker = "function previewText(value, max = 220) {"
    start = js.find(marker)
    if start == -1:
        print("[warn] previewText() not found")
        return js

    i = start
    brace_depth = 0
    end = None

    while i < len(js):
        ch = js[i]
        if ch == "{":
            brace_depth += 1
        elif ch == "}":
            brace_depth -= 1
            if brace_depth == 0:
                end = i + 1
                break
        i += 1

    if end is None:
        print("[warn] previewText() end not found")
        return js

    return js[:start] + PREVIEW_TEXT_REPLACEMENT + js[end:]


def harden_components():
    path = FILES["components"]
    if not path.exists():
        print("[missing] f64_ui_components.js")
        return

    text = path.read_text(encoding="utf-8", errors="replace")

    text = text.replace('class="ghost-btn sm"', 'class="btn-ghost sm"')
    text = text.replace("class='ghost-btn sm'", "class='btn-ghost sm'")
    text = replace_preview_text_function(text)

    write(path, text)
    print("[patched] f64_ui_components.js")


def harden_artifacts():
    path = FILES["artifacts"]
    if not path.exists():
        print("[missing] f67_ui_artifacts.js")
        return

    text = path.read_text(encoding="utf-8", errors="replace")
    text = text.replace('class="ghost-btn sm"', 'class="btn-ghost sm"')
    text = text.replace("class='ghost-btn sm'", "class='btn-ghost sm'")

    write(path, text)
    print("[patched] f67_ui_artifacts.js")


def bump_shell_versions(text: str) -> str:
    text = "\n".join(line for line in text.splitlines() if line.strip() != "```")

    text = re.sub(
        r'href="/f61_ui_styles\.css\?v=\d+"',
        f'href="/f61_ui_styles.css?v={NEW_VERSION}"',
        text,
    )

    imports_to_bump = [
        "f63_ui_api.js",
        "f64_ui_components.js",
        "f65_ui_theme.js",
        "f66_ui_workbench.js",
        "f67_ui_artifacts.js",
        "f68_ui_pets.js",
        "f69_ui_motion.js",
    ]

    for name in imports_to_bump:
        old_plain = f'"/{name}": "/{name}"'
        old_versioned_pattern = rf'"/{re.escape(name)}"\s*:\s*"/{re.escape(name)}\?v=\d+"'
        new_value = f'"/{name}": "/{name}?v={NEW_VERSION}"'

        if old_plain in text:
            text = text.replace(old_plain, new_value)
        else:
            text = re.sub(old_versioned_pattern, new_value, text)

    if 'src="/f62_ui_app.js"' in text:
        text = text.replace(
            'src="/f62_ui_app.js"',
            f'src="/f62_ui_app.js?v={NEW_VERSION}"'
        )
    else:
        text = re.sub(
            r'src="/f62_ui_app\.js\?v=\d+"',
            f'src="/f62_ui_app.js?v={NEW_VERSION}"',
            text,
        )

    return text


def harden_shell():
    path = FILES["shell"]
    if not path.exists():
        print("[missing] f60_ui_shell.html")
        return

    text = path.read_text(encoding="utf-8", errors="replace")
    text = bump_shell_versions(text)

    write(path, text)
    print("[patched] f60_ui_shell.html")


def harden_replit():
    path = FILES["replit"]
    if not path.exists():
        print("[missing] .replit")
        return

    text = path.read_text(encoding="utf-8", errors="replace")

    if "[[ports]]" not in text:
        text += "\n[[ports]]\nlocalPort = 8000\nexternalPort = 80\n"
    elif "externalPort" not in text:
        text = re.sub(
            r"(\[\[ports\]\]\s*[\r\n]+localPort\s*=\s*8000\s*)",
            r"\1externalPort = 80\n",
            text,
            count=1,
        )

    write(path, text)
    print("[patched] .replit")


def remove_accidental_space_file():
    candidates = [
        ROOT / " f22_store_tasks.py",
        ROOT / " f22_store_tasks.py ",
    ]

    removed = False
    for path in candidates:
        if path.exists():
            bak = path.with_suffix(path.suffix + ".bak")
            if not bak.exists():
                bak.write_text(path.read_text(encoding="utf-8", errors="replace"), encoding="utf-8")
            path.unlink()
            removed = True
            print(f"[removed] accidental file: {path.name}")

    if not removed:
        print("[ok] no accidental spaced f22_store_tasks.py file found")


def main():
    harden_shell()
    harden_components()
    harden_artifacts()
    harden_replit()
    remove_accidental_space_file()

    print("\\nDone.")
    print("Next steps:")
    print("1. Stop the running app")
    print("2. Run: python final_hardening_pass_v2.py")
    print("3. Run: python app.py")
    print("4. Hard refresh Preview")
    print("5. Reopen the app on mobile if needed")


if __name__ == "__main__":
    main()