#!/usr/bin/env python3
"""
Scan a front-end source tree and report which colors and spacing values it uses.

Usage: python3 scan_styles.py <src-dir> [--top N]

Reads .vue, .css, .scss and .less files. Prints:
  - colors by frequency (hex normalized to lowercase 6/8 digits; rgb()/hsl() as written)
  - px values per property group (spacing, radius, font-size); rem/em counted as 16px
  - existing CSS custom properties (--name: value)
"""
import argparse
import os
import re
import sys
from collections import Counter, defaultdict

EXTENSIONS = ('.vue', '.css', '.scss', '.less')
SKIP_DIRS = {'node_modules', 'dist', 'build', '.git', '.nuxt', '.output', 'coverage'}

HEX_RE = re.compile(r'#(?:[0-9a-fA-F]{8}|[0-9a-fA-F]{6}|[0-9a-fA-F]{3,4})\b')
FUNC_COLOR_RE = re.compile(r'\b(?:rgba?|hsla?)\([^)]*\)')
DECL_RE = re.compile(r'(?<![\w-])([a-z-]+)\s*:\s*([^;{}]+);')
# rem/em are converted at 16px, so apps that size in rem still show their real scale
LENGTH_RE = re.compile(r'(-?\d*\.?\d+)(px|rem|em)\b')
VAR_DEF_RE = re.compile(r'(--[\w-]+)\s*:\s*([^;{}]+);')

GROUPS = {
    'spacing': ('padding', 'margin', 'gap', 'row-gap', 'column-gap', 'top', 'bottom', 'left', 'right'),
    'radius': ('border-radius',),
    'font-size': ('font-size',),
}


def normalize_hex(value):
    h = value[1:].lower()
    # Expand #abc / #abcd shorthand so the same color is counted once
    if len(h) in (3, 4):
        h = ''.join(c * 2 for c in h)
    return '#' + h


def group_for(prop):
    for group, props in GROUPS.items():
        if any(prop == p or prop.startswith(p + '-') for p in props):
            return group
    return None


def style_text(path, text):
    """Return only the CSS part of a file: <style> blocks for .vue, everything otherwise."""
    if path.endswith('.vue'):
        return '\n'.join(re.findall(r'<style[^>]*>(.*?)</style>', text, re.S))
    return text


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('src')
    parser.add_argument('--top', type=int, default=25)
    args = parser.parse_args()

    files = []
    for root, dirs, names in os.walk(args.src):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        files.extend(os.path.join(root, n) for n in names if n.endswith(EXTENSIONS))
    if not files:
        sys.exit(f'No style files found under {args.src}')

    colors = Counter()
    color_files = defaultdict(set)
    px_values = defaultdict(Counter)
    variables = {}

    for i, path in enumerate(sorted(files), 1):
        print(f'[{i}/{len(files)}] {os.path.relpath(path, args.src)}', file=sys.stderr)
        with open(path, encoding='utf-8', errors='replace') as f:
            raw = f.read()
        rel = os.path.relpath(path, args.src)

        # Colors: scan whole file, since templates and scripts also hard-code colors
        for m in HEX_RE.findall(raw):
            c = normalize_hex(m)
            colors[c] += 1
            color_files[c].add(rel)
        for m in FUNC_COLOR_RE.findall(raw):
            c = re.sub(r'\s+', '', m.lower())
            colors[c] += 1
            color_files[c].add(rel)

        css = style_text(path, raw)
        for name, value in VAR_DEF_RE.findall(css):
            variables.setdefault(name, value.strip())
        for prop, value in DECL_RE.findall(css):
            group = group_for(prop)
            if group:
                for number, unit in LENGTH_RE.findall(value):
                    px = float(number) * (1 if unit == 'px' else 16)
                    px_values[group][round(px)] += 1

    print(f'\nScanned {len(files)} files under {args.src}\n')

    print(f'## Colors (top {args.top} of {len(colors)})')
    for color, count in colors.most_common(args.top):
        print(f'  {color:<28} {count:>4}x  in {len(color_files[color])} file(s)')

    for group in GROUPS:
        values = px_values[group]
        if not values:
            continue
        print(f'\n## {group} values in px (value: count)')
        ordered = sorted(values.items())
        print('  ' + ', '.join(f'{v:g}: {n}' for v, n in ordered))
        if group == 'spacing':
            off_scale = [f'{v:g}' for v, _ in ordered if v > 0 and v % 4]
            if off_scale:
                print(f'  off the 4px scale: {", ".join(off_scale)}')

    print(f'\n## CSS custom properties ({len(variables)})')
    if variables:
        for name, value in sorted(variables.items()):
            print(f'  {name}: {value}')
    else:
        print('  none defined')


if __name__ == '__main__':
    main()
