#!/usr/bin/env python3
import ast
import glob
import json
import os
import sys


def get_used_keys(project_root):
    """
    Scans all .py files in the project for calls to t('string') or t("string").
    Returns a set of found keys.
    """
    keys = set()
    for root, dirs, files in os.walk(project_root):
        # Skip common non-source directories
        dirs[:] = [d for d in dirs if d not in {'.venv', '.git', '.idea', 'build', 'dist', 'scripts'}]

        for file in files:
            if file.endswith(".py"):
                path = os.path.join(root, file)
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        tree = ast.parse(f.read(), filename=path)

                    for node in ast.walk(tree):
                        if not isinstance(node, ast.Call):
                            continue
                        # Look for calls to 't' function or 'obj.t' method
                        is_t_call = False
                        if isinstance(node, ast.Call):
                            if isinstance(node.func, ast.Name) and node.func.id == 't':
                                is_t_call = True
                            elif isinstance(node.func, ast.Attribute) and node.func.attr == 't':
                                is_t_call = True

                        if is_t_call and node.args:
                            # Get the first argument if it's a string literal
                            arg = node.args[0]
                            if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                                keys.add(arg.value)

                        # Look for calls to I18nCheckBox(master, "key", ...)
                        is_i18n_comp = False
                        if isinstance(node.func, ast.Name) and node.func.id.startswith('I18n'):
                            is_i18n_comp = True
                        elif isinstance(node.func, ast.Attribute) and node.func.attr.startswith('I18n'):
                            is_i18n_comp = True
                        if is_i18n_comp:
                            # Check positional argument at index 1 (after master)
                            if len(node.args) > 1:
                                arg = node.args[1]
                                if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                                    keys.add(arg.value)

                            # Check keyword argument 'text_key'
                            for kw in node.keywords:
                                if kw.arg == 'text_key' and isinstance(kw.value, ast.Constant) and isinstance(kw.value.value, str):
                                    keys.add(kw.value.value)
                except Exception as e:
                    print(f"Warning: Failed to parse {path}: {e}")
    return keys


def validate(project_root):
    locales_dir = os.path.join(project_root, "locales")
    if not os.path.isdir(locales_dir):
        print(f"Error: 'locales' directory not found in {project_root}")
        return False

    used_keys = get_used_keys(project_root)
    json_files = glob.glob(os.path.join(locales_dir, "*.json"))

    if not json_files:
        print("Error: No .json files found in locales directory.")
        return False

    success = True

    for json_path in json_files:
        filename = os.path.basename(json_path)
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            print(f"❌ Error parsing {filename}: {e}")
            success = False
            continue

        defined_keys = set(data.keys())

        # Check 1: Keys used in code but missing in this locale file
        missing = used_keys - defined_keys
        if missing:
            print(f"❌ [{filename}] Missing keys (used in code, missing in file):")
            for k in sorted(missing):
                print(f"   - {k}")
            success = False

        # Check 2: Keys in this locale file but never used in code
        unused = defined_keys - used_keys
        if unused:
            print(f"⚠️ [{filename}] Unused keys (defined in file, not used in code):")
            for k in sorted(unused):
                print(f"   - {k}")
            success = False

    return success


if __name__ == "__main__":
    # Assume script is run from project root or scripts/ subdir
    cwd = os.getcwd()
    if os.path.exists(os.path.join(cwd, "locales")):
        root = cwd
    elif os.path.exists(os.path.join(os.path.dirname(cwd), "locales")):
        root = os.path.dirname(cwd)
    else:
        print("Error: Could not determine project root.")
        sys.exit(1)

    print(f"Running i18n validation on {root}...")
    if validate(root):
        print("✅ All i18n checks passed.")
        sys.exit(0)
    else:
        print("❌ i18n checks failed.")
        sys.exit(1)
