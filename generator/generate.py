#!/usr/bin/env python3
"""ux-boards: render UX documentation boards from one YAML spec.

Commands
  init  DIR           copy the starter spec into DIR/spec.yaml
  check SPEC          validate a spec, list unfilled TODOs and contrast problems
  build SPEC -o OUT   write OUT/index.html, plus --pdf and/or --png exports
"""
from __future__ import annotations

import argparse
import re
import shutil
import sys
from pathlib import Path

import yaml
from jinja2 import Environment, FileSystemLoader, StrictUndefined

HERE = Path(__file__).resolve().parent
TEMPLATES = HERE / "templates"
STARTER = HERE.parent / "template" / "spec.yaml"

BOARD_W, BOARD_H = 1400, 990
PAD = 56
HEADER_H = 236  # space taken by a screen board's heading
FRAME_GAP = 40
DEVICES = {"phone": (390, 844), "tablet": (820, 1180), "desktop": (1440, 900)}
TODO = re.compile(r"\bTODO\b")

# Neutral greys used when a screen is drawn as a wireframe.
WIRE_THEME = {
    "ink": "#1F1F1F", "muted": "#6B6B6B", "primary": "#1F1F1F",
    "primary-ink": "#FFFFFF", "tint": "#EFEFEF", "surface": "#FFFFFF",
    "shelf": "#FFFFFF", "rule": "#DADADA", "danger": "#1F1F1F",
    "warning": "#1F1F1F", "warning-bg": "#EFEFEF",
}
THEME_TOKENS = set(WIRE_THEME)


# ---------------------------------------------------------------- colour maths
def _rgb(hex_: str) -> tuple[float, float, float]:
    h = hex_.strip().lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    if not re.fullmatch(r"[0-9a-fA-F]{6}", h):
        raise ValueError(f"not a hex colour: {hex_!r}")
    return tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))


def _luminance(hex_: str) -> float:
    def lin(c: float) -> float:
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = map(lin, _rgb(hex_))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(fg: str, bg: str = "#FFFFFF") -> float:
    """WCAG 2.x contrast ratio between two hex colours."""
    hi, lo = sorted((_luminance(fg), _luminance(bg)), reverse=True)
    return (hi + 0.05) / (lo + 0.05)


# ---------------------------------------------------------------- spec helpers
def load(path: Path) -> dict:
    with path.open(encoding="utf-8") as fh:
        spec = yaml.safe_load(fh) or {}
    if not isinstance(spec, dict):
        raise SystemExit(f"{path}: the spec must be a YAML mapping")
    return spec


def walk_strings(node, trail=""):
    if isinstance(node, str):
        yield trail, node
    elif isinstance(node, dict):
        for k, v in node.items():
            yield from walk_strings(v, f"{trail}.{k}" if trail else str(k))
    elif isinstance(node, list):
        for i, v in enumerate(node):
            yield from walk_strings(v, f"{trail}[{i}]")


def norm_block(b) -> dict:
    """`- button: Save` + extra keys  ->  {"type": "button", "value": "Save", ...}"""
    if isinstance(b, str):
        return {"type": "text", "value": b}
    if not isinstance(b, dict) or not b:
        raise ValueError(f"cannot read block {b!r}")
    kind = next(iter(b))
    out = {k: v for k, v in b.items() if k != kind}
    out.update(type=kind, value=b[kind])
    if kind == "columns":
        out["value"] = [norm_blocks(col) for col in b[kind]]
    return out


def norm_blocks(blocks) -> list[dict]:
    return [norm_block(b) for b in (blocks or [])]


def problems(spec: dict) -> tuple[list[str], list[str]]:
    """Return (errors, warnings)."""
    errors, warnings = [], []
    if not (spec.get("project") or {}).get("name"):
        errors.append("project.name is required")
    sections = (spec.get("ia") or {}).get("sections") or []
    if not sections:
        errors.append("ia.sections needs at least one section")
    for i, s in enumerate(sections):
        if not s.get("name"):
            errors.append(f"ia.sections[{i}] has no name")
    names = {s.get("name") for s in sections}

    for i, c in enumerate((spec.get("visual") or {}).get("colours") or []):
        where = f"visual.colours[{i}] ({c.get('name', '?')})"
        try:
            ratio = contrast(c["hex"], c.get("on", "#FFFFFF"))
        except (KeyError, ValueError) as exc:
            errors.append(f"{where}: {exc}")
            continue
        if c.get("token") and c["token"] not in THEME_TOKENS:
            errors.append(f"{where}: unknown token {c['token']!r}; use one of {sorted(THEME_TOKENS)}")
        if c.get("role", "text") == "text" and ratio < 4.5:
            warnings.append(f"{where}: {ratio:.1f}:1 fails WCAG AA for body text (needs 4.5:1)")

    for i, sc in enumerate(spec.get("screens") or []):
        for j, fr in enumerate(sc.get("frames") or []):
            if fr.get("device") not in DEVICES:
                errors.append(f"screens[{i}].frames[{j}]: device must be one of {list(DEVICES)}")
            nav = fr.get("nav")
            if isinstance(nav, str) and nav not in names:
                warnings.append(f"screens[{i}].frames[{j}]: nav {nav!r} is not a section name")
            for key in ("blocks", "footer", "panel"):
                try:
                    norm_blocks(fr.get(key))
                except ValueError as exc:
                    errors.append(f"screens[{i}].frames[{j}].{key}: {exc}")

    todos = [f"{trail}: {text}" for trail, text in walk_strings(spec) if TODO.search(text)]
    if todos:
        warnings.append(f"{len(todos)} placeholder(s) still say TODO:")
        warnings.extend(f"    {t}" for t in todos)
    return errors, warnings


# ---------------------------------------------------------------- view model
def frame_layout(frames: list[dict]) -> float:
    """One zoom factor so every frame on a screen board fits side by side."""
    sizes = [(f.get("width") or DEVICES[f["device"]][0],
              f.get("height") or DEVICES[f["device"]][1]) for f in frames]
    avail_w = BOARD_W - 2 * PAD - FRAME_GAP * (len(frames) - 1)
    avail_h = BOARD_H - PAD - HEADER_H
    zoom = min(1.0, avail_w / sum(w for w, _ in sizes), avail_h / max(h for _, h in sizes))
    for f, (w, h) in zip(frames, sizes):
        f["w"], f["h"] = w, h
    return round(zoom, 4)


def view_model(spec: dict) -> dict:
    visual = spec.get("visual") or {}
    theme = dict(WIRE_THEME)
    for c in visual.get("colours") or []:
        ratio = contrast(c["hex"], c.get("on", "#FFFFFF"))
        role = c.get("role", "text")
        c["ratio"] = f"{ratio:.1f} : 1" if role == "text" else f"{role} only"
        c["passes"] = role != "text" or ratio >= 4.5
        if c.get("token"):
            theme[c["token"]] = c["hex"]
            if c["token"] == "warning" and c.get("on"):
                theme["warning-bg"] = c["on"]
    if theme["primary"] != WIRE_THEME["primary"]:
        theme["primary-ink"] = "#FFFFFF" if contrast("#FFFFFF", theme["primary"]) >= 4.5 else theme["ink"]

    if visual.get("components"):
        visual = dict(visual, components=norm_blocks(visual["components"]))

    screens = []
    for sc in spec.get("screens") or []:
        frames = []
        for fr in sc.get("frames") or []:
            fr = dict(fr)
            for key in ("blocks", "footer", "panel"):
                fr[key] = norm_blocks(fr.get(key))
            frames.append(fr)
        sc = dict(sc, frames=frames)
        sc["zoom"] = frame_layout(frames) if frames else 1
        sc.setdefault("style", "wire")
        screens.append(sc)

    sections = (spec.get("ia") or {}).get("sections") or []
    return {
        "spec": spec,
        "project": spec.get("project") or {},
        "labels": spec.get("release_labels") or {1: "First release", 2: "Next release"},
        "ia": spec.get("ia") or {},
        "nav_items": [s["name"] for s in sections],
        "nav_foot": (spec.get("shell") or {}).get("nav_foot") or [],
        "breakpoints": spec.get("breakpoints"),
        "screens": screens,
        "visual": visual or None,
        "theme": theme,
        "wire_theme": WIRE_THEME,
        "type": visual.get("type") or {},
        "W": BOARD_W, "H": BOARD_H, "PAD": PAD,
    }


def render_html(spec: dict) -> str:
    env = Environment(loader=FileSystemLoader(TEMPLATES), autoescape=True,
                      undefined=StrictUndefined, trim_blocks=True, lstrip_blocks=True)
    env.tests["mapping"] = lambda v: isinstance(v, dict)
    env.tests["sequence"] = lambda v: isinstance(v, list)
    env.filters["slug"] = lambda v: re.sub(r"[^a-z0-9]+", "-", str(v).lower()).strip("-")
    css = (TEMPLATES / "boards.css").read_text(encoding="utf-8")
    return env.get_template("boards.html.j2").render(css=css, **view_model(spec))


# ---------------------------------------------------------------- exports
def export(html_path: Path, out: Path, pdf: bool, png: bool) -> list[str]:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        raise SystemExit("PDF/PNG export needs Playwright:\n  pip install playwright && playwright install chromium")
    overflow = []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": BOARD_W, "height": BOARD_H})
        page.goto(html_path.resolve().as_uri())
        page.wait_for_load_state("networkidle")
        page.evaluate("document.fonts.ready.then(() => true)")
        overflow = page.evaluate(
            """() => [...document.querySelectorAll('.board')].flatMap((b, i) =>
                b.scrollHeight > b.clientHeight + 1 ? [`board ${i + 1} (${b.dataset.name})`] : [])""")
        if png:
            for i, board in enumerate(page.query_selector_all(".board"), 1):
                name = board.get_attribute("data-slug")
                board.screenshot(path=str(out / f"{i:02d}-{name}.png"))
        if pdf:
            page.pdf(path=str(out / "boards.pdf"), width=f"{BOARD_W}px", height=f"{BOARD_H}px",
                     print_background=True, prefer_css_page_size=True)
        browser.close()
    return overflow


# ---------------------------------------------------------------- CLI
def cmd_init(args) -> int:
    target = Path(args.dir)
    target.mkdir(parents=True, exist_ok=True)
    dest = target / "spec.yaml"
    if dest.exists() and not args.force:
        print(f"{dest} already exists (use --force to overwrite)")
        return 1
    shutil.copyfile(STARTER, dest)
    print(f"Wrote {dest}. Replace every TODO, then run:\n"
          f"  python {sys.argv[0]} build {dest} -o {target / 'out'} --pdf")
    return 0


def report(spec_path: Path, strict: bool, limit: int | None = None) -> tuple[dict, bool]:
    spec = load(spec_path)
    errors, warnings = problems(spec)
    for e in errors:
        print(f"error: {e}")
    todo_lines = [w for w in warnings if w.startswith("    ")]
    for w in warnings:
        if not w.startswith("    "):
            print(f"warning: {w}")
    shown = todo_lines if limit is None else todo_lines[:limit]
    for w in shown:
        print(w)
    if len(shown) < len(todo_lines):
        print(f"    ... and {len(todo_lines) - len(shown)} more (run `check` to list them all)")
    ok = not errors and not (strict and warnings)
    return spec, ok


def cmd_check(args) -> int:
    _, ok = report(Path(args.spec), args.strict)
    print("ok" if ok else "spec has problems")
    return 0 if ok else 1


def cmd_build(args) -> int:
    spec, ok = report(Path(args.spec), args.strict, limit=8)
    if not ok:
        return 1
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    html_path = out / "index.html"
    html_path.write_text(render_html(spec), encoding="utf-8")
    print(f"wrote {html_path}")
    if args.pdf or args.png:
        for b in export(html_path, out, args.pdf, args.png):
            print(f"warning: {b} is taller than one page; trim it or split it")
        if args.pdf:
            print(f"wrote {out / 'boards.pdf'}")
        if args.png:
            print(f"wrote PNGs to {out}")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("init", help="start a new spec from the template")
    p.add_argument("dir")
    p.add_argument("--force", action="store_true")
    p.set_defaults(fn=cmd_init)
    p = sub.add_parser("check", help="validate a spec")
    p.add_argument("spec")
    p.add_argument("--strict", action="store_true", help="treat warnings (including TODOs) as errors")
    p.set_defaults(fn=cmd_check)
    p = sub.add_parser("build", help="render the boards")
    p.add_argument("spec")
    p.add_argument("-o", "--out", default="out")
    p.add_argument("--pdf", action="store_true", help="also write boards.pdf (needs Playwright)")
    p.add_argument("--png", action="store_true", help="also write one PNG per board (needs Playwright)")
    p.add_argument("--strict", action="store_true")
    p.set_defaults(fn=cmd_build)
    args = ap.parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
