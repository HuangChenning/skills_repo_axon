#!/usr/bin/env python3
"""Generate / refresh ~/.axon/README.md catalog from repo/skills and repo/workflows.

Usage (from ~/.axon or anywhere):
  python3 repo/scripts/generate_readme.py
  python3 repo/scripts/generate_readme.py --dry-run
  python3 repo/scripts/generate_readme.py --catalog-only
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from datetime import date
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
REPO = SCRIPT_DIR.parent
AXON = REPO.parent
SKILLS = REPO / "skills"
WORKFLOWS = REPO / "workflows"
README = AXON / "README.md"
ZH_CATALOG = SCRIPT_DIR / "zh_catalog.json"

MARKER_START = "<!-- AUTO:CATALOG:START -->"
MARKER_END = "<!-- AUTO:CATALOG:END -->"
LINK_PREFIX = "repo/"  # README lives at ~/.axon/, skills under repo/

CATEGORIES: list[tuple[str, str, list[str]]] = [
    (
        "diagrams",
        "图表 / 架构可视化",
        [
            "anthropic-diagram",
            "archimate",
            "architecture",
            "architecture-diagram",
            "bpmn",
            "canvas",
            "cloud",
            "data-analytics",
            "drawio",
            "graphviz",
            "infocard",
            "infographic",
            "iot",
            "mindmap",
            "network",
            "security",
            "uml",
            "vega",
        ],
    ),
    (
        "design",
        "设计 / README / 视觉产出",
        [
            "awesome-design-md",
            "beautify-github-readme",
            "beautify-readme",
            "canvas-design",
            "card-skill",
            "frontend-design",
            "huashu-design",
            "imagegen",
        ],
    ),
    (
        "office",
        "办公文档",
        ["docx", "pdf", "pptx", "xlsx"],
    ),
    (
        "adk",
        "Google ADK Agent 开发",
        [
            "adk-cheatsheet",
            "adk-deploy-guide",
            "adk-dev-guide",
            "adk-eval-guide",
            "adk-observability-guide",
            "adk-scaffold",
        ],
    ),
    (
        "git",
        "Git / GitHub 协作",
        [
            "git-commit-message",
            "git-pr-cleanup",
            "git-pr-creator",
            "git-release",
            "git-upstream-sync",
            "github-actions-debugging",
            "github-issues",
            "github-pr-reply-advisor",
            "pr-comments-analyzer",
            "receiving-code-review",
            "requesting-code-review",
        ],
    ),
    (
        "agent",
        "Agent Skills 生态 / 通用能力",
        [
            "book-to-skill",
            "claude-api",
            "code-simplifier",
            "eli5",
            "find-skills",
            "mcp-builder",
            "openai-docs",
            "planning-with-files",
            "skill-creator",
            "skills-discovery",
            "linear",
        ],
    ),
    (
        "mes",
        "MES / 内部业务",
        [
            "gemini-code-assist-check",
            "low-hour-report",
            "mes-cli-terminal",
            "mes-weekly-report",
        ],
    ),
    (
        "lang",
        "语言 / 知识蒸馏",
        ["cangjie-skill"],
    ),
    (
        "collections",
        "技能合集（含子 Skill）",
        [
            "humanlayer-skills",
            "mattpocock-skills",
            "mopheus-skills",
            "obsidian-skills",
            "openai",
            "superpowers",
        ],
    ),
]

BUNDLES = [
    "humanlayer-skills",
    "mattpocock-skills",
    "mopheus-skills",
    "obsidian-skills",
    "openai",
    "superpowers",
]


def load_zh() -> dict[str, str]:
    if not ZH_CATALOG.exists():
        return {}
    return json.loads(ZH_CATALOG.read_text(encoding="utf-8"))


def extract_frontmatter(text: str) -> tuple[str | None, str | None]:
    if not text.startswith("---"):
        return None, None
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n", text, re.S)
    if not m:
        return None, None
    fm = m.group(1)
    name = None
    nm = re.search(r"^name:\s*(.+)$", fm, re.M)
    if nm:
        name = nm.group(1).strip().strip("\"'")
    desc = None
    dm = re.search(r"^description:\s*(\||>)?\s*(.*)$", fm, re.M)
    if dm:
        if dm.group(1):
            lines = fm.splitlines()
            collecting = False
            parts: list[str] = []
            for line in lines:
                if re.match(r"^description:\s*(\||>)?", line):
                    collecting = True
                    rest = re.sub(r"^description:\s*(\||>)?\s*", "", line)
                    if rest:
                        parts.append(rest)
                    continue
                if collecting:
                    if re.match(r"^[a-zA-Z_][\w-]*:", line) and not line.startswith(" "):
                        break
                    parts.append(line.strip())
            desc = " ".join(p for p in parts if p).strip()
        else:
            desc = dm.group(2).strip().strip("\"'")
    return name, desc


def first_heading_para(text: str) -> tuple[str | None, str]:
    heading = None
    for line in text.splitlines():
        if line.startswith("# "):
            heading = line[2:].strip()
            break
    first_para = ""
    after = False
    for line in text.splitlines():
        if line.startswith("# "):
            after = True
            continue
        if after:
            if line.startswith("#"):
                break
            if line.strip() and line.strip() != "---":
                first_para = line.strip()
                break
    return heading, first_para


def shorten(s: str, n: int = 140) -> str:
    s = re.sub(r"\s+", " ", (s or "")).strip()
    if len(s) <= n:
        return s
    return s[: n - 1] + "…"


def esc(s: str) -> str:
    return (s or "").replace("|", "\\|")


def skill_desc(path: str, en: str, zh_map: dict[str, str]) -> str:
    if path in zh_map:
        return zh_map[path]
    if re.search(r"[\u4e00-\u9fff]", en):
        return shorten(en)
    # fallback: keep English but warn via marker
    return shorten(en) + " 〔待译〕"


def collect_skills(zh_map: dict[str, str]) -> list[dict]:
    skills: list[dict] = []
    for skill_md in sorted(SKILLS.rglob("SKILL.md")):
        rel = skill_md.relative_to(SKILLS)
        top = rel.parts[0]
        text = skill_md.read_text(encoding="utf-8", errors="replace")
        name, desc = extract_frontmatter(text)
        heading, para = first_heading_para(text)
        name = name or heading or rel.parent.name
        path = str(rel.parent).replace("\\", "/")
        en = shorten(desc or para or "", 200)
        skills.append(
            {
                "path": path,
                "top": top,
                "name": name,
                "desc": skill_desc(path, en, zh_map),
                "is_system": top.startswith("."),
            }
        )
    return skills


def collect_workflows(zh_map: dict[str, str]) -> list[tuple[str, str]]:
    rows: list[tuple[str, str]] = []
    if not WORKFLOWS.is_dir():
        return rows
    for f in sorted(WORKFLOWS.glob("*.md")):
        key = f"workflow:{f.name}"
        if key in zh_map:
            desc = zh_map[key]
        else:
            text = f.read_text(encoding="utf-8", errors="replace")
            m = re.search(r"^description:\s*(.+)$", text, re.M)
            en = m.group(1).strip() if m else ""
            desc = skill_desc(key, en, {})
        rows.append((f.name, shorten(desc, 160)))
    return rows


def href(rel: str) -> str:
    return f"{LINK_PREFIX}{rel}"


def table_for_tops(tops: list[str], by_top: dict) -> str:
    lines = ["| 目录 | Skill | 用途 |", "| --- | --- | --- |"]
    for t in tops:
        items = by_top.get(t, [])
        if not items:
            if t == "awesome-design-md" and (SKILLS / t).exists():
                n = len(list((SKILLS / t).iterdir()))
                lines.append(
                    f"| [`{t}`]({href(f'skills/{t}/')}) | （设计参考包，无 SKILL.md） | "
                    f"品牌/产品 design-md 合集（约 {n} 个条目），供设计风格参考 |"
                )
            else:
                lines.append(
                    f"| [`{t}`]({href(f'skills/{t}/')}) | — | （暂无 SKILL.md） |"
                )
            continue
        if len(items) == 1 and items[0]["path"] == t:
            it = items[0]
            lines.append(
                f"| [`{t}`]({href(f'skills/{t}/')}) | `{esc(it['name'])}` | {esc(it['desc'])} |"
            )
        else:
            lines.append(
                f"| [`{t}`]({href(f'skills/{t}/')}) | **合集 · {len(items)} 个子 Skill** | 见下方「合集明细」 |"
            )
    return "\n".join(lines)


def bundle_detail(top: str, by_top: dict) -> str:
    items = sorted(by_top.get(top, []), key=lambda x: x["path"])
    if not items:
        return ""
    lines = [
        f"#### `{top}`（{len(items)}）",
        "",
        "| 路径 | 名称 | 用途 |",
        "| --- | --- | --- |",
    ]
    for it in items:
        lines.append(
            f"| [`{it['path']}`]({href(f'skills/{it['path']}/')}) | `{esc(it['name'])}` | {esc(it['desc'])} |"
        )
    return "\n".join(lines)


def build_catalog(skills: list[dict], workflows: list[tuple[str, str]]) -> str:
    by_top: dict[str, list] = defaultdict(list)
    for s in skills:
        by_top[s["top"]].append(s)

    user_skills = [s for s in skills if not s["is_system"]]
    top_dirs = sorted(
        p.name for p in SKILLS.iterdir() if p.is_dir() and not p.name.startswith(".")
    )
    no_skill = [t for t in top_dirs if not list((SKILLS / t).rglob("SKILL.md"))]
    assigned: set[str] = set()
    for _, _, items in CATEGORIES:
        assigned.update(items)
    unassigned = [t for t in top_dirs if t not in assigned and t not in no_skill]
    leftover_no_skill = [t for t in no_skill if t not in assigned]
    sys_items = by_top.get(".system", [])

    parts: list[str] = []
    parts.append(
        f"> 自动生成于 {date.today().isoformat()} · Skill 文件 `{len(user_skills)}` 个 · "
        f"顶层目录 `{len(top_dirs)}` 个 · Workflow `{len(workflows)}` 个"
    )
    parts.append("")
    parts.append("### 分类一览")
    parts.append("")

    for _, title, tops in CATEGORIES:
        existing = [t for t in tops if (SKILLS / t).exists()]
        if not existing:
            continue
        parts.append(f"#### {title}")
        parts.append("")
        parts.append(table_for_tops(existing, by_top))
        parts.append("")

    if unassigned:
        parts.append("#### 未分类")
        parts.append("")
        parts.append(table_for_tops(unassigned, by_top))
        parts.append("")

    if leftover_no_skill:
        parts.append("#### 无 SKILL.md 的目录")
        parts.append("")
        parts.append(table_for_tops(leftover_no_skill, by_top))
        parts.append("")

    parts.append("### 合集明细")
    parts.append("")
    for top in BUNDLES:
        if (SKILLS / top).exists():
            detail = bundle_detail(top, by_top)
            if detail:
                parts.append(detail)
                parts.append("")

    if sys_items:
        parts.append("### 系统内置（`skills/.system`）")
        parts.append("")
        parts.append("| 路径 | 名称 | 用途 |")
        parts.append("| --- | --- | --- |")
        for it in sorted(sys_items, key=lambda x: x["path"]):
            parts.append(
                f"| `{it['path']}` | `{esc(it['name'])}` | {esc(it['desc'])} |"
            )
        parts.append("")

    parts.append("### Workflows")
    parts.append("")
    parts.append("| 文件 | 用途 |")
    parts.append("| --- | --- |")
    for name, desc in workflows:
        parts.append(f"| [`{name}`]({href(f'workflows/{name}')}) | {esc(desc)} |")
    parts.append("")
    return "\n".join(parts)


def maintenance_footer() -> str:
    return """- 新增独立 skill：放到 `repo/skills/<skill-name>/SKILL.md`（YAML frontmatter 必须含 `name` 与 `description`）。
- 新增中文用途：在 `repo/scripts/zh_catalog.json` 增加对应路径条目（否则 README 会显示英文并标「待译」）。
- 新增合集：放到 `repo/skills/<bundle>/.../SKILL.md`，并在 `generate_readme.py` 的 `CATEGORIES` 里归类（可选）。
- 新增 workflow：放到 `repo/workflows/<name>.md`，并在 `zh_catalog.json` 增加 `workflow:<name>.md`。
- 不要手改 AUTO 标记之间的表格；改分类或中文释义后重新运行生成脚本。
"""


def build_intro(skills: list[dict], workflows: list[tuple[str, str]]) -> str:
    user_skills = [s for s in skills if not s["is_system"]]
    top_dirs = sorted(
        p.name for p in SKILLS.iterdir() if p.is_dir() and not p.name.startswith(".")
    )
    sys_count = sum(1 for s in skills if s["is_system"])
    return f"""# Axon Skills Hub

本文件是 Axon 本地 Hub（`~/.axon`）的总览：内容存放在 `repo/`，通过 `axon.yaml` 同步到 Cursor / Claude Code / Codex / Gemini 等多端工具目录。

**一句话**：这里是个人/团队的「技能与工作流仓库」——不是业务应用代码，而是给 AI Agent 用的可复用能力包。

## 目录结构

```text
~/.axon/
├── README.md          # 本文件（总览与目录）
├── axon.yaml          # 同步目标与 vendors 镜像配置
└── repo/
    ├── skills/        # Agent Skills（每个子目录通常含 SKILL.md）
    ├── workflows/     # 多步骤工作流
    ├── commands/      # 自定义斜杠命令（可为空）
    └── scripts/       # 维护脚本（含 README 目录自动生成）
```

## 有什么用

| 类型 | 作用 |
| --- | --- |
| **Skill** | 告诉 Agent「遇到某类任务时按什么规范/流程做」；触发词写在 `SKILL.md` 的 `description` 里 |
| **Workflow** | 固定多步作业流程（审代码、发版、依赖升级、安全审计等），偏「跑一遍 checklist」 |
| **合集目录** | 如 `openai/`、`superpowers/`、`mattpocock-skills/`，一个顶层目录下挂多个子 Skill |

同步目标（节选，完整见 `axon.yaml`）：

- `~/.cursor/skills`、`~/.claude/skills`、`~/.codex/skills`、`~/.gemini/skills` …
- Workflows → Antigravity / Windsurf 的 global workflows

上游镜像源也可在 `axon.yaml` 的 `vendors:` 中配置（从 GitHub 拉取第三方 skill 到本 Hub）。

## 快速查找

1. 先看下方「分类一览」，按场景定位顶层目录。
2. 打开对应 `repo/skills/<name>/SKILL.md` 阅读触发条件与用法。
3. 合集类再往下翻「合集明细」。
4. 固定工程流程看 `repo/workflows/`。

## 持续更新 README（新增 Skill 后）

在 `~/.axon` 下执行：

```bash
python3 repo/scripts/generate_readme.py
```

脚本会：

1. 扫描全部 `SKILL.md` 的 `name` / `description`
2. 用 `repo/scripts/zh_catalog.json` 把「用途」写成中文
3. 扫描 `workflows/*.md`
4. 重写本文件中 AUTO 目录标记（`AUTO:CATALOG:START` / `END`）之间的表格

也可：

```bash
python3 repo/scripts/generate_readme.py --dry-run       # 只预览
python3 repo/scripts/generate_readme.py --catalog-only  # 只刷新目录表，保留手写前言
```

> 建议：每次 `axon sync` 拉入新 skill 后，先补 `zh_catalog.json` 中文释义，再跑生成脚本。

## 统计快照

- 顶层 skill 目录：{len(top_dirs)}
- `SKILL.md` 数量（不含 `.system`）：{len(user_skills)}
- Workflows：{len(workflows)}
- 系统内置 skill（`.system`）：{sys_count}

---

"""


def render_full(skills: list[dict], workflows: list[tuple[str, str]], catalog: str) -> str:
    return (
        build_intro(skills, workflows)
        + MARKER_START
        + "\n"
        + catalog
        + MARKER_END
        + "\n\n## 维护约定\n\n"
        + maintenance_footer()
    )


def upsert_readme(full_text: str, dry_run: bool) -> None:
    if dry_run:
        print(full_text)
        return
    README.write_text(full_text, encoding="utf-8")
    print(f"Wrote {README} ({README.stat().st_size} bytes)", file=sys.stderr)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="Print README to stdout")
    parser.add_argument(
        "--catalog-only",
        action="store_true",
        help="Only refresh AUTO catalog markers if README already exists",
    )
    args = parser.parse_args()

    if not SKILLS.is_dir():
        print(f"skills directory not found: {SKILLS}", file=sys.stderr)
        return 1

    zh_map = load_zh()
    skills = collect_skills(zh_map)
    workflows = collect_workflows(zh_map)
    catalog = build_catalog(skills, workflows)

    pending = sum(1 for s in skills if "〔待译〕" in s["desc"])
    if pending:
        print(f"warning: {pending} skill(s) missing Chinese in zh_catalog.json", file=sys.stderr)

    if args.catalog_only and README.exists():
        text = README.read_text(encoding="utf-8")
        start = text.find(MARKER_START)
        end = text.find(MARKER_END, start + len(MARKER_START)) if start >= 0 else -1
        if start < 0 or end < 0:
            print("Markers not found; regenerating full README", file=sys.stderr)
            full = render_full(skills, workflows, catalog)
        else:
            before = text[:start]
            after = text[end + len(MARKER_END) :]
            full = before + MARKER_START + "\n" + catalog + MARKER_END + after
            user_n = sum(1 for s in skills if not s["is_system"])
            top_n = len(
                [p for p in SKILLS.iterdir() if p.is_dir() and not p.name.startswith(".")]
            )
            sys_n = sum(1 for s in skills if s["is_system"])
            full = re.sub(r"(- 顶层 skill 目录：)\d+", rf"\g<1>{top_n}", full, count=1)
            full = re.sub(
                r"(- `SKILL\.md` 数量（不含 `\.system`）：)\d+",
                rf"\g<1>{user_n}",
                full,
                count=1,
            )
            full = re.sub(r"(- Workflows：)\d+", rf"\g<1>{len(workflows)}", full, count=1)
            full = re.sub(
                r"(- 系统内置 skill（`\.system`）：)\d+",
                rf"\g<1>{sys_n}",
                full,
                count=1,
            )
    else:
        full = render_full(skills, workflows, catalog)

    upsert_readme(full, args.dry_run)
    user_n = sum(1 for s in skills if not s["is_system"])
    print(
        f"skills={user_n} workflows={len(workflows)} "
        f"system={sum(1 for s in skills if s['is_system'])} zh={len(zh_map)}",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
