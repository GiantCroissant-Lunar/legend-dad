#!/usr/bin/env python3
"""Download Godot 4.6.2 web export templates from GitHub releases."""

import io
import platform
import sys
import urllib.request
import zipfile
from pathlib import Path

GODOT_VERSION = "4.6.2"
GODOT_VERSION_TAG = f"{GODOT_VERSION}-stable"
TEMPLATE_FOLDER_NAME = f"{GODOT_VERSION}.stable"

DOWNLOAD_URL = (
    f"https://github.com/godotengine/godot/releases/download/{GODOT_VERSION_TAG}/"
    f"Godot_v{GODOT_VERSION}-stable_export_templates.tpz"
)


def get_template_dir() -> Path:
    """Return OS-appropriate Godot export templates directory."""
    system = platform.system()
    if system == "Darwin":
        return Path.home() / "Library" / "Application Support" / "Godot" / "export_templates" / TEMPLATE_FOLDER_NAME
    if system == "Windows":
        return Path.home() / "AppData" / "Roaming" / "Godot" / "export_templates" / TEMPLATE_FOLDER_NAME
    if system == "Linux":
        return Path.home() / ".local" / "share" / "godot" / "export_templates" / TEMPLATE_FOLDER_NAME
    print(f"Unsupported OS: {system}", file=sys.stderr)
    sys.exit(1)


def main() -> None:
    template_dir = get_template_dir()

    if template_dir.exists() and any(template_dir.iterdir()):
        print(f"Export templates already exist at {template_dir}")
        print("Delete the directory to re-download.")
        return

    print(f"Downloading export templates from:\n  {DOWNLOAD_URL}")
    print("This may take a few minutes...")

    try:
        response = urllib.request.urlopen(DOWNLOAD_URL)  # noqa: S310
        data = response.read()
    except Exception as e:
        print(f"Download failed: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"Extracting to {template_dir}...")
    template_dir.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        for member in zf.namelist():
            # Templates are inside a "templates/" folder in the zip
            if member.startswith("templates/") and not member.endswith("/"):
                filename = member.replace("templates/", "", 1)
                target = template_dir / filename
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(zf.read(member))

    print("Done! Export templates installed.")


if __name__ == "__main__":
    main()
