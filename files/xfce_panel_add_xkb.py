#!/usr/bin/env python3
"""Add the XFCE keyboard layout indicator (xkb) to a user's panel, right after the clock,
and set its options.

Usage: xfce_panel_add_xkb.py <user xfce4-panel.xml> <system default.xml> <options json>
Options map xkb plugin property names to values, e.g. {"display-type": 1, "caps-lock-indicator": false};
ints are stored as uint, bools as bool. Starts from the system default when the user has no
panel config yet. Prints CHANGED or UNCHANGED; never adds a second xkb plugin.
"""
import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


def plugin_id(prop):
    return int(prop.get("name").split("-", 1)[1])


def xfconf_value(value):
    if isinstance(value, bool):
        return "bool", "true" if value else "false"
    if isinstance(value, int) and value >= 0:
        return "uint", str(value)
    raise ValueError(f"unsupported option value {value!r}")


def add_plugin(plugins, panel_ids, entries):
    new_id = max(plugin_id(p) for p in entries) + 1
    plugin = ET.SubElement(plugins, "property", {"name": f"plugin-{new_id}", "type": "string", "value": "xkb"})

    clock_ids = {str(plugin_id(p)) for p in entries if p.get("value") == "clock"}
    values = list(panel_ids)
    after = next((i for i, v in enumerate(values) if v.get("value") in clock_ids), len(values) - 1)
    new_value = ET.Element("value", {"type": "int", "value": str(new_id)})
    new_value.tail = values[after].tail
    panel_ids.insert(after + 1, new_value)
    return plugin


def set_options(plugin, options):
    changed = False
    for name, value in options.items():
        kind, text = xfconf_value(value)
        prop = plugin.find(f"./property[@name='{name}']")
        if prop is None:
            ET.SubElement(plugin, "property", {"name": name, "type": kind, "value": text})
            changed = True
        elif prop.get("type") != kind or prop.get("value") != text:
            prop.set("type", kind)
            prop.set("value", text)
            changed = True
    return changed


def main(user_file, default_file, options_json):
    options = json.loads(options_json)
    path = Path(user_file)
    source = path if path.exists() else Path(default_file)
    # Kali's default.xml has a comment ending in "<!---->" that only XFCE's lenient parser
    # accepts; comments carry nothing the panel needs (an inactive ARM layout).
    text = re.sub(r"<!--.*?-->", "", source.read_text(encoding="utf-8"), flags=re.S)
    root = ET.fromstring(text)
    tree = ET.ElementTree(root)
    plugins = root.find("./property[@name='plugins']")
    panel_ids = root.find("./property[@name='panels']/property[@name='panel-1']/property[@name='plugin-ids']")
    if plugins is None or panel_ids is None:
        sys.exit(f"{source}: no plugins or panel-1 plugin-ids")

    entries = [p for p in plugins if p.get("name", "").startswith("plugin-")]
    plugin = next((p for p in entries if p.get("value") == "xkb"), None)
    changed = plugin is None
    if plugin is None:
        plugin = add_plugin(plugins, panel_ids, entries)
    changed = set_options(plugin, options) or changed

    if not changed:
        print("UNCHANGED")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    tree.write(path, encoding="UTF-8", xml_declaration=True)
    print("CHANGED")


if __name__ == "__main__":
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    main(sys.argv[1], sys.argv[2], sys.argv[3])
