from pathlib import Path
import re

ROOT = Path(".")

FILES = {
    "shell": ROOT / "f60_ui_shell.html",
    "components": ROOT / "f64_ui_components.js",
    "artifacts": ROOT / "f67_ui_artifacts.js",
    "replit": ROOT / ".replit",
}

NEW_VERSION = "302"


def backup(path: Path):
    if not path.exists():
        return
    bak = path.with_suffix(path.suffix + ".bak")
    if not bak.exists():
        bak.write_text(path.read_text(encoding="utf-8", errors="replace"), encoding="utf-8")


def write(path: Path, text: str):
    backup(path)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def clean_preview_text_fn(js: str) -> str:
    pattern = r"""function previewText\(value, max = 220\) \{[\s\S]*?\n\}"""
    replacement = r'''function previewText(value, max = 220) {
  if (value == null) return "";

  let text = typeof value === "string" ? value : JSON.stringify(value, null, 2);

  text = text.replace(/```[\s\S]*?```/g, "[code block]");
  text = text.replace(/^#{1,6}\s+/gm, "");
  text = text.replace(/\*\*(.+?)\*\*/g, "$1");
  text = text.replace(/\*(.+?)\*/g, "$1");
  text = text.replace(/`([^`]+)`/g, "$1");
  text = text.replace(/^\s*[-*]\s+/gm, "");
  text = text.replace(/\|/g, " ");
  text = text.replace(/\s+/g, " ").trim();

  return text.length <= max ? text : `${text.slice(0, max - 3)}...`;
}'''
    new_js, count = re.subn(pattern, replacement, js, count=1)
    return new_js if count else js


def harden_components():
    path = FILES["components"]
    if not path.exists():
        print("[missing] f64_ui_components.js")
        return

    text = path.read_text(encoding="utf-8", errors="replace")

    text = text.replace('class="ghost-btn sm"', 'class="btn-ghost sm"')
    text = text.replace("class='ghost-btn sm'", "class='btn-ghost sm'")
    text = clean_preview_text_fn(text)

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


def harden_shell():
    path = FILES["shell"]
    if not path.exists():
        print("[missing] f60_ui_shell.html")
        return

    text = path.read_text(encoding="utf-8", errors="replace")

    text = "\n".join(line for line in text.splitlines() if line.strip() != "```")

    text = re.sub(
        r'href="/f61_ui_styles\.css\?v=\d+"',
        f'href="/f61_ui_styles.css?v={NEW_VERSION}"',
        text,
    )

    for name in [
        "f63_ui_api.js",
        "f64_ui_components.js",
        "f65_ui_theme.js",
        "f66_ui_workbench.js",
        "f67_ui_artifacts.js",
        "f68_ui_pets.js",
        "f69_ui_motion.js",
    ]:
        text = re.sub(
            rf'"/{re.escape(name)}(?:\?v=\d+)?"\s*:\s*"/{re.escape(name)}(?:\?v=\d+)?"',
            f'"/{name}": "/{name}?v={NEW_VERSION}"',
            text,
        )

    text = re.sub(
        r'src="/f62_ui_app\.js\?v=\d+"',
        f'src="/f62_ui_app.js?v={NEW_VERSION}"',
        text,
    )

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

    print("\nDone.")
    print("Next steps:")
    print("1. Stop the running app")
    print("2. Run: python final_hardening_pass.py")
    print("3. Run: python app.py")
    print("4. Hard refresh Preview")
    print("5. Reopen the app on mobile if needed")


if __name__ == "__main__":
    main()