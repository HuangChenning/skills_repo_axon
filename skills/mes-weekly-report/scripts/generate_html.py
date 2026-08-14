#!/usr/bin/env python3
"""
生成周报汇总 HTML 报告。
用法：
  python generate_html.py --from 2026-07-06 --to 2026-07-12
  python generate_html.py  # 默认上周一~上周日
"""

import argparse
import html as html_mod
import json
import os
import re
import subprocess
import sys
from datetime import date, timedelta
from pathlib import Path


# ── helpers ──────────────────────────────────────────────

def run_mes(cmd: list[str]) -> dict:
    full_cmd = ["mes", "-o", "json"] + cmd
    try:
        result = subprocess.run(full_cmd, capture_output=True, text=True, timeout=30)
    except FileNotFoundError:
        print("[ERROR] 未找到 'mes' 命令，请确保已安装 mes CLI 并将其添加到 PATH。", file=sys.stderr)
        return {}
    except subprocess.TimeoutExpired:
        print(f"[ERROR] mes 命令超时: {' '.join(full_cmd)}", file=sys.stderr)
        return {}
    if result.returncode != 0:
        print(f"[ERROR] mes 命令执行失败 (exit code {result.returncode}):\n{result.stderr}", file=sys.stderr)
        return {}
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return {}


def strip_html(html_text: str) -> str:
    if not html_text:
        return ""
    text = re.sub(r'<br\s*/?>', '\n', html_text)
    text = re.sub(r'</(?:p|div|h\d|li|tr|section|article|blockquote)>', '\n', text)
    text = re.sub(r'<[^>]+>', '', text)
    text = html_mod.unescape(text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


def sanitize_html(html_text: str) -> str:
    """移除危险标签和属性，保留安全的结构化标签。"""
    if not html_text:
        return ""
    for tag in ('script', 'style', 'iframe', 'object', 'embed'):
        html_text = re.sub(rf'<{tag}[^>]*>.*?</{tag}>', '', html_text, flags=re.DOTALL | re.IGNORECASE)
    html_text = re.sub(r'\s+on\w+\s*=\s*"[^"]*"', '', html_text)
    html_text = re.sub(r"\s+on\w+\s*=\s*'[^']*'", '', html_text)
    html_text = re.sub(r'\s+style\s*=\s*"[^"]*"', '', html_text)
    html_text = re.sub(r"\s+style\s*=\s*'[^']*'", '', html_text)
    html_text = re.sub(r'href\s*=\s*"[^"]*javascript:', 'href="#"', html_text, flags=re.IGNORECASE)
    return html_text


def last_week_dates() -> tuple[str, str]:
    today = date.today()
    last_monday = today - timedelta(days=today.weekday() + 7)
    last_sunday = last_monday + timedelta(days=6)
    return last_monday.isoformat(), last_sunday.isoformat()
    today = date.today()
    last_monday = today - timedelta(days=today.weekday() + 7)
    last_sunday = last_monday + timedelta(days=6)
    return last_monday.isoformat(), last_sunday.isoformat()


def _has_markdown_syntax(html_text: str) -> bool:
    """检测 HTML 中是否嵌入了 Markdown 标记（如 # 标题、**粗体**）。"""
    return bool(re.search(r'(?:<p>|>)\s*#{1,3}\s', html_text)) or '**' in html_text


def content_to_display_html(content_html: str) -> str:
    """将 MES 周报内容转为安全的展示 HTML。

    双路径策略：
    - 纯 HTML 报告：清洗后直接保留结构化标签
    - 内嵌 Markdown 报告：先转义再按 Markdown 重新构建 HTML
    """
    if not content_html:
        return ""
    cleaned = sanitize_html(content_html)
    if _has_markdown_syntax(cleaned):
        # Markdown 内嵌：剥离 HTML → 转义防 XSS → Markdown → 干净 HTML
        plain = strip_html(cleaned)
        safe = html_escape(plain)
        return _markdown_plain_to_html(safe)
    else:
        # 纯 HTML：已清洗，直接使用
        return cleaned


def _markdown_plain_to_html(text: str) -> str:
    """将纯文本中的 Markdown 语法转为 HTML。"""
    lines = text.split('\n')
    out = []
    list_type = None
    para_lines = []

    def close_list():
        nonlocal list_type
        if list_type:
            out.append(f'</{list_type}>')
            list_type = None

    def flush_para():
        if para_lines:
            content = ' '.join(para_lines)
            out.append(f'<p>{_convert_inline_md(content)}</p>')
            para_lines.clear()

    for line in lines:
        stripped = line.strip()

        if not stripped:
            close_list()
            flush_para()
            out.append('')
            continue

        m = re.match(r'^(#{1,3})\s+(.+)', stripped)
        if m:
            close_list()
            flush_para()
            level = len(m.group(1))
            out.append(f'<h{level}>{_convert_inline_md(m.group(2))}</h{level}>')
            continue

        m = re.match(r'^[-*]\s+(.+)', stripped)
        if m:
            flush_para()
            if list_type != 'ul':
                close_list()
                out.append('<ul>')
                list_type = 'ul'
            out.append(f'<li>{_convert_inline_md(m.group(1))}</li>')
            continue

        # 有序列表：1、1）1)  或  1. + 空格（避免误匹配日期 2026.07.14）
        m = re.match(r'^\d+[、)]\s*(.+)', stripped)
        if not m:
            m = re.match(r'^\d+\.\s+(.+)', stripped)
        if m:
            flush_para()
            if list_type != 'ol':
                close_list()
                out.append('<ol>')
                list_type = 'ol'
            out.append(f'<li>{_convert_inline_md(m.group(1))}</li>')
            continue

        close_list()
        para_lines.append(stripped)

    close_list()
    flush_para()
    return '\n'.join(out)


def _convert_inline_md(text: str) -> str:
    """转换行内 Markdown：**粗体**、*斜体*。"""
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    text = re.sub(r'\*(.+?)\*', r'<em>\1</em>', text)
    return text


def html_escape(text: str) -> str:
    return html_mod.escape(text, quote=False)


# ── data fetching ────────────────────────────────────────

def fetch_person_report(name: str, from_date: str, to_date: str) -> dict | None:
    """拉取单人周报，返回 {name, team, createdTime, content_text, report_id} 或 None。"""
    data = run_mes([
        "dashboard", "weeklyReport",
        "--creator", name,
        "--period-from", from_date,
        "--period-to", to_date,
        "--type", "WEEKLY",
        "--json",
    ])
    reports = data.get("list", [])
    if not reports:
        return None
    r = reports[0]

    # view 获取完整正文
    rid = r.get("id")
    full_html = r.get("content") or ""
    if rid:
        detail = run_mes(["dashboard", "weeklyReport", "view", str(rid)])
        obj = detail.get("operateCallBackObj", {}) if isinstance(detail, dict) else {}
        full_html = obj.get("content") or full_html

    return {
        "name": name,
        "team": r.get("adminTeamName") or "",
        "createdTime": r.get("createdTime", ""),
        "content_html": full_html,
        "content_text": strip_html(full_html),
        "report_id": rid,
    }


# ── risk extraction ──────────────────────────────────────

def extract_risks_from_html(raw_html: str, content_text: str, author: str, team: str) -> list[dict]:
    """从周报 HTML 中提取风险项。返回 [{author, team, source, text, level}]。"""
    risks = []

    # 目标章节 → (来源标签, 风险等级)
    target_sections = {
        "交付风险反馈": ("交付风险", "red"),
        "收入风险反馈": ("收入风险", "amber"),
        "需要升级的问题": ("需升级", "red"),
    }

    # 方案：在原始 HTML 中按 <h1> 标签拆分章节
    # <h1 ...>章节名</h1>
    # 仅按 <h1> 拆分顶级章节；子标题 (<h2>/<h3>) 保留在章节正文中
    section_pattern = re.compile(
        r'<h1[^>]*>\s*(.+?)\s*</h1>\s*(.*?)(?=<h1[^>]*>|$)',
        re.DOTALL | re.IGNORECASE,
    )

    for m in section_pattern.finditer(raw_html):
        heading = strip_html(m.group(1)).strip()
        body_html = m.group(2).strip()

        # 匹配目标章节
        matched = None
        for key, (label, level) in target_sections.items():
            if key in heading:
                matched = (label, level)
                break
        if not matched:
            continue

        source_label, level = matched

        # 提取正文纯文本
        body_text = strip_html(body_html)

        # 跳过空/无意义内容
        if not body_text or body_text in ('...', '无', '...', ''):
            continue

        # 拆分为独立条目（支持数字序号和无序列表符号）
        # 拆分条目：数字序号（1、1）1) 或 1. + 空格） + 无序列表符号
        items = re.split(r'\n(?=(?:\d+[、)]|\d+\.\s+|[-*•])\s*)', body_text)
        for item in items:
            item = item.strip()
            if not item or len(item) < 8 or item in ('...', '无'):
                continue
            item = re.sub(r'^(?:\d+[、)]|\d+\.\s+|[-*•])\s*', '', item)
            risks.append({
                "author": author, "team": team,
                "source": source_label, "text": item[:300], "level": level,
            })

    return risks


# ── HTML generation ──────────────────────────────────────

def build_html(template: str, data: dict) -> str:
    """简单模板替换（{{KEY}} → value）。"""
    for key, value in data.items():
        template = template.replace("{{" + key + "}}", str(value))
    return template


def main():
    parser = argparse.ArgumentParser(description="生成 MES 周报汇总 HTML")
    default_from, default_to = last_week_dates()
    parser.add_argument("--from", dest="from_date", default=default_from)
    parser.add_argument("--to", dest="to_date", default=default_to)
    parser.add_argument("--people-file", default=None)
    parser.add_argument("--output", default=None)
    parser.add_argument("--template", default=None)
    args = parser.parse_args()

    # 路径
    script_dir = os.path.dirname(os.path.abspath(__file__))
    skill_dir = os.path.dirname(script_dir)
    people_file = args.people_file or os.path.join(skill_dir, "people.json")
    template_file = args.template or os.path.join(skill_dir, "templates", "weekly-report.html")

    if not os.path.exists(people_file):
        print(f"[ERROR] 人员清单不存在: {people_file}", file=sys.stderr)
        sys.exit(1)
    if not os.path.exists(template_file):
        print(f"[ERROR] 模版不存在: {template_file}", file=sys.stderr)
        sys.exit(1)

    try:
        with open(people_file, "r", encoding="utf-8") as f:
            config = json.load(f)
    except json.JSONDecodeError as e:
        print(f"[ERROR] 人员清单 JSON 格式错误: {e}", file=sys.stderr)
        sys.exit(1)

    with open(template_file, "r", encoding="utf-8") as f:
        template = f.read()

    people = config.get("people", [])
    if not people:
        print("[ERROR] 人员清单为空", file=sys.stderr)
        sys.exit(1)

    print(f"拉取 {len(people)} 人周报  {args.from_date} ~ {args.to_date}")

    # 拉取数据
    submitted = []
    missing = []
    all_risks = []

    for person in people:
        name = person.get("name")
        if not name:
            print("  [WARN] 发现未配置姓名的记录，跳过", file=sys.stderr)
            continue
        print(f"  {name}...", end=" ", flush=True)
        report = fetch_person_report(name, args.from_date, args.to_date)
        if report:
            report["role"] = person.get("role", "")
            print(f"✓ {len(report['content_text'])}字")
            submitted.append(report)
            # 提取风险（使用原始 HTML）
            risks = extract_risks_from_html(
                report["content_html"],
                report["content_text"],
                name,
                report["team"] or person.get("team", ""),
            )
            all_risks.extend(risks)
        else:
            missing.append(person)
            print("✗")

    total = len(people)
    submitted_count = len(submitted)
    missing_count = len(missing)
    submission_rate = round(submitted_count / total * 100) if total else 0

    # ── 构建模板变量 ──

    # Hero
    date_range = f"{args.from_date}  ~  {args.to_date}"
    generated_at = date.today().isoformat()

    # 未提交 strip
    if missing:
        names_html = "".join(
            f'<span class="unsubmitted-name">{html_escape(p.get("name", ""))}</span>'
            for p in missing
        )
        unsubmitted_hidden = ""
    else:
        names_html = ""
        unsubmitted_hidden = "hidden"

    # 风险卡片 — 按人聚合
    if all_risks:
        # 按 author 分组
        grouped: dict[str, dict] = {}
        for r in all_risks:
            key = r["author"]
            if key not in grouped:
                grouped[key] = {"team": r["team"], "risks": []}
            grouped[key]["risks"].append(r)

        risk_cards_html = ""
        for author, grp in grouped.items():
            team_str = f" · {html_escape(grp['team'])}" if grp["team"] else ""
            # 取最高风险等级决定卡片左边框颜色
            has_red = any(r["level"] == "red" for r in grp["risks"])
            level_class = "" if has_red else "amber"

            items_html = ""
            for r in grp["risks"]:
                items_html += f"""        <div class="risk-item">
          <span class="risk-item-source">{r['source']}</span>
          <span class="risk-item-text">{html_escape(r['text'])}</span>
        </div>
"""

            risk_cards_html += f"""    <div class="risk-card {level_class}">
      <div class="risk-indicator"></div>
      <div class="risk-body">
        <div class="risk-author"><span>{html_escape(author)}</span>{team_str}  ·  {len(grp['risks'])} 项</div>
{items_html}      </div>
    </div>
"""
        risk_empty_hidden = "display:none;"
    else:
        risk_cards_html = ""
        risk_empty_hidden = ""

    # 提交总览卡片
    person_cards_html = ""
    for p in people:
        name = p.get("name", "")
        if not name:
            continue
        is_submitted = any(s["name"] == name for s in submitted)
        if is_submitted:
            person_cards_html += f"""    <div class="person-card">
      <div class="person-status done">✓</div>
      <div class="person-info">
        <div class="person-name">{html_escape(name)}</div>
        <div class="person-role">{html_escape(p.get('role',''))}{' · ' + html_escape(p.get('team','')) if p.get('team') else ''}</div>
      </div>
    </div>
"""
        else:
            person_cards_html += f"""    <div class="person-card missing">
      <div class="person-status miss">✗</div>
      <div class="person-info">
        <div class="person-name">{html_escape(name)}</div>
        <div class="person-role">{html_escape(p.get('role',''))}{' · ' + html_escape(p.get('team','')) if p.get('team') else ''}</div>
      </div>
    </div>
"""

    # 周报详情 accordion
    report_items_html = ""
    for r in submitted:
        name = r["name"]
        initial = name[0] if name else "?"
        team = r["team"] or ""
        role = r.get("role", "")
        meta = " · ".join(filter(None, [role, team]))
        time_str = r["createdTime"]

        # 智能转换：处理 Markdown 内嵌或纯 HTML
        body_html = content_to_display_html(r["content_html"])

        report_items_html += f"""    <div class="report-item">
      <button class="report-toggle" aria-expanded="false">
        <div class="report-avatar">{html_escape(initial)}</div>
        <div class="report-meta">
          <div class="report-author">{html_escape(name)}<span class="report-team">{html_escape(meta)}</span></div>
          <div class="report-time">{html_escape(time_str)} 提交</div>
        </div>
        <div class="report-chevron">▾</div>
      </button>
      <div class="report-body">{body_html}</div>
    </div>
"""

    # ── 组装 ──
    html = build_html(template, {
        "DATE_RANGE": date_range,
        "SUBMITTED_COUNT": submitted_count,
        "MISSING_COUNT": missing_count,
        "TOTAL_COUNT": total,
        "SUBMISSION_RATE": submission_rate,
        "UNSUBMITTED_HIDDEN": unsubmitted_hidden,
        "UNSUBMITTED_NAMES": names_html,
        "RISK_COUNT": len(all_risks),
        "RISK_CARDS": risk_cards_html,
        "RISK_EMPTY_HIDDEN": risk_empty_hidden,
        "PERSON_CARDS": person_cards_html,
        "REPORT_ITEMS": report_items_html,
        "GENERATED_AT": generated_at,
    })

    # 输出
    if args.output:
        out_path = Path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
    else:
        repo_root = Path(__file__).resolve().parents[4]
        out_dir = repo_root / "output" / "mes" / "mes-weekly-report"
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / f"weekly_report_{args.from_date}_to_{args.to_date}.html"

    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"\n[OK] {out_path}")
    print(f"  提交 {submitted_count}/{total}  ·  风险 {len(all_risks)} 项")


if __name__ == "__main__":
    main()
