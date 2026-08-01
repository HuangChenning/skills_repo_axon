#!/usr/bin/env python3
"""Programmatic README compliance checker for the beautify-readme skill.

Checks four dimensions that can be verified without human judgment:
  1. Content architecture — sections, install path, alt text
  2. Visual system — SVG structure, legible text, no fragile features
  3. Quality bar — AI filler phrases, pure black, meaningful alt text
  4. Diagram engine syntax — fence names, PlantUML/Vega/Infographic basics

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
        "proof", "demo", "example", "screenshot", "showcase", "benchmark", "result",
        "示例", "演示", "截图", "效果", "展示",
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
    # Match ![alt](src) patterns
    img_pattern = re.compile(r"!\[([^\]]*)\]\(([^)]+)\)")
    matches = img_pattern.findall(readme)

    if not matches:
        results.append(CheckResult(
            "1.6 Images have alt text",
            True,
            "No images found (N/A)"
        ))
        return results

    for alt, src in matches:
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

        # Check viewBox width is 1200 for full-width SVGs
        vb_match = re.search(r'viewBox=["\'](\d+(?:\.\d+)?)\s+(\d+(?:\.\d+)?)\s+(\d+(?:\.\d+)?)\s+(\d+(?:\.\d+)?)["\']', content)
        if vb_match:
            vb_width = float(vb_match.group(3))
            has_1200 = abs(vb_width - 1200) < 1
            results.append(CheckResult(
                f"2.3 viewBox width 1200: {basename}",
                has_1200,
                f"width={vb_width}" if not has_1200 else ""
            ))
        else:
            results.append(CheckResult(
                f"2.3 viewBox width 1200: {basename}",
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
        if re.search(r'@font-face|@import', content):
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
# Dimension 4: Diagram engine syntax
# ---------------------------------------------------------------------------

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
    d1 = check_content_sections(readme) + check_content_sequence(readme) + check_alt_text(readme)
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

    # Dimension 4: Diagram engine syntax
    print("Dimension 4 — Diagram engine syntax")
    print("-" * 50)
    d4 = check_code_fences(readme)
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
