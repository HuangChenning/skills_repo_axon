---
name: mes-weekly-report
description: >
  查看指定人员的 MES 周报内容，支持 Markdown 和 HTML 两种输出格式。
  支持通过 people.json 配置关注人员清单（如总监、区总等管理层），
  定期拉取周报并展示正文内容。HTML 版含提交统计、风险汇总、折叠详情。

  触发关键词：查看周报、周报汇总、总监周报、区总周报、管理层周报、
  周报内容、周报查看、拉取周报、周报分析、周报HTML、周报看板。
---

# MES 周报查看

基于 `people.json` 配置的关注人员清单，通过 `mes` CLI 拉取指定日期范围内的周报。

## 主题 / HTML 看板 / 邮件正文设计规范（全量内嵌，可独立运行）

> **触发**：修改 `scripts/generate_html.py` 的内联 CSS、调整 `templates/weekly-report.html` 样式、或新增 `--email-html` 主管群发邮件正文时，必须按本章 6 件事逐段套用。
>
> 所有代码块 **可直接粘贴**，无需跳读任何外部文档。

### §0 MES 周报独有安全铁律
1. **禁止手写 SMTP / MIME 整头编码**（会导致 Content-Disposition 编码错误、附件变 `.bin`，2026-08-05 事故）。**必须**走标准发送脚本；**收件人不得写死在本 skill 中**，必须按下方「收件人解析」解析后再传 `--to`：
   ```bash
   # 优先级：本地 enmo_support_skill checkout > 仓库内置副本
   if [ -f "$HOME/enmo-local/enmo_support_skill/skills/report-quality-report/scripts/send_report_email.py" ]; then
     SEND_SCRIPT="$HOME/enmo-local/enmo_support_skill/skills/report-quality-report/scripts/send_report_email.py"
   else
     SEND_SCRIPT="skills/meta/scripts/send_report_email.py"
   fi
   # $TO 必须来自「收件人解析」，禁止在命令里写死邮箱地址
   python "$SEND_SCRIPT" --to "$TO" --body-html weekly_email.html --attach "weekly_report.html" --verify
   ```
2. **Outlook Word 兼容**：`--email-html` 生成的主管群发邮件正文必须有 **4 处** `<!--[if mso]>` 条件注释、禁止 `border-left` 画侧边线/进度条、所有颜色行内写死（Word 不读 `var(--xxx)`）。
3. **transition 下限 160ms**：周报是"人眼看的管理看板"，不能用 120ms 一跳一跳的动画；只有按压回弹 `:active` 允许用 120ms。

### A. §15 Typography · 字体体系（6 Token）

```css
:root {
  --font-sans: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI",
    "PingFang SC", "Microsoft YaHei", "Helvetica Neue", Arial, sans-serif;
  font-optical-sizing: auto;
  --typo-hero-size: 32px; --typo-hero-weight: 700;
  --typo-hero-tracking: -0.02em; --typo-hero-leading: 1.05;
  --typo-section-size: 18px; --typo-section-weight: 600;
  --typo-section-tracking: -0.008em; --typo-section-leading: 1.25;
  --typo-card-size: 14px; --typo-card-weight: 600; --typo-card-leading: 1.3;
  --typo-body-size: 13px; --typo-body-weight: 400;
  --typo-body-tracking: 0.005em; --typo-body-leading: 1.5;
  --typo-label-size: 12px; --typo-label-weight: 400; --typo-label-leading: 1.4;
  --typo-caption-size: 11px; --typo-caption-weight: 400; --typo-caption-leading: 1.4;
}
@media (max-width: 768px) {
  :root {
    --typo-hero-size: 28px; --typo-section-size: 16px;
    --typo-card-size: 13px; --typo-body-size: 12px;
    --typo-label-size: 11px; --typo-caption-size: 10px;
  }
}
```

### B. §8 四色语义反馈（12 Token · 浅/暗 2 版）

浅色主题：

```css
:root {
  --fb-status-bg: rgba(148,163,184,.12); --fb-status-fg: #475569;
  --fb-status-border: rgba(148,163,184,.25);
  --fb-warn-bg: rgba(249,115,22,.12); --fb-warn-fg: #c2410c;
  --fb-warn-border: rgba(249,115,22,.28);
  --fb-error-bg: rgba(239,68,68,.12); --fb-error-fg: #b91c1c;
  --fb-error-border: rgba(239,68,68,.28);
  --fb-success-bg: rgba(34,197,94,.12); --fb-success-fg: #15803d;
  --fb-success-border: rgba(34,197,94,.28);
}
```

暗色主题（如需）：fg 换亮字 `#cbd5e1/#fde68a/#fecaca/#bbf7d0`，bg/border 透明度加至 `.18/.35`。

### C. §12 Materials & Depth · 4 阶厚度公式（核心！）

**铁律**：阴影颜色必须用中性灰（浅 `rgba(15,23,42,.xx)` / 暗 `rgba(0,0,0,.xx)`），严禁品牌色染色。每阶最外一层带 **Negative Spread = blur/6**（防阴影溢出盖下一区标题）。

#### C1. 浅色主题 4 阶阴影 Token

```css
:root {
  --shadow-chip: 0 1px 1px rgba(15,23,42,.12), inset 0 1px 0 rgba(255,255,255,.72);
  --shadow-card: 0 1px 2px rgba(15,23,42,.10),
    0 6px 16px -4px rgba(15,23,42,.14),
    inset 0 1px 0 rgba(255,255,255,.68);
  --shadow-panel: 0 1px 2px rgba(15,23,42,.08),
    0 4px 12px -4px rgba(15,23,42,.12),
    0 16px 36px -8px rgba(15,23,42,.14),
    inset 0 1px 0 rgba(255,255,255,.72);
  --shadow-sheet: 0 1px 1px rgba(15,23,42,.10),
    0 8px 20px -6px rgba(15,23,42,.14),
    0 24px 54px -10px rgba(15,23,42,.16),
    0 54px 120px -20px rgba(15,23,42,.18),
    inset 0 1px 0 rgba(255,255,255,.80);
}
```

#### C2. 暗色主题 4 阶阴影 Token

把颜色全部换成 `rgba(0,0,0, .30~.38)`，顶边高光的白透明度从 `.68~.80` 改为 `.06~.08`。

#### C3. 四向边框接光（45° 顶光物理模型 · 套到 .card/.panel）

| 边框 | 浅色主题 | 暗色主题 |
|------|---------|---------|
| border-top | `rgba(255,255,255,.68)` | `rgba(255,255,255,.06)` |
| border-left | `rgba(255,255,255,.20)` | `rgba(255,255,255,.03)` |
| border-right | `rgba(15,23,42,.05)` | `rgba(0,0,0,.06)` |
| border-bottom | `rgba(15,23,42,.04)` | `rgba(0,0,0,.08)` |

```css
.card {
  border-top:1px solid rgba(255,255,255,.68);
  border-left:1px solid rgba(255,255,255,.20);
  border-right:1px solid rgba(15,23,42,.05);
  border-bottom:1px solid rgba(15,23,42,.04);
  box-shadow: var(--shadow-card);
}
```

#### C4. Nav 毛玻璃（Sheet 级最厚 · 邮件场景禁用）

```css
.nav-bar {
  background: rgba(255,255,255,.72);                         /* 暗色换 rgba(22,33,62,.78) */
  backdrop-filter: blur(20px) saturate(180%);
  -webkit-backdrop-filter: blur(20px) saturate(180%);
  border-top:1px solid rgba(255,255,255,.80);
  border-left:1px solid rgba(255,255,255,.22);
  border-right:1px solid rgba(15,23,42,.06);
  border-bottom:1px solid rgba(15,23,42,.06);
  box-shadow: var(--shadow-sheet);
}
```

### D. §7 镜像 Easing · 关/开/按压三态

严禁 `transition: all` 或 `ease`；**周报 `transition` 下限 160ms**（只有 `:active` 允许 120ms）。

```css
.card {
  transform: translateY(0) scale(1);
  transition: transform 160ms cubic-bezier(.68,0,.32,1),
    box-shadow 160ms cubic-bezier(.68,0,.32,1),
    background-color 160ms cubic-bezier(.68,0,.32,1),
    border-color 160ms cubic-bezier(.68,0,.32,1);
  box-shadow: var(--shadow-chip);
}
@media (hover: hover) {
  .card:hover {
    transform: translateY(-2px) scale(1.01);
    transition: transform 160ms cubic-bezier(.23,1,.32,1),
      box-shadow 160ms cubic-bezier(.23,1,.32,1),
      background-color 160ms cubic-bezier(.23,1,.32,1),
      border-color 160ms cubic-bezier(.23,1,.32,1);
    box-shadow: var(--shadow-card);
  }
}
.card:active {
  transform: translateY(0) scale(.97);
  box-shadow: var(--shadow-chip);
  transition: transform 120ms cubic-bezier(.4,0,.2,1),
    box-shadow 120ms cubic-bezier(.4,0,.2,1);
}
```

### E. §14 三门控 + A6 断点 + Print 强化

```css
/* §14 门控 1：减少动效 */
@media (prefers-reduced-motion: reduce) {
  *,*::before,*::after { animation:none !important; transition:none !important; transform:none !important; }
}
/* §14 门控 2：减少透明 → 毛玻璃降级实体 */
@media (prefers-reduced-transparency: reduce) {
  .nav-bar { background:#ffffff !important; backdrop-filter:none !important; -webkit-backdrop-filter:none !important; }
}
/* §14 门控 3：高对比 → 去阴影 + 2px 实边（暗底主题把颜色换成 #fff） */
@media (prefers-contrast: more) {
  .card,.panel,.kpi-card,.nav-bar,.badge { box-shadow:none !important; border:2px solid #000 !important; }
}
/* A6 响应式断点 1080/768/1440：1080 时多人网格→1 列，768 时全 1 列紧 padding */
@media (max-width: 1080px) { .people-grid,.grid2,.grid3,.grid4 { grid-template-columns:1fr !important; } }
@media (max-width: 768px) {
  .container { padding:12px !important; } .hero { padding:24px 16px !important; }
  .people-grid,.grid2,.grid3,.grid4,.grid5,.grid6 { grid-template-columns:1fr !important; gap:12px !important; }
}
@media (min-width: 1440px) { .container { max-width:1400px; margin:0 auto; } }
/* Print 打印模式：防跨页 + 去阴影 + 实灰边 + 深色墨（管理周报常被导 PDF 存档） */
@media print {
  .card,.panel,.section,.kpi-card,tr,.badge,.person-block { break-inside:avoid !important; page-break-inside:avoid !important; }
  .card,.panel,.kpi-card,.nav-bar,.badge { box-shadow:none !important; border:1px solid #ccc !important; }
  .hero,.nav-bar { background:#fff !important; backdrop-filter:none !important; }
  * { color:#111 !important; }
}
```

### §G. 主管群发邮件 Outlook 降级 7 条铁律（生成 `--email-html` 时）

| 功能 | 邮件正文处理 | 说明 |
|------|------------|------|
| Nav 毛玻璃 `backdrop-filter` | ❌ 不写 | Word 完全不支持 → `bgcolor="#F8FAFC"` 实色 |
| `transition` / `:hover` / `:active` | ❌ 不写 | 邮件是静态文档，不写任何交互 |
| 1080 / 1440 断点 | ❌ 不写 | 只保留 768px 断点（可选） |
| `border-radius` | ⚠️ ≤4px | Word 会把大圆角转方角 |
| `border-left` / CSS 进度条 | ❌ 不写 | 改为 `<table><td width="2%" bgcolor="#…"></td>` 两列表 |
| `<!--[if mso]>` 条件注释 | ✅ 必须 4 处 | 容器 / 面板头 / 页脚 / 风险条 table fallback |
| `var(--xxx)` CSS 变量 | ❌ 不依赖 | 所有颜色行内写死 `style="background:#fff;color:#0F172A"` |

### F. 修改样式自检 Checklist

**首选：一键执行脚本（周报独有：160ms 下限 + `--email` 模式 Outlook 降级）**

```bash
cd skills/mes/mes-weekly-report
# 1) HTML 看板（templates/weekly-report.html；generate_html.py 若无独立 CSS 段则跳过）
bash scripts/verify_new_theme.sh templates/weekly-report.html
# 2) 主管群发邮件正文（`--email-html` 生成的 body template）
bash scripts/verify_new_theme.sh --email /tmp/weekly_email_body.html
```

**逐条手动校验（阈值与脚本保持一致）：**

```bash
# 1) HTML 看板内联 CSS（scripts/generate_html.py 或 templates/weekly-report.html）
cd skills/mes/mes-weekly-report
SRC=scripts/generate_html.py
grep -c -- '-[0-9]\+px' $SRC                                 # §12 Negative Spread ≥ 4
grep -c 'fb-\(status\|warn\|error\|success\)-bg' $SRC          # §8 四色 bg ≥ 4
grep -c 'prefers-\(reduced-motion\|reduced-transparency\|contrast\)' $SRC  # §14 三门控 ≥ 3
awk '/:active[^{]*\{/,/^[[:space:]]*\}/ { if (match($0,/scale\(0?\.9/)) c++ } END{print c+0}' $SRC   # §7 按压态 ≥ 1
grep -c 'inset 0 1px 0' $SRC                                   # §12 顶边高光 ≥ 4
# 周报独有 1：transition 下限（不能只有 120ms，必须有 160ms）
grep -cE '160ms' $SRC                                         # §7 D 段下限 ≥ 1

# 2) 如发布 --email-html：必须用标准发送（不能自己写 SMTP）
grep -cE 'send_report_email|--body-html' <发送脚本或说明>    # §0 必须 ≥ 1
```

---

**两种输出格式**：
- **Markdown**（`fetch_weekly.py`）— 纯文本，适合终端快速浏览
- **HTML**（`generate_html.py`）— 可视化看板，含提交统计、风险汇总、折叠详情

## 适用场景

- 定期查看总监、区总等管理层的周报
- 汇总特定人员的周报内容
- 快速浏览周报正文（非 HTML 看板）

## 人员清单

编辑 `skills/mes/mes-weekly-report/people.json` 增删关注人员：

```json
{
  "people": [
    {"name": "李华", "role": "总监", "team": "东西大区1部"}
  ]
}
```

- `name`：必填，用于匹配 `mes` CLI 的 `--creator` 参数
- `role`：可选，输出中标注职位
- `team`：可选，fallback 团队名（CLI 返回的 `adminTeamName` 优先）

## 使用流程

### Step 1：确认环境

```bash
mes auth status
```

未登录时执行 `mes auth login --web`。

### Step 2：执行脚本

```bash
# 默认拉取上周（周一~周日）
python skills/mes/mes-weekly-report/scripts/fetch_weekly.py

# 指定日期范围
python skills/mes/mes-weekly-report/scripts/fetch_weekly.py \
  --from 2026-07-06 --to 2026-07-12

# 指定输出路径
python skills/mes/mes-weekly-report/scripts/fetch_weekly.py \
  --from 2026-07-06 --to 2026-07-12 \
  --output /path/to/output.md
```

### Step 3：查看结果

输出文件默认位于 `output/mes/mes-weekly-report/weekly_report_<起始日期>_to_<截止日期>.md`。

脚本同时将 Markdown 内容打印到 stdout，可在终端直接阅读。

## 输出格式

```markdown
# 周报汇总 — 2026-07-06 ~ 2026-07-12

> 关注 6 人，已提交 6 人

---

## 李华（总监 | 东西大区1部）
提交时间：2026-07-12 23:57  |  周期：2026-07-06 ~ 2026-07-12

（纯文本正文...）

---

## 许文榕（总监 | 东西大区2部）
...
```

## 参数说明

### fetch_weekly.py（Markdown）

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `--from` | 上周一 | 周报周期起始日期 |
| `--to` | 上周日 | 周报周期截止日期 |
| `--people-file` | `people.json` | 人员清单路径 |
| `--output` | `output/mes/mes-weekly-report/weekly_report_<日期>.md` | 输出文件路径 |

### generate_html.py（HTML 看板）

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `--from` | 上周一 | 周报周期起始日期 |
| `--to` | 上周日 | 周报周期截止日期 |
| `--people-file` | `people.json` | 人员清单路径 |
| `--output` | `output/mes/mes-weekly-report/weekly_report_<日期>.html` | 输出文件路径 |
| `--template` | `templates/weekly-report.html` | HTML 模版路径 |

## HTML 看板功能

`generate_html.py` 生成的可视化看板包含：

1. **Hero 区**：日期范围、已提交/未提交人数、提交率进度条
2. **未提交提醒**：醒目标注未提交人员名单
3. **风险汇总**：自动从「交付风险反馈」「收入风险反馈」「需要升级的问题」章节提取风险项，红/橙分级
4. **提交总览**：全员卡片矩阵（✓/✗ 状态）
5. **周报详情**：折叠式手风琴，点击展开每人完整周报正文 |

## 维护人员清单

直接编辑 `people.json`，增删 `people` 数组中的对象：

```bash
# 示例：添加区总
# 在 people 数组中追加：
# {"name": "区总姓名", "role": "区总", "team": "东西大区"}
```

保存后下次执行脚本即可生效，无需修改代码。

## 注意事项

- 脚本通过 `mes dashboard weeklyReport --creator <name>` 按姓名查询，姓名需与 MES 中一致
- 每人只取第一条匹配的周报
- 未提交周报的人员在输出中标记为「未提交」
- HTML 正文自动转换为纯文本，去除格式标签

## 邮件发送

> **⚠️ 运行日自检（防 catch-up 补跑误发，2026-08 起强制）**
>
> 周报汇总由「每周一早上」的定时任务调用。**非预期触发（gateway 停机后 catch-up 补跑、jobs.json 恢复、手动运行）会在错误日期执行**，此时发送的周报日期范围错误（2026-08-06 已发生同类事故：catch-up 补跑导致报告在非运行日误发）。
>
> **本检查必须在执行入口（任何数据拉取、文件生成、邮件发送之前）执行**，不是发送前的最后一道检查：
> ```python
> import sys
> from datetime import date
> if date.today().weekday() != 0:   # 周一 = weekday()==0
>     print(f"[SILENT] 今天不是周一（今日={date.today()}），跳过本次执行（防补跑误发）")
>     sys.exit(0)
> ```
> - 不是周一 → `[SILENT]` 退出，**不拉数据、不生成文件、不发送**
> - 是周一 → 继续；周报日期范围固定为**上周一 ~ 上周日**，因已通过周一校验，可直接计算：`--from = today - 7 天`（上周一）、`--to = today - 1 天`（上周日），**禁止**使用非预期日期范围
> - 例外：用户手动指定 `--from`/`--to` 查看历史周报时不受本检查约束（本检查仅针对定时任务触发的自动发送流程）

周报汇总生成后通过标准脚本发送。**本 skill 不硬编码任何业务邮箱**（收件人见下；发件人/SMTP 由 `send_report_email.py` 从环境变量或 `~/.config/enmo_support_skill/email.json` 解析）。

### 收件人解析（强制，禁止硬编码）

**本 skill 可在不同团队/环境复用。收件人、抄送、密送一律由调用方在运行时约定，禁止写入 `SKILL.md`、脚本默认值或仓库内已提交配置。**

解析优先级（高 → 低）：

1. **本次用户/调用方明确指定**（对话中给出的收件人、`--to` / `--cc` / `--bcc` 参数）
2. **环境变量**
   - `MES_WEEKLY_REPORT_TO`（必填才可发送；逗号分隔）
   - `MES_WEEKLY_REPORT_CC`、`MES_WEEKLY_REPORT_BCC`（可选）
3. **本地配置** `skills/mes/mes-weekly-report/runtime.local.json`（git-ignored；示例见 `runtime.local.json.example`）

```json
{
  "email": {
    "to": ["alice@example.com", "bob@example.com"],
    "cc": [],
    "bcc": []
  }
}
```

规则：

- 以上三者均未提供有效 `to` → **禁止发送**，向用户说明缺少收件人，并请其指定或配置后再发
- **禁止**从 `people.json`、历史对话默认、或其他 skill 文档抄写邮箱当作收件人
- 发件人/SMTP/授权码：`REPORT_EMAIL_FROM`、`REPORT_SMTP_HOST`、`REPORT_EMAIL_PASS` 等，或 `~/.config/enmo_support_skill/email.json` / `email_pass`（见 `skills/meta/scripts/README.md`）
- 附件：生成的 HTML 看板文件（必须携带，发送前经过下方自检）

### 邮件主题与正文定义（强制）

**主题格式**：`周报汇总 {起始日期} ~ {截止日期}（已提交 x/y）`

示例：`周报汇总 2026-07-20 ~ 2026-07-26（已提交 6/11）`

**正文必须依次包含以下三个板块**：

#### 板块一：提交情况

```text
一、提交情况
关注 {n} 人，已提交 {x} 人，未提交 {y} 人。

已提交：{姓名1、姓名2、...}
未提交：{姓名1、姓名2、...}
```

- 人员名单按 `people.json` 中的顺序排列
- 无人未提交时写「未提交：无」

#### 板块二：风险与问题

```text
二、风险与问题

【交付风险】
1. [{提交人}] {风险/问题内容，一两句话提炼}

【收入风险】
1. [{提交人}] ...

【人员风险】
1. [{提交人}] ...

【需要升级】
1. [{提交人}] ...
```

收集范围：已提交人员周报中以下章节的实质内容：
- 「交付风险反馈」
- 「收入风险反馈」
- 「需要升级的问题」

**风险分类标准**（每条风险必须归入一类，按分组展示）：

| 分类 | 判定标准 |
|------|----------|
| 交付风险 | 影响项目交付质量、进度、服务连续性或客户体验 |
| 收入风险 | 影响回款、验收、订单消耗、合同签订或续约 |
| 人员风险 | 人员离职、招聘缺口、调配冲突、人力成本异常 |
| 需要升级 | 周报「需要升级的问题」章节明确提出需管理层决策介入 |

规则：
- 一条风险若跨多类，归入**主要影响**所在的一类，不重复列出
- 空分组直接省略，不输出「无」占位；若四类全空则写「本周各周报未提及风险与需升级问题」
- 只收集有实质内容的条目，章节为空或为「无」「...」时跳过
- 每条标注提交人姓名，内容做一句话提炼，不照搬全文

#### 板块三：业务机会线索

```text
三、业务机会线索

【Mopheus 相关】
1. [{提交人}] {机会描述}
2. ...

【其他商机】
1. [{提交人}] {机会描述}
2. ...
```

收集范围：已提交人员周报全文中的业务机会信号，包括但不限于：
- 新产品推广/试点（**Mopheus 相关机会（产品族含 MoClaw/墨小侠）优先标注，单独成组**）
- 新商机、投标、续约扩容、客户主动需求

规则：
- **⚠️ 板块标题固定为「【Mopheus 相关】」，必须与上方示例完全一致；严禁写成【Mopheus / MoClaw 相关】/【Mopheus/MoClaw 相关】/【MoClaw 相关】——标题中禁止出现「MoClaw」字样**（MoClaw/墨小侠仅作为内容识别关键词用于筛选机会，绝不写入标题）
- Mopheus 相关机会（含 MoClaw/墨小侠）必须置顶并单独分组，识别关键词：MoClaw、moclaw、墨小侠、Mopheus、mopheus、AI 运维一体机
- 其他商机按提交人归类
- 无商机线索时写「本周各周报未提及新的业务机会线索」

**正文结尾**：

```text
详细周报内容请查看附件 HTML 看板（含提交统计、风险汇总、折叠式详情）。
```

### ⚠️ 发送必须使用标准脚本（强制，v2.2）

**禁止手写 SMTP/MIME 代码**（手写会导致 Content-Disposition 编码错误、附件丢失或变 .bin，2026-08-05 电信/平台报告曾出事故）。统一调用标准发送脚本。

**脚本路径解析（可移植，支持在其他 agent/机器上执行，勿写死绝对路径）：**

```bash
# 优先级：本地 enmo_support_skill checkout（版本更新）> 本仓库内置副本
if [ -f "$HOME/enmo-local/enmo_support_skill/skills/report-quality-report/scripts/send_report_email.py" ]; then
    SEND_SCRIPT="$HOME/enmo-local/enmo_support_skill/skills/report-quality-report/scripts/send_report_email.py"
else
    SEND_SCRIPT="skills/meta/scripts/send_report_email.py"   # 仓库内置副本，需在仓库根目录执行
fi
[ -f "$SEND_SCRIPT" ] || { echo "❌ 未找到标准发送脚本，放弃发送（禁止手写 SMTP 代替）"; exit 1; }
```

两处都找不到 → **放弃发送并报错，绝不允许手写 SMTP/MIME 代替**。先完成「收件人解析」得到 `$TO`（及可选 `$CC` / `$BCC`），再调用：

```bash
# $TO 来自用户指定 / MES_WEEKLY_REPORT_TO / runtime.local.json，禁止在此写死邮箱
python3 "$SEND_SCRIPT" \
    --to "$TO" \
    ${CC:+--cc "$CC"} \
    ${BCC:+--bcc "$BCC"} \
    --subject "周报汇总 2026-07-20 ~ 2026-07-26（已提交 6/11）" \
    --body-html /tmp/weekly_body.html \
    --attach /path/to/weekly_report_2026-07-20_to_2026-07-26.html \
    --verify
```

- 邮件 HTML 正文先写入临时文件（如 `/tmp/weekly_body.html`）再传 `--body-html`
- 脚本内置自检（文件存在/后缀/DOCTYPE/≤10MB）+ 正确的 Content-Disposition
- **`--verify`（v3.6 起强制加）**：发送后自动 IMAP 回读「已发送」最近 100 封验证附件（Content-Disposition 以 `attachment;` 开头且含 `filename="` 或 `filename*=`；以 `=?utf-8?b?` 开头=损坏需重发），退出码 0=通过；1=损坏/缺失需重发。**v3.7 起未命中自动重试**：腾讯企业邮箱「已发送」同步到 IMAP 有几秒~几十秒延迟，未命中时最多重试 3 次、每次间隔 15 秒（命中但附件异常则立即失败，不重试）。**不要手写 imaplib 代码做回读**（该邮箱 IMAP 的 SINCE 日期过滤失效，手写容易踩坑）

### 附件文件名

**中文附件名完全可用**（标准脚本 `add_header` 会自动做 RFC 2231 编码，企业邮箱/Outlook 正常识别）。旧认知「中文名变 .bin」是错的——真正根因是手写代码把**整个 Content-Disposition 头**做了 RFC 2047 编码。文件名唯一禁止项：路径分隔符、换行、控制字符。

`generate_html.py` 和 `fetch_weekly.py` 的默认输出文件名已是 ASCII 格式（如 `weekly_report_2026-07-13_to_2026-07-19.html`），直接使用即可，无需手动改名。
