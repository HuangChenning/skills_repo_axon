#!/usr/bin/env python3
"""Programmatic README compliance checker for the beautify-readme skill.

Checks four dimensions that can be verified without human judgment:
  1. Content architecture — sections, install path, alt text
  2. Visual system — SVG structure, legible text, no fragile features
  3. Quality bar — AI filler phrases, pure black, meaningful alt text
  4. Diagram integrity — fence syntax and editorial-static provenance

Usage:
  python3 verify_readme.py README.md
  python3 verify_readme.py README.md --svg-dir ./assets/readme

Exit codes:
  0 — all checks passed
  1 — one or more checks failed
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# AI filler phrases to detect
# ---------------------------------------------------------------------------
AI_FILLER = [
    "empower", "seamless", "seamlessly", "unleash", "next-generation",
    "cutting-edge", "revolutionary", "game-changing", "world-class",
    "state-of-the-art", "best-in-class", "industry-leading",
]

FILLER_DATA = [
    "99.99%", "99.999%", "1234567", "1000000+",
]

GENERIC_ALT_TEXT = [
    "banner", "image", "logo", "picture", "photo", "img",
    "hero", "header", "graphic", "icon",
]

EDITORIAL_STATIC_TYPES = {
    "flowchart", "dependency", "class", "er", "db-schema",
    "tree", "timeline", "swimlane",
}
EDITORIAL_STATIC_FORMATS = {"svg", "png"}
EDITORIAL_STATIC_SIZES = {
    "doc-inline": (960.0, 600.0),
    "doc-wide": (1200.0, 675.0),
}
EDITORIAL_STATIC_DETAILS = {"faithful", "balanced", "simplified"}
EDITORIAL_STATIC_AUDIENCES = {"engineer", "mixed", "executive"}
EDITORIAL_STATIC_BUDGETS = {
    "faithful": {"nodes": 18, "connectors": 32},
    "balanced": {"nodes": 9, "connectors": 12},
    "simplified": {"nodes": 7, "connectors": 9},
}


class CheckResult:
    def __init__(self, name, passed, detail=""):
        self.name = name
        self.passed = passed
        self.detail = detail

    def __str__(self):
        mark = "✓" if self.passed else "✗"
        line = f"  {mark} {self.name}"
        if self.detail:
            line += f": {self.detail}"
        return line


def read_file(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return None


def parse_svg_attribute(opening_tag, name):
    """Return one quoted SVG attribute value from an opening tag."""
    match = re.search(
        rf'\b{re.escape(name)}\s*=\s*(["\'])(.*?)\1',
        opening_tag,
        re.IGNORECASE | re.DOTALL,
    )
    return match.group(2) if match else None


def is_archify_export(opening_tag):
    """Return True when the root <svg> carries Archify's export contract markers."""
    labelled_by = parse_svg_attribute(opening_tag, "aria-labelledby") or ""
    return (
        parse_svg_attribute(opening_tag, "data-layout-contract") is not None
        and "archify-diagram-title" in labelled_by.split()
    )


def font_faces_are_embedded(content):
    """Return True when every @font-face src uses only data: URIs."""
    blocks = re.findall(r"@font-face\s*\{[^}]*\}", content)
    if not blocks:
        return False
    for block in blocks:
        urls = re.findall(r"url\(\s*['\"]?([^'\")\s]+)", block)
        if not urls or any(not url.startswith("data:") for url in urls):
            return False
    return True


# ---------------------------------------------------------------------------
# Dimension 1: Content architecture
# ---------------------------------------------------------------------------

def check_content_sections(readme):
    """Check that essential content sections are present."""
    results = []
    text_lower = readme.lower()

    # Check for at least one heading that suggests "what is this"
    has_what = bool(re.search(r"^#+\s.*(what|about|overview|introduction|是什么|概述|简介|介绍|它能做什么)", text_lower, re.MULTILINE))
    results.append(CheckResult(
        "1.1 What-is section present",
        has_what,
        "" if has_what else "No heading describing what the project is"
    ))

    # Check for install / getting started
    has_install = bool(re.search(r"^#+\s.*(install|getting started|quick start|setup|usage|安装|使用|快速开始|入门|开始使用)", text_lower, re.MULTILINE))
    results.append(CheckResult(
        "1.2 Install / usage section present",
        has_install,
        "" if has_install else "No installation or usage section found"
    ))

    # Check for code block with install-like commands
    # Extract all code blocks and check if any line contains install commands
    code_blocks = re.findall(r"```(?:\w*)\s*\n(.*?)```", readme, re.DOTALL)
    has_install_cmd = any(
        re.search(r"(npm|pip|cargo|brew|apt|yum|go\s+install|cp\s+-r|git\s+clone|docker)", block, re.IGNORECASE)
        for block in code_blocks
    )
    results.append(CheckResult(
        "1.3 Install commands in code block",
        has_install_cmd,
        "" if has_install_cmd else "No code block with install commands detected"
    ))

    # Check README doesn't start with a long table of contents
    lines = readme.split("\n")
    non_empty = [l for l in lines if l.strip()]
    starts_with_toc = False
    if non_empty:
        first_heading_idx = None
        for i, line in enumerate(non_empty[:20]):
            if line.startswith("#"):
                first_heading_idx = i
                break
        if first_heading_idx is not None:
            heading_text = non_empty[first_heading_idx].lower()
            if "table of contents" in heading_text or heading_text == "## contents" or "目录" in heading_text:
                starts_with_toc = True
    results.append(CheckResult(
        "1.4 README does not start with TOC",
        not starts_with_toc,
        "" if not starts_with_toc else "README starts with a table of contents — lead with value instead"
    ))

    # Check for limitations / caveats section
    has_limits = bool(re.search(r"^#+\s.*(limit|caveat|constraint|known issue|trade.off|局限|限制|约束|已知问题|注意事项)", text_lower, re.MULTILINE))
    results.append(CheckResult(
        "1.5 Limitations section present",
        has_limits,
        "" if has_limits else "No limitations or constraints section — add one if limitations affect user choice"
    ))

    return results


# Stage keywords for Value → Proof → Mechanism → First use → Detail sequence
STAGE_KEYWORDS = {
    "Value": [
        "what", "about", "overview", "introduction", "features",
        "它能做什么", "是什么", "概述", "简介", "介绍", "功能", "特点",
    ],
    "Proof": [
        "proof", "demo", "example", "screenshot", "showcase", "benchmark",
        "result", "outcome", "output", "deliverable",
        "示例", "演示", "截图", "效果", "展示", "成果", "产出", "结果",
    ],
    "Mechanism": [
        "how it works", "architecture", "design", "mechanism", "principle",
        "工作原理", "工作流程", "流程", "架构", "原理", "机制", "设计",
    ],
    "First use": [
        "install", "getting started", "quick start", "setup", "usage",
        "安装", "使用", "快速开始", "入门", "开始使用",
    ],
    "Detail": [
        "api", "configuration", "advanced", "reference", "faq", "contributing",
        "license", "limitation", "constraint", "caveat",
        "配置", "高级", "参考", "常见问题", "贡献", "许可证", "局限", "限制",
    ],
}

# The recommended order
STAGE_ORDER = ["Value", "Proof", "Mechanism", "First use", "Detail"]


def classify_heading(heading_text):
    """Map a heading to a content-architecture stage. Returns stage name or None."""
    text_lower = heading_text.lower()
    for stage in STAGE_ORDER:
        for kw in STAGE_KEYWORDS[stage]:
            if kw in text_lower:
                return stage
    return None


def check_content_sequence(readme):
    """Check that sections follow Value → Proof → Mechanism → First use → Detail order."""
    results = []

    # Extract all headings (## and #) with their line positions
    headings = []
    for match in re.finditer(r"^(#{1,2})\s+(.+)$", readme, re.MULTILINE):
        level = len(match.group(1))
        text = match.group(2).strip()
        pos = match.start()
        headings.append((level, text, pos))

    if not headings:
        results.append(CheckResult(
            "1.7 Content sequence order",
            False,
            "No headings found"
        ))
        return results

    # Classify each heading to a stage
    stage_positions = {}  # stage -> first occurrence position
    for level, text, pos in headings:
        stage = classify_heading(text)
        if stage and stage not in stage_positions:
            stage_positions[stage] = pos

    found_stages = [s for s in STAGE_ORDER if s in stage_positions]

    if len(found_stages) < 2:
        results.append(CheckResult(
            "1.7 Content sequence order",
            True,
            f"Only {len(found_stages)} stage(s) detected — order check N/A"
        ))
        return results

    # Check that found stages appear in the correct relative order
    order_ok = True
    violations = []
    for i in range(len(found_stages) - 1):
        earlier = found_stages[i]
        later = found_stages[i + 1]
        if stage_positions[earlier] > stage_positions[later]:
            order_ok = False
            violations.append(f"{earlier} appears after {later}")

    results.append(CheckResult(
        "1.7 Content sequence order (Value → Proof → Mechanism → First use → Detail)",
        order_ok,
        "; ".join(violations) if violations else f"Stages in order: {' → '.join(found_stages)}"
    ))

    return results


def check_alt_text(readme):
    """Check that images have meaningful alt text."""
    results = []
    images = []

    # Match ![alt](src) patterns.
    img_pattern = re.compile(r"!\[([^\]]*)\]\(([^)]+)\)")
    images.extend(img_pattern.findall(readme))

    # Match HTML images, which are commonly used for centered/full-width heroes.
    for tag in re.findall(r"<img\b[^>]*>", readme, re.IGNORECASE):
        src_match = re.search(
            r'\bsrc=(["\'])(.*?)\1',
            tag,
            re.IGNORECASE | re.DOTALL,
        )
        if not src_match:
            continue
        alt_match = re.search(
            r'\balt=(["\'])(.*?)\1',
            tag,
            re.IGNORECASE | re.DOTALL,
        )
        images.append((alt_match.group(2) if alt_match else "", src_match.group(2)))

    if not images:
        results.append(CheckResult(
            "1.6 Images have alt text",
            True,
            "No images found (N/A)"
        ))
        return results

    for alt, src in images:
        alt_clean = alt.strip().lower()
        if not alt_clean:
            results.append(CheckResult(
                f"1.6 Alt text for {os.path.basename(src)}",
                False,
                "Empty alt text"
            ))
        elif alt_clean in GENERIC_ALT_TEXT:
            results.append(CheckResult(
                f"1.6 Alt text for {os.path.basename(src)}",
                False,
                f"Generic alt text '{alt}' — describe the purpose"
            ))
        else:
            results.append(CheckResult(
                f"1.6 Alt text for {os.path.basename(src)}",
                True,
                f"'{alt[:50]}...'" if len(alt) > 50 else f"'{alt}'"
            ))

    return results


MECHANISM_HEADING = re.compile(
    r"(how it works|architecture|workflow|sequence|data flow|dataflow|"
    r"lifecycle|mechanism|repository structure|工作原理|架构|工作流|流程|"
    r"数据流|生命周期|机制|仓库结构)",
    re.IGNORECASE,
)
PROSE_ONLY_DECISION = re.compile(
    r"<!--\s*diagram-decision:\s*prose-only\s*\|\s*reason:\s*(.*?)\s*-->",
    re.IGNORECASE | re.DOTALL,
)


def extract_heading_sections(readme):
    """Return Markdown heading text and the body controlled by that heading."""
    headings = list(re.finditer(r"^(#{1,6})\s+(.+)$", readme, re.MULTILINE))
    sections = []
    for index, heading in enumerate(headings):
        level = len(heading.group(1))
        end = len(readme)
        for candidate in headings[index + 1:]:
            if len(candidate.group(1)) <= level:
                end = candidate.start()
                break
        sections.append((heading.group(2).strip(), readme[heading.end():end]))
    return sections


def mechanism_stage_count(section):
    """Estimate whether a mechanism section contains four or more stages."""
    arrow_count = len(re.findall(r"(?:→|⇒|--?>)", section))
    numbered_count = len(re.findall(r"^\s*\d+[.)]\s+\S", section, re.MULTILINE))
    return max(arrow_count + 1 if arrow_count else 0, numbered_count)


def mechanism_has_visual(section):
    """Detect a static image, SVG/HTML map, or supported diagram fence."""
    return bool(
        re.search(r"!\[[^\]]*\]\([^)]+\)", section)
        or re.search(r"<img\b[^>]*>", section, re.IGNORECASE)
        or re.search(
            r"```(?:plantuml|puml|vega(?:-lite)?|infographic|canvas)\b",
            section,
            re.IGNORECASE,
        )
        or re.search(r"<svg\b|data-diagram-engine=|class=[\"'][^\"']*arch-", section)
    )


def check_mechanism_visualization(readme):
    """Require a visual or an explicit reason for complex mechanism sections."""
    results = []
    mechanism_sections = [
        (heading, section)
        for heading, section in extract_heading_sections(readme)
        if MECHANISM_HEADING.search(heading)
    ]
    if not mechanism_sections:
        return [CheckResult(
            "1.8 Structured-visual opportunity assessed",
            True,
            "No mechanism section found (N/A)",
        )]

    complex_sections = 0
    for heading, section in mechanism_sections:
        stages = mechanism_stage_count(section)
        if stages < 4:
            continue
        complex_sections += 1
        if mechanism_has_visual(section):
            results.append(CheckResult(
                f"1.8 Mechanism visual: {heading}",
                True,
                f"{stages} stages; structured visual present",
            ))
            continue

        decision = PROSE_ONLY_DECISION.search(section)
        reason = decision.group(1).strip() if decision else ""
        reason_is_concrete = (
            len(reason) >= 12
            and reason.lower() not in {
                "not needed", "not applicable", "n/a", "none", "无需", "不需要",
            }
        )
        results.append(CheckResult(
            f"1.8 Mechanism visual: {heading}",
            reason_is_concrete,
            (
                f"{stages} stages; prose-only reason recorded: {reason}"
                if reason_is_concrete
                else (
                    f"{stages} stages but no structured visual or concrete "
                    "diagram-decision comment"
                )
            ),
        ))

    if complex_sections == 0:
        results.append(CheckResult(
            "1.8 Structured-visual opportunity assessed",
            True,
            "Mechanism sections are below the four-stage threshold",
        ))
    return results


# ---------------------------------------------------------------------------
# Dimension 2: Visual system (SVG checks)
# ---------------------------------------------------------------------------

def find_svg_files(readme, readme_path, svg_dir=None):
    """Find all local SVG files referenced in the README."""
    svg_files = []
    readme_dir = os.path.dirname(os.path.abspath(readme_path))

    # From img tags ![alt](path)
    img_pattern = re.compile(r"!\[[^\]]*\]\(([^)]+\.svg)\)")
    for match in img_pattern.findall(readme):
        if match.startswith("http"):
            continue
        full_path = os.path.join(readme_dir, match) if not os.path.isabs(match) else match
        svg_files.append(full_path)

    # From HTML img tags <img src="path.svg">
    html_pattern = re.compile(r'<img[^>]+src=["\']([^"\']+\.svg)["\']')
    for match in html_pattern.findall(readme):
        if match.startswith("http"):
            continue
        full_path = os.path.join(readme_dir, match) if not os.path.isabs(match) else match
        if full_path not in svg_files:
            svg_files.append(full_path)

    # Additional SVG directory
    if svg_dir:
        for f in Path(svg_dir).rglob("*.svg"):
            if str(f) not in svg_files:
                svg_files.append(str(f))

    return svg_files


def check_svg_files(svg_files, readme_path):
    """Check SVG file structure and quality."""
    results = []

    if not svg_files:
        results.append(CheckResult(
            "2.1 SVG files found",
            True,
            "No SVG files referenced (N/A)"
        ))
        return results

    readme_dir = os.path.dirname(os.path.abspath(readme_path))

    for svg_path in svg_files:
        content = read_file(svg_path)
        if content is None:
            results.append(CheckResult(
                f"2.1 SVG exists: {os.path.basename(svg_path)}",
                False,
                "File not found"
            ))
            continue

        basename = os.path.basename(svg_path)

        # viewBox check
        has_viewbox = "viewBox" in content
        results.append(CheckResult(
            f"2.2 viewBox present: {basename}",
            has_viewbox,
            "" if has_viewbox else "Missing viewBox attribute"
        ))

        # Full-width assets use 1200. Editorial-static doc-inline diagrams may
        # use 960 only when their root explicitly declares the production branch.
        svg_open_match = re.search(r"<svg\b[^>]*>", content, re.IGNORECASE | re.DOTALL)
        svg_open = svg_open_match.group(0) if svg_open_match else ""
        diagram_engine = parse_svg_attribute(svg_open, "data-diagram-engine")
        readme_preset = parse_svg_attribute(svg_open, "data-readme-preset")
        archify_export = is_archify_export(svg_open)
        vb_match = re.search(r'viewBox=["\'](\d+(?:\.\d+)?)\s+(\d+(?:\.\d+)?)\s+(\d+(?:\.\d+)?)\s+(\d+(?:\.\d+)?)["\']', content)
        if vb_match:
            vb_width = float(vb_match.group(3))
            # Archify sizes its own reader-fit canvas, so any positive width is accepted.
            approved_width = abs(vb_width - 1200) < 1 or (
                abs(vb_width - 960) < 1
                and diagram_engine == "editorial-static"
                and readme_preset == "doc-inline"
            ) or (archify_export and vb_width > 0)
            results.append(CheckResult(
                f"2.3 Approved viewBox width: {basename}",
                approved_width,
                (
                    f"width={vb_width}; expected 1200, marked editorial-static doc-inline at 960, or an Archify export"
                    if not approved_width else ""
                )
            ))
        else:
            results.append(CheckResult(
                f"2.3 Approved viewBox width: {basename}",
                False,
                "Could not parse viewBox"
            ))

        # title and desc
        has_title = "<title" in content
        results.append(CheckResult(
            f"2.4 <title> element: {basename}",
            has_title,
            "" if has_title else "Missing <title> element"
        ))

        has_desc = "<desc" in content
        results.append(CheckResult(
            f"2.5 <desc> element: {basename}",
            has_desc,
            "" if has_desc else "Missing <desc> element"
        ))

        # No fragile features
        fragile = []
        if "<script" in content:
            fragile.append("<script>")
        if "foreignObject" in content:
            fragile.append("foreignObject")
        if "@import" in content:
            fragile.append("@import")
        if "@font-face" in content and not (
            archify_export and font_faces_are_embedded(content)
        ):
            fragile.append("remote font")
        if re.search(r'https?://[^"\'>\s]+\.(woff2?|ttf|otf|css)', content):
            fragile.append("external font/css")
        results.append(CheckResult(
            f"2.6 No fragile SVG features: {basename}",
            len(fragile) == 0,
            ", ".join(fragile) if fragile else ""
        ))

        # No pure black #000000
        has_pure_black = bool(re.search(r'#000000\b|#000\b', content, re.IGNORECASE))
        results.append(CheckResult(
            f"2.7 No pure black #000000: {basename}",
            not has_pure_black,
            "Use off-black like #1a1a1a or #333" if has_pure_black else ""
        ))

        # System fonts check — every font-family declaration must end with a
        # generic family keyword (sans-serif, serif, monospace, system-ui, etc.)
        # Match double-quoted and single-quoted attributes separately so that
        # one quote type can appear inside the other (e.g. font-family="...'Segoe UI'...,")
        font_decls = re.findall(r'font-family="([^"]*)"', content) + \
                     re.findall(r"font-family='([^']*)'", content)
        generic_families = {"sans-serif", "serif", "monospace", "system-ui", "cursive", "fantasy"}
        all_system = True
        non_system_found = []
        for decl in font_decls:
            last_token = decl.rstrip("'").split(",")[-1].strip().lower().strip("'\"")
            if last_token not in generic_families:
                all_system = False
                non_system_found.append(decl)
        results.append(CheckResult(
            f"2.8 System font stack: {basename}",
            all_system,
            f"Non-generic fallback: {'; '.join(non_system_found[:2])}" if not all_system else ""
        ))

    return results


# ---------------------------------------------------------------------------
# Dimension 3: Quality bar (AI filler, taste)
# ---------------------------------------------------------------------------

def check_ai_filler(readme):
    """Check for AI filler phrases and generic content."""
    results = []
    text_lower = readme.lower()

    found_filler = []
    for phrase in AI_FILLER:
        if phrase in text_lower:
            found_filler.append(phrase)

    results.append(CheckResult(
        "3.1 No AI filler phrases",
        len(found_filler) == 0,
        f"Found: {', '.join(found_filler)}" if found_filler else ""
    ))

    # Check for filler data
    found_filler_data = []
    for data in FILLER_DATA:
        if data.lower() in text_lower:
            found_filler_data.append(data)

    results.append(CheckResult(
        "3.2 No filler data",
        len(found_filler_data) == 0,
        f"Found: {', '.join(found_filler_data)}" if found_filler_data else ""
    ))

    return results


def check_image_references(readme, readme_path):
    """Check that all local image references point to existing files."""
    results = []
    readme_dir = os.path.dirname(os.path.abspath(readme_path))

    # Markdown image syntax
    img_pattern = re.compile(r"!\[[^\]]*\]\(([^)]+)\)")
    html_img_pattern = re.compile(r'<img[^>]+src=["\']([^"\']+)["\']')

    all_refs = img_pattern.findall(readme) + html_img_pattern.findall(readme)

    local_refs = [r for r in all_refs if not r.startswith("http")]

    if not local_refs:
        results.append(CheckResult(
            "3.3 Local image references valid",
            True,
            "No local images (N/A)"
        ))
        return results

    all_valid = True
    invalid = []
    for ref in local_refs:
        full_path = os.path.join(readme_dir, ref) if not os.path.isabs(ref) else ref
        if not os.path.exists(full_path):
            all_valid = False
            invalid.append(ref)

    results.append(CheckResult(
        "3.3 Local image references valid",
        all_valid,
        f"Missing: {', '.join(invalid)}" if invalid else f"{len(local_refs)} file(s) verified"
    ))

    return results


# ---------------------------------------------------------------------------
# Dimension 4: Diagram integrity
# ---------------------------------------------------------------------------

def find_editorial_static_assets(readme, readme_path):
    """Find local images published under assets/readme/diagrams/."""
    readme_dir = Path(readme_path).resolve().parent
    markdown_refs = re.findall(r"!\[[^\]]*\]\(([^)\s]+)", readme)
    html_refs = re.findall(r'<img[^>]+src=["\']([^"\']+)["\']', readme)
    assets = []

    for raw_ref in markdown_refs + html_refs:
        ref = raw_ref.strip().strip("<>")
        if ref.startswith(("http://", "https://", "//", "data:")):
            continue
        ref = ref.split("#", 1)[0].split("?", 1)[0]
        normalized = ref.replace("\\", "/").lstrip("./")
        if "assets/readme/diagrams/" not in normalized:
            continue
        path = Path(ref)
        full_path = path.resolve() if path.is_absolute() else (readme_dir / path).resolve()
        if full_path not in assets:
            assets.append(full_path)

    return assets


def archify_ir_path(asset):
    """Return the retained Archify IR path for a published diagram asset."""
    return asset.parent.parent / "source" / f"{asset.stem}.archify.json"


def is_archify_asset(asset):
    """Return True for Archify exports: marked SVG roots or assets with a retained IR."""
    if archify_ir_path(asset).is_file():
        return True
    if asset.suffix.lower() != ".svg" or not asset.is_file():
        return False
    content = asset.read_text(encoding="utf-8", errors="replace")
    svg_open = re.search(r"<svg\b[^>]*>", content, re.IGNORECASE | re.DOTALL)
    return bool(svg_open) and is_archify_export(svg_open.group(0))


def check_archify_diagrams(readme, readme_path):
    """Require a retained JSON IR beside every published Archify export."""
    assets = [
        asset for asset in find_editorial_static_assets(readme, readme_path)
        if is_archify_asset(asset)
    ]
    if not assets:
        return [CheckResult("4.13 Archify exports", True, "No Archify exports found (N/A)")]
    results = []
    for asset in assets:
        ir_path = archify_ir_path(asset)
        valid = False
        detail = f"Missing {ir_path}"
        if ir_path.is_file():
            try:
                ir = json.loads(ir_path.read_text(encoding="utf-8"))
                valid = isinstance(ir, dict) and bool(ir.get("diagram_type"))
                detail = "" if valid else "IR must be an object with diagram_type"
            except (OSError, UnicodeError, json.JSONDecodeError) as error:
                detail = str(error)[:120]
        results.append(CheckResult(f"4.13 Archify IR retained: {asset.name}", valid, detail))
    return results


def path_is_within(path, root):
    """Compatibility helper for checking repository-relative evidence paths."""
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def check_editorial_static_diagrams(readme, readme_path):
    """Validate editorial-static asset markers, manifests, and source evidence."""
    results = []
    assets = [
        asset for asset in find_editorial_static_assets(readme, readme_path)
        if not is_archify_asset(asset)
    ]
    if not assets:
        return [CheckResult(
            "4.8 Editorial-static assets",
            True,
            "No editorial-static assets found (N/A)"
        )]

    repo_root = Path(readme_path).resolve().parent
    for asset in assets:
        label = asset.name
        extension = asset.suffix.lower().lstrip(".")
        source_dir = asset.parent.parent / "source"
        manifest_path = source_dir / f"{asset.stem}.diagram.json"

        results.append(CheckResult(
            f"4.8 Editorial-static asset exists: {label}",
            asset.is_file(),
            "" if asset.is_file() else f"Missing {asset}"
        ))
        if not asset.is_file():
            continue

        results.append(CheckResult(
            f"4.9 Editorial-static manifest exists: {label}",
            manifest_path.is_file(),
            "" if manifest_path.is_file() else f"Missing {manifest_path}"
        ))
        if not manifest_path.is_file():
            continue

        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as error:
            results.append(CheckResult(
                f"4.10 Editorial-static manifest valid JSON: {label}",
                False,
                str(error)[:120]
            ))
            continue
        if not isinstance(manifest, dict):
            results.append(CheckResult(
                f"4.10 Editorial-static manifest contract: {label}",
                False,
                "manifest root must be an object"
            ))
            continue

        field_errors = []
        if manifest.get("schema_version") != 1:
            field_errors.append("schema_version must be 1")
        if manifest.get("engine") != "editorial-static":
            field_errors.append("engine must be editorial-static")
        if manifest.get("type") not in EDITORIAL_STATIC_TYPES:
            field_errors.append(f"unsupported type {manifest.get('type')!r}")
        if manifest.get("format") not in EDITORIAL_STATIC_FORMATS:
            field_errors.append(f"unsupported format {manifest.get('format')!r}")
        if manifest.get("format") != extension:
            field_errors.append(f"format {manifest.get('format')!r} does not match .{extension}")
        if manifest.get("size") not in EDITORIAL_STATIC_SIZES:
            field_errors.append(f"unsupported size {manifest.get('size')!r}")
        if manifest.get("detail") not in EDITORIAL_STATIC_DETAILS:
            field_errors.append(f"unsupported detail {manifest.get('detail')!r}")
        if manifest.get("audience") not in EDITORIAL_STATIC_AUDIENCES:
            field_errors.append(f"unsupported audience {manifest.get('audience')!r}")
        if not isinstance(manifest.get("source_backed"), bool):
            field_errors.append("source_backed must be boolean")

        counts = manifest.get("counts")
        if not isinstance(counts, dict):
            field_errors.append("counts must be an object")
        else:
            for key in ("nodes", "connectors", "focal", "zones"):
                value = counts.get(key)
                if not isinstance(value, int) or isinstance(value, bool) or value < 0:
                    field_errors.append(f"counts.{key} must be a non-negative integer")
            detail = manifest.get("detail")
            budget = EDITORIAL_STATIC_BUDGETS.get(detail)
            if budget and all(isinstance(counts.get(key), int) for key in ("nodes", "connectors")):
                if counts["nodes"] > budget["nodes"]:
                    field_errors.append(
                        f"{detail} node budget is {budget['nodes']}, got {counts['nodes']}"
                    )
                if counts["connectors"] > budget["connectors"]:
                    field_errors.append(
                        f"{detail} connector budget is {budget['connectors']}, got {counts['connectors']}"
                    )
            if isinstance(counts.get("focal"), int) and counts["focal"] > 2:
                field_errors.append(f"focal budget is 2, got {counts['focal']}")
            if (
                detail == "faithful"
                and isinstance(counts.get("nodes"), int)
                and counts["nodes"] > 9
                and (
                    not isinstance(counts.get("zones"), int)
                    or not 2 <= counts["zones"] <= 4
                )
            ):
                field_errors.append("faithful diagrams above 9 nodes need 2-4 zones")

        fidelity = manifest.get("fidelity")
        if not isinstance(fidelity, dict):
            field_errors.append("fidelity must be an object")
        else:
            for key in ("merged", "collapsed", "dropped"):
                if not isinstance(fidelity.get(key), list):
                    field_errors.append(f"fidelity.{key} must be an array")
                elif not all(
                    isinstance(item, str) and item.strip()
                    for item in fidelity[key]
                ):
                    field_errors.append(f"fidelity.{key} entries must be non-empty strings")

        results.append(CheckResult(
            f"4.10 Editorial-static manifest contract: {label}",
            not field_errors,
            "; ".join(field_errors)
        ))

        evidence = manifest.get("evidence")
        evidence_errors = []
        if not isinstance(evidence, list):
            evidence_errors.append("evidence must be an array")
            evidence = []
        if manifest.get("source_backed") is True and not evidence:
            evidence_errors.append("source-backed diagram needs at least one evidence entry")
        if manifest.get("source_backed") is False and evidence:
            evidence_errors.append("conceptual diagram must use an empty evidence array")

        for index, entry in enumerate(evidence, 1):
            if not isinstance(entry, dict):
                evidence_errors.append(f"evidence #{index} must be an object")
                continue
            evidence_path = entry.get("path")
            lines = entry.get("lines")
            if not isinstance(evidence_path, str) or not evidence_path.strip():
                evidence_errors.append(f"evidence #{index} needs path")
                continue
            candidate = (repo_root / evidence_path).resolve()
            candidate_exists = False
            if Path(evidence_path).is_absolute() or not path_is_within(candidate, repo_root):
                evidence_errors.append(f"evidence #{index} path escapes repository")
            elif not candidate.is_file():
                evidence_errors.append(f"evidence #{index} file not found: {evidence_path}")
            else:
                candidate_exists = True
            if not isinstance(lines, str) or not re.fullmatch(r"\d+(?:-\d+)?", lines):
                evidence_errors.append(f"evidence #{index} lines must be N or N-N")
            elif candidate_exists:
                start_text, _, end_text = lines.partition("-")
                start = int(start_text)
                end = int(end_text or start_text)
                try:
                    line_count = len(candidate.read_text(
                        encoding="utf-8", errors="replace"
                    ).splitlines())
                except OSError as error:
                    evidence_errors.append(
                        f"evidence #{index} file unreadable: {error}"
                    )
                    continue
                if start < 1 or end < start or end > line_count:
                    evidence_errors.append(
                        f"evidence #{index} lines {lines} outside 1-{line_count}"
                    )

        results.append(CheckResult(
            f"4.11 Editorial-static evidence resolves: {label}",
            not evidence_errors,
            "; ".join(evidence_errors)
        ))

        if extension == "svg":
            content = read_file(asset)
            marker_errors = []
            svg_open_match = re.search(
                r"<svg\b[^>]*>", content or "", re.IGNORECASE | re.DOTALL
            )
            svg_open = svg_open_match.group(0) if svg_open_match else ""
            if parse_svg_attribute(svg_open, "data-diagram-engine") != "editorial-static":
                marker_errors.append("missing data-diagram-engine=editorial-static")
            if parse_svg_attribute(svg_open, "data-readme-preset") != manifest.get("size"):
                marker_errors.append("data-readme-preset does not match manifest size")

            viewbox = parse_svg_attribute(svg_open, "viewBox")
            viewbox_match = re.fullmatch(
                r"\s*-?\d+(?:\.\d+)?\s+-?\d+(?:\.\d+)?\s+"
                r"(\d+(?:\.\d+)?)\s+(\d+(?:\.\d+)?)\s*",
                viewbox or "",
            )
            expected = EDITORIAL_STATIC_SIZES.get(manifest.get("size"))
            if not viewbox_match:
                marker_errors.append("viewBox is missing or invalid")
            elif expected:
                actual = (float(viewbox_match.group(1)), float(viewbox_match.group(2)))
                if any(abs(value - wanted) >= 1 for value, wanted in zip(actual, expected)):
                    marker_errors.append(
                        f"viewBox {actual[0]:g}×{actual[1]:g} does not match "
                        f"{manifest.get('size')} {expected[0]:g}×{expected[1]:g}"
                    )

            results.append(CheckResult(
                f"4.12 Editorial-static SVG markers/preset: {label}",
                not marker_errors,
                "; ".join(marker_errors)
            ))

    return results


def check_code_fences(readme):
    """Check code-fence diagram syntax for common errors."""
    results = []

    # Extract all fenced code blocks
    fence_pattern = re.compile(r"```(\w[\w-]*)\s*\n(.*?)```", re.DOTALL)
    fences = fence_pattern.findall(readme)

    # Track diagram engine fences
    engine_fences = {
        "plantuml": [],
        "vega": [],
        "vega-lite": [],
        "infographic": [],
        "canvas": [],
    }

    for lang, content in fences:
        lang_lower = lang.lower()
        if lang_lower in engine_fences:
            engine_fences[lang_lower].append(content)

    # PlantUML checks
    for i, content in enumerate(engine_fences["plantuml"]):
        has_start = "@startuml" in content or "@startmindmap" in content or "@startsalt" in content
        has_end = "@enduml" in content or "@endmindmap" in content or "@endsalt" in content
        results.append(CheckResult(
            f"4.1 PlantUML #{i+1} has @start directive",
            has_start,
            "" if has_start else "Missing @startuml/@startmindmap"
        ))
        results.append(CheckResult(
            f"4.2 PlantUML #{i+1} has @end directive",
            has_end,
            "" if has_end else "Missing @enduml/@endmindmap"
        ))

    # Vega/Vega-Lite checks
    for engine in ["vega", "vega-lite"]:
        for i, content in enumerate(engine_fences[engine]):
            has_schema = "$schema" in content
            results.append(CheckResult(
                f"4.3 {engine} #{i+1} has $schema",
                has_schema,
                "" if has_schema else "Missing $schema field"
            ))
            # Try JSON parse
            try:
                json.loads(content)
                results.append(CheckResult(
                    f"4.4 {engine} #{i+1} valid JSON",
                    True,
                    ""
                ))
            except json.JSONDecodeError as e:
                results.append(CheckResult(
                    f"4.4 {engine} #{i+1} valid JSON",
                    False,
                    str(e)[:80]
                ))

    # Infographic checks
    for i, content in enumerate(engine_fences["infographic"]):
        # Should not use colons in key-value pairs
        has_colon_syntax = bool(re.search(r"^\w+\s*:\s*\w+", content, re.MULTILINE))
        results.append(CheckResult(
            f"4.5 Infographic #{i+1} uses space-separated syntax",
            not has_colon_syntax,
            "Use 'key value' not 'key: value'" if has_colon_syntax else ""
        ))
        # Should use 'desc' not 'description'
        has_description = bool(re.search(r"^description\s+", content, re.MULTILINE))
        results.append(CheckResult(
            f"4.6 Infographic #{i+1} uses 'desc' not 'description'",
            not has_description,
            "Use 'desc' instead of 'description'" if has_description else ""
        ))
        # Should use 'items' not 'steps'
        has_steps = bool(re.search(r"^steps\s+", content, re.MULTILINE))
        results.append(CheckResult(
            f"4.7 Infographic #{i+1} uses 'items' not 'steps'",
            not has_steps,
            "Use 'items' instead of 'steps'" if has_steps else ""
        ))

    # If no diagram fences found
    total_diagrams = sum(len(v) for v in engine_fences.values())
    if total_diagrams == 0:
        results.append(CheckResult(
            "4.0 Diagram engine fences",
            True,
            "No code-fence diagrams found (N/A)"
        ))

    return results


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Verify README compliance for beautify-readme skill")
    parser.add_argument("readme", help="Path to README.md file")
    parser.add_argument("--svg-dir", help="Additional directory to scan for SVG files", default=None)
    args = parser.parse_args()

    readme_path = args.readme
    readme = read_file(readme_path)

    if readme is None:
        print(f"ERROR: Cannot read {readme_path}")
        sys.exit(1)

    print(f"README: {os.path.abspath(readme_path)}")
    print()

    all_results = []

    # Dimension 1: Content architecture
    print("Dimension 1 — Content architecture")
    print("-" * 50)
    d1 = (
        check_content_sections(readme)
        + check_content_sequence(readme)
        + check_alt_text(readme)
        + check_mechanism_visualization(readme)
    )
    all_results.extend(d1)
    for r in d1:
        print(r)
    print()

    # Dimension 2: Visual system
    print("Dimension 2 — Visual system")
    print("-" * 50)
    svg_files = find_svg_files(readme, readme_path, args.svg_dir)
    d2 = check_svg_files(svg_files, readme_path)
    all_results.extend(d2)
    for r in d2:
        print(r)
    print()

    # Dimension 3: Quality bar
    print("Dimension 3 — Quality bar")
    print("-" * 50)
    d3 = check_ai_filler(readme) + check_image_references(readme, readme_path)
    all_results.extend(d3)
    for r in d3:
        print(r)
    print()

    # Dimension 4: Diagram integrity
    print("Dimension 4 — Diagram integrity")
    print("-" * 50)
    d4 = (
        check_code_fences(readme)
        + check_editorial_static_diagrams(readme, readme_path)
        + check_archify_diagrams(readme, readme_path)
    )
    all_results.extend(d4)
    for r in d4:
        print(r)
    print()

    # Summary
    passed = sum(1 for r in all_results if r.passed)
    failed = sum(1 for r in all_results if not r.passed)
    total = len(all_results)

    print("=" * 50)
    print(f"Programmatic checks: {passed} passed, {failed} failed, {total} total")

    if failed == 0:
        print("Overall: PASS")
        print()
        print("NOTE: Manual checks from references/output-verification.md must also pass.")
        print("      This script covers only programmatically verifiable items.")
        sys.exit(0)
    else:
        print("Overall: FAIL — fix the gaps above before declaring complete.")
        print()
        print("See references/output-verification.md for the full checklist.")
        sys.exit(1)


if __name__ == "__main__":
    main()
