#!/usr/bin/env python3
"""Add the XFCE keyboard layout indicator (xkb) to a user's panel, right after the clock.

Usage: xfce_panel_add_xkb.py <user xfce4-panel.xml> <system default.xml>
Starts from the system default when the user has no panel config yet. Prints CHANGED or
UNCHANGED; never adds a second xkb plugin.
"""
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


def plugin_id(prop):
    return int(prop.get("name").split("-", 1)[1])


def main(user_file, default_file):
    path = Path(user_file)
    source = path if path.exists() else Path(default_file)
    # Kali's default.xml has a comment ending in "<!---->" that only XFCE's lenient parser
    # accepts; comments carry nothing the panel needs (an inactive ARM layout).
    text = re.sub(r"<!--.*?-->", "", source.read_text(encoding="utf-8"), flags=re.S)
    tree = ET.ElementTree(ET.fromstring(text))
    plugins = tree.getroot().find("./property[@name='plugins']")
    panel_ids = tree.getroot().find("./property[@name='panels']/property[@name='panel-1']/property[@name='plugin-ids']")
    if plugins is None or panel_ids is None:
        sys.exit(f"{path}: no plugins or panel-1 plugin-ids")

    entries = [p for p in plugins if p.get("name", "").startswith("plugin-")]
    if any(p.get("value") == "xkb" for p in entries):
        print("UNCHANGED")
        return

    new_id = max(plugin_id(p) for p in entries) + 1
    ET.SubElement(plugins, "property", {"name": f"plugin-{new_id}", "type": "string", "value": "xkb"})

    clock_ids = {str(plugin_id(p)) for p in entries if p.get("value") == "clock"}
    values = list(panel_ids)
    after = next((i for i, v in enumerate(values) if v.get("value") in clock_ids), len(values) - 1)
    new_value = ET.Element("value", {"type": "int", "value": str(new_id)})
    new_value.tail = values[after].tail
    panel_ids.insert(after + 1, new_value)

    path.parent.mkdir(parents=True, exist_ok=True)
    tree.write(path, encoding="UTF-8", xml_declaration=True)
    print("CHANGED")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(sys.argv[1], sys.argv[2])
