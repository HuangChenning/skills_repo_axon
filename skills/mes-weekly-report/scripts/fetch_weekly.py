#!/usr/bin/env python3
"""
MES 周报拉取脚本 — 按人员清单拉取周报，输出 Markdown。
用法：
  python fetch_weekly.py --from 2026-07-06 --to 2026-07-12
  python fetch_weekly.py  # 默认上周一~上周日
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


def run_mes(cmd: list[str]) -> dict:
    """执行 mes 命令并返回 JSON 结果。"""
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
        print(f"[ERROR] mes 命令输出无法解析: {result.stdout[:200]}", file=sys.stderr)
        return {}


def strip_html(html_text: str) -> str:
    """去除 HTML 标签，还原实体，返回纯文本。"""
    if not html_text:
        return ""
    # 将 <br> 和 <br/> 等转为换行
    text = re.sub(r'<br\s*/?>', '\n', html_text)
    # </p> </div> </h1>-</h6> </li> </tr> 等块级结束标签后加换行
    text = re.sub(r'</(?:p|div|h\d|li|tr|section|article|blockquote)>', '\n', text)
    # 去除其余标签
    text = re.sub(r'<[^>]+>', '', text)
    # 还原 HTML 实体
    text = html_mod.unescape(text)
    # 清理多余空行
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


def last_week_dates() -> tuple[str, str]:
    """返回上周一和上周日的日期字符串。"""
    today = date.today()
    # 上周一 = 今天 - 今天 weekday - 7
    last_monday = today - timedelta(days=today.weekday() + 7)
    last_sunday = last_monday + timedelta(days=6)
    return last_monday.isoformat(), last_sunday.isoformat()


def fetch_report(person: dict, from_date: str, to_date: str) -> dict | None:
    """拉取指定人员的周报。返回 {name, role, team, period, createdTime, content} 或 None。"""
    name = person.get("name", "")
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

    # 取第一条匹配的周报
    r = reports[0]

    # 通过 view 获取完整正文
    report_id = r.get("id")
    if report_id:
        detail = run_mes(["dashboard", "weeklyReport", "view", str(report_id)])
        obj = detail.get("operateCallBackObj", {}) if isinstance(detail, dict) else {}
        full_content = obj.get("content") or r.get("content") or ""
    else:
        full_content = r.get("content") or ""

    return {
        "name": name,
        "role": person.get("role", ""),
        "team": r.get("adminTeamName") or person.get("team", ""),
        "period": f"{r.get('periodStartDate', '')} ~ {r.get('periodEndDate', '')}",
        "createdTime": r.get("createdTime", ""),
        "content": strip_html(full_content),
    }


def main():
    parser = argparse.ArgumentParser(description="拉取指定人员的 MES 周报，输出 Markdown")
    default_from, default_to = last_week_dates()
    parser.add_argument("--from", dest="from_date", default=default_from,
                        help=f"起始日期（默认 {default_from}）")
    parser.add_argument("--to", dest="to_date", default=default_to,
                        help=f"截止日期（默认 {default_to}）")
    parser.add_argument("--people-file", default=None,
                        help="人员清单 JSON 文件路径（默认脚本同目录下的 people.json）")
    parser.add_argument("--output", default=None,
                        help="输出 Markdown 文件路径（默认 output/mes/mes-weekly-report/周报_<日期>.md）")
    args = parser.parse_args()

    # 人员清单路径
    script_dir = os.path.dirname(os.path.abspath(__file__))
    people_file = args.people_file or os.path.join(script_dir, "..", "people.json")
    people_file = os.path.normpath(people_file)

    if not os.path.exists(people_file):
        print(f"[ERROR] 人员清单不存在: {people_file}", file=sys.stderr)
        sys.exit(1)

    try:
        with open(people_file, "r", encoding="utf-8") as f:
            config = json.load(f)
    except json.JSONDecodeError as e:
        print(f"[ERROR] 人员清单 JSON 格式错误: {e}", file=sys.stderr)
        sys.exit(1)

    people = config.get("people", [])

    if not people:
        print("[ERROR] 人员清单为空", file=sys.stderr)
        sys.exit(1)

    print(f"关注人员: {len(people)} 人")
    print(f"日期范围: {args.from_date} ~ {args.to_date}")
    print()

    # 拉取周报
    results = []
    for person in people:
        name = person.get("name")
        if not name:
            print("  [WARN] 发现未配置姓名的记录，跳过", file=sys.stderr)
            continue
        print(f"  查询 {name}...", end=" ", flush=True)
        report = fetch_report(person, args.from_date, args.to_date)
        if report:
            print(f"✓ ({len(report['content'])} 字)")
            results.append(report)
        else:
            print("✗ 未提交")

    # 生成 Markdown
    submitted = len(results)
    missing = len(people) - submitted
    status_parts = [f"已提交 {submitted} 人"]
    if missing > 0:
        status_parts.append(f"未提交 {missing} 人")
        missing_names = [
            p.get("name", "") for p in people
            if p.get("name") and not any(r["name"] == p.get("name") for r in results)
        ]
        status_parts.append(f"（{'、'.join(missing_names)}）")

    lines = [
        f"# 周报汇总 — {args.from_date} ~ {args.to_date}",
        "",
        f"> 关注 {len(people)} 人，{'，'.join(status_parts)}",
        "",
    ]

    if not results:
        lines.append("本周暂无人员提交周报。")
        md = "\n".join(lines)
    else:
        lines.append("---")
        lines.append("")
        for r in results:
            meta_parts = [r["role"], r["team"]]
            meta_str = " | ".join(p for p in meta_parts if p)
            lines.append(f"## {r['name']}（{meta_str}）" if meta_str else f"## {r['name']}")
            lines.append(f"提交时间：{r['createdTime']}  |  周期：{r['period']}")
            lines.append("")
            lines.append(r["content"])
            lines.append("")
            lines.append("---")
            lines.append("")
        md = "\n".join(lines)

    # 输出文件
    if args.output:
        out_path = Path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
    else:
        repo_root = Path(__file__).resolve().parents[4]
        out_dir = repo_root / "output" / "mes" / "mes-weekly-report"
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / f"weekly_report_{args.from_date}_to_{args.to_date}.md"

    with open(out_path, "w", encoding="utf-8") as f:
        f.write(md)

    print(f"\n[OK] 输出: {out_path}")
    # 同时打印到 stdout
    print()
    print(md)


if __name__ == "__main__":
    main()
