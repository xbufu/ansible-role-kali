#!/usr/bin/env python3
"""Add a plugin to a user's XFCE panel (panel-1) and set its options.

Usage: xfce_panel_plugin.py <user xfce4-panel.xml> <system default.xml> <spec json>

Spec keys:
  plugin       plugin type, e.g. "xkb" or "launcher"
  items        launcher only: desktop file names; also identifies the launcher
  desktop_dir  launcher only: where the desktop files come from; copied into the
               launcher's own ~/.config/xfce4/panel/launcher-<id>/ like the panel GUI does
  after        place the new plugin after the first plugin of this type ("plugin"),
               optionally one whose items include one of "items_any"
  options      plugin properties; ints are stored as uint, bools as bool

Starts from the system default when the user has no panel config yet. Prints CHANGED or
UNCHANGED; never adds the same plugin twice.
"""
import json
import re
import shutil
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


def plugin_id(prop: ET.Element) -> int:
    return int(prop.get("name", "").split("-", 1)[1])


def items_of(prop: ET.Element) -> list[str]:
    array = prop.find("./property[@name='items']")
    return [] if array is None else [v.get("value", "") for v in array]


def matches(prop: ET.Element, kind: str, items: list[str]) -> bool:
    return prop.get("value") == kind and (not items or bool(set(items) & set(items_of(prop))))


def xfconf_value(value: object) -> tuple[str, str]:
    if isinstance(value, bool):
        return "bool", "true" if value else "false"
    if isinstance(value, int) and value >= 0:
        return "uint", str(value)
    raise ValueError(f"unsupported option value {value!r}")


def set_property(plugin: ET.Element, name: str, value: object) -> bool:
    prop = plugin.find(f"./property[@name='{name}']")
    if isinstance(value, list):
        wanted = [str(v) for v in value]
        if prop is not None and prop.get("type") == "array" and [v.get("value") for v in prop] == wanted:
            return False
        if prop is not None:
            plugin.remove(prop)
        array = ET.SubElement(plugin, "property", {"name": name, "type": "array"})
        for v in wanted:
            ET.SubElement(array, "value", {"type": "string", "value": v})
        return True
    kind, text = xfconf_value(value)
    if prop is None:
        ET.SubElement(plugin, "property", {"name": name, "type": kind, "value": text})
        return True
    if prop.get("type") == kind and prop.get("value") == text:
        return False
    prop.set("type", kind)
    prop.set("value", text)
    return True


def add_plugin(plugins: ET.Element, panel_ids: ET.Element, entries: list[ET.Element], spec: dict) -> ET.Element:
    new_id = max(plugin_id(p) for p in entries) + 1
    plugin = ET.SubElement(plugins, "property", {"name": f"plugin-{new_id}", "type": "string", "value": spec["plugin"]})

    after = spec.get("after", {})
    after_ids = {str(plugin_id(p)) for p in entries if matches(p, after.get("plugin", ""), after.get("items_any", []))}
    values = list(panel_ids)
    index = next((i for i, v in enumerate(values) if v.get("value") in after_ids), len(values) - 1)
    new_value = ET.Element("value", {"type": "int", "value": str(new_id)})
    new_value.tail = values[index].tail
    panel_ids.insert(index + 1, new_value)
    return plugin


def copy_desktop_files(panel_file: Path, plugin: ET.Element, spec: dict) -> bool:
    # ~/.config/xfce4/xfconf/xfce-perchannel-xml/xfce4-panel.xml -> ~/.config/xfce4/panel/launcher-<id>/
    target = panel_file.parents[2] / "panel" / f"launcher-{plugin_id(plugin)}"
    changed = False
    for name in spec.get("items", []):
        source = Path(spec["desktop_dir"]) / name
        dest = target / name
        if dest.exists() and dest.read_bytes() == source.read_bytes():
            continue
        target.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, dest)
        changed = True
    return changed


def main(user_file: str, default_file: str, spec_json: str) -> None:
    spec = json.loads(spec_json)
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
    items = spec.get("items", [])
    plugin = next((p for p in entries if matches(p, spec["plugin"], items)), None)
    changed = plugin is None
    if plugin is None:
        plugin = add_plugin(plugins, panel_ids, entries, spec)
    options = dict(spec.get("options", {}))
    if items:
        options["items"] = items
    for name, value in options.items():
        changed = set_property(plugin, name, value) or changed
    if items and spec.get("desktop_dir"):
        changed = copy_desktop_files(path, plugin, spec) or changed

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
