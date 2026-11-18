#!/usr/bin/env python3
"""Build CSP-safe single-file anatomy exports from the site pages.

Site pages keep script-src 'self' plus the theme-boot hash and load
anatomy.js as an external file. Standalone files inline CSS/JS, so every
executable inline script must have a matching sha256 hash in CSP.
'unsafe-inline' is not added to script-src: once a hash is present,
browsers ignore 'unsafe-inline' and would still block any unhashed script.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SITE = "https://88daxiong.github.io/xhot/"
ANAT = SITE + "anatomy/"
THEME_HASH = "sha256-eySqtWEMW2APPEHKl4ofjbb4sL/hbt3uVDrovVQbBOY="

SCRIPT_TAG = re.compile(r"<script([^>]*)>(.*?)</script>", re.S | re.I)
CSP_ATTR = re.compile(
    r'(<meta http-equiv="Content-Security-Policy" content=")([^"]+)(")',
    re.I,
)


def sha256_b64(data: bytes) -> str:
    return base64.b64encode(hashlib.sha256(data).digest()).decode("ascii")


def script_is_executable(attrs: str) -> bool:
    typ = re.search(r'type\s*=\s*["\']([^"\']+)["\']', attrs, re.I)
    if typ:
        t = typ.group(1).strip().lower()
        if t in ("", "text/javascript", "application/javascript", "module"):
            return True
        return False
    return "src=" not in attrs.lower()


def executable_inline_scripts(html: str) -> list[tuple[str, str, bytes, str]]:
    """Return (attrs, body_text, body_bytes, sha256-xxx) for executable inline scripts."""
    out = []
    for m in SCRIPT_TAG.finditer(html):
        attrs, body = m.group(1), m.group(2)
        if re.search(r"\bsrc\s*=", attrs, re.I):
            continue
        if not script_is_executable(attrs):
            continue
        raw = body.encode("utf-8")
        out.append((attrs, body, raw, "sha256-" + sha256_b64(raw)))
    return out


def csp_script_src(html: str) -> str | None:
    m = CSP_ATTR.search(html)
    if not m:
        return None
    parts = [p.strip() for p in m.group(2).split(";") if p.strip()]
    for p in parts:
        if p.startswith("script-src"):
            return p
    return None


def set_script_src(html: str, hashes: list[str]) -> str:
    m = CSP_ATTR.search(html)
    if not m:
        raise SystemExit("missing CSP meta")
    parts = [p.strip() for p in m.group(2).split(";") if p.strip()]
    tokens = ["'self'"] + [f"'{h}'" for h in hashes]
    new_src = "script-src " + " ".join(tokens)
    replaced = False
    out_parts = []
    for p in parts:
        if p.startswith("script-src"):
            out_parts.append(new_src)
            replaced = True
        else:
            out_parts.append(p)
    if not replaced:
        # keep default-src first if present
        if out_parts and out_parts[0].startswith("default-src"):
            out_parts.insert(1, new_src)
        else:
            out_parts.insert(0, new_src)
    new_csp = "; ".join(out_parts)
    return CSP_ATTR.sub(lambda mm: mm.group(1) + new_csp + mm.group(3), html, count=1)


def rewrite_links(html: str) -> str:
    html = html.replace('href="index.html"', f'href="{ANAT}index.html"')
    for name in ("ai-memory.html", "weknora.html", "git-twig.html", "motlab.html", "pybot.html", "rust-anything.html", "borg.html", "mas-office.html"):
        html = html.replace(f'href="{name}"', f'href="{ANAT}{name}"')
    html = html.replace('href="exports/', f'href="{ANAT}exports/')
    html = html.replace('href="../', f'href="{SITE}')
    return html


def build_one(src_html: Path, css: str, js: str) -> str:
    t = src_html.read_text(encoding="utf-8")
    if 'href="anatomy.css"' not in t or 'src="anatomy.js"' not in t:
        raise SystemExit(f"{src_html} is not a site page with external anatomy.css/js")
    t = t.replace(
        '<link rel="stylesheet" href="anatomy.css">',
        "<style>\n" + css + "\n</style>",
        1,
    )
    # Keep the inlined JS body stable and explicit so the hash is reproducible.
    t = t.replace('<script src="anatomy.js" defer></script>\n', "", 1)
    if "anatomy.js" in t:
        raise SystemExit(f"{src_html} still references anatomy.js after rewrite")
    js_block = "<script>\n" + js + "\n</script>\n"
    if "</body>" not in t:
        raise SystemExit(f"{src_html} missing </body>")
    t = t.replace("</body>", js_block + "</body>", 1)
    t = rewrite_links(t)
    hashes = [item[3] for item in executable_inline_scripts(t)]
    if THEME_HASH not in hashes:
        raise SystemExit(f"{src_html}: theme boot hash missing or changed: {hashes}")
    if len(hashes) < 2:
        raise SystemExit(f"{src_html}: expected theme boot + inlined anatomy.js, got {hashes}")
    t = set_script_src(t, hashes)
    # verify immediately
    ok, detail = verify_html(t)
    if not ok:
        raise SystemExit(f"{src_html}: post-build CSP check failed: {detail}")
    return t


def verify_html(html: str) -> tuple[bool, str]:
    src = csp_script_src(html)
    if not src:
        return False, "no script-src"
    if "unsafe-inline" in src:
        return False, "script-src still contains unsafe-inline (ignored when hashes exist)"
    declared = re.findall(r"'sha256-[^']+'", src)
    declared_set = {d.strip("'") for d in declared}
    scripts = executable_inline_scripts(html)
    got = [s[3] for s in scripts]
    missing = [h for h in got if h not in declared_set]
    extra = [h for h in declared_set if h not in got]
    if missing:
        return False, f"inline scripts missing from CSP: {missing}; got={got}; csp={src}"
    if extra:
        return False, f"CSP hashes with no matching inline script: {extra}; got={got}; csp={src}"
    if "src=\"anatomy.js\"" in html or "href=\"anatomy.css\"" in html:
        return False, "export still points at external anatomy.css/js"
    if THEME_HASH not in got:
        return False, f"theme hash drifted: {got}"
    return True, f"ok {len(got)} hashed scripts: {got}"


def check_file(path: Path) -> tuple[bool, str]:
    return verify_html(path.read_text(encoding="utf-8"))


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true", help="only verify existing exports")
    args = ap.parse_args(argv)
    exports = {
        "ai-memory.html": HERE / "exports" / "ai-memory.standalone.html",
        "weknora.html": HERE / "exports" / "weknora.standalone.html",
        "pybot.html": HERE / "exports" / "pybot.standalone.html",
        "rust-anything.html": HERE / "exports" / "rust-anything.standalone.html",
        "borg.html": HERE / "exports" / "borg.standalone.html",
        "mas-office.html": HERE / "exports" / "mas-office.standalone.html",
    }
    if args.check:
        failed = 0
        for src, dest in exports.items():
            ok, detail = check_file(dest)
            print(f"{dest.name}: {'PASS' if ok else 'FAIL'} {detail}")
            if not ok:
                failed += 1
        return failed
    css = (HERE / "anatomy.css").read_text(encoding="utf-8")
    js = (HERE / "anatomy.js").read_text(encoding="utf-8")
    if "</style" in css.lower() or "</script" in js.lower():
        raise SystemExit("refusing to inline CSS/JS that contains a closing tag")
    for src_name, dest in exports.items():
        html = build_one(HERE / src_name, css, js)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(html, encoding="utf-8")
        ok, detail = check_file(dest)
        print(f"wrote {dest} ({len(html)} bytes) {detail}")
        if not ok:
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
