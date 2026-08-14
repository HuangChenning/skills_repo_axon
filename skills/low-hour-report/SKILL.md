---
name: low-hour-report
description: >-
  通过 mes CLI 查询指定时间范围内零报工或极低报工的实施计划。以 statistics（实际报工记录）为数据源，按计划聚合后筛选。当用户需要检查报工情况、查找未报工或报工不足的计划、排查工时异常、生成报工合规报告时使用。触发场景：「查零报工」「哪些计划没报工」「报工不足20小时」「极低报工排查」「报工检查」「工时合规」「谁没报工」。
---

# 低报工排查

> **数据源**：`mes statistics list` 中的实际报工记录（`type=1`，实施计划），按 `rid`（计划 ID）聚合 `taskTime`。**不得使用 `plan list` 的 `executorList.taskTime`**——那是计划分配工时，不是实际报工工时。

## MES 登录

本技能所有数据均通过 `mes` CLI 拉取。使用前需先完成登录并确认 token 有效：

```bash
mes auth login
mes auth status
```

## 一、判定标准

| 分类 | 条件 | 标记 |
|------|------|------|
| 零报工 | 实际报工总工时 = 0 | 🔴 零报工 |
| 极低报工 | 0 < 实际报工总工时 < 20h | 🟡 极低报工 |
| 正常 | 实际报工总工时 ≥ 20h | — |

阈值 20h 为默认值，用户可指定其他阈值（如 10h、30h）。

## 二、查询流程

### 步骤1：解析时间范围

将用户输入的时间范围转换为 `YYYY-MM-DD` 格式：

| 用户表述 | 转换（示例为 2026 年） |
|---------|---------------------|
| 「最近3个月」 | 当前日期往前推3个月 → 当月1日 ~ 今天 |
| 「Q2」「4月到6月」 | 2026-04-01 ~ 2026-06-30 |
| 「4月1日~6月30日」 | 2026-04-01 ~ 2026-06-30 |
| 「上个月」 | 上月1日 ~ 上月最后一天 |
| 「今年」 | 2026-01-01 ~ 2026-12-31 |

默认当年至今。年份未指定时默认当年。对于长周期查询（超过 3 个月），告知用户需要分页拉取全部报工记录，耗时可能较长。

### 步骤2：拉取全部实施计划（元数据）

```bash
mes -o json plan list \
  --start-date "<开始日期>" \
  --end-date "<结束日期>" \
  --page-size 100 --page 1
```

逐页拉取直到覆盖全部计划。将结果保存为以 `id` 为 key 的字典，用于后续关联元数据。

**提取字段**：`id`, `title`, `companyName`, `contractName`, `statusDesc`, `startDate`, `endDate`, `checkTypeDesc`, `executorList[].executorName`

### 步骤3：拉取全部实际报工记录（核心数据）

```bash
mes -o json statistics list \
  --from "<开始日期>" \
  --to "<结束日期>" \
  --page-size 200 --page 1
```

**必须将 JSON 重定向到临时文件**，用 `python3` 逐页解析。不要依赖终端截断输出。

对每页记录：
1. 筛选 `type == 1`（实施计划报工）
2. 按 `rid`（计划 ID）累加 `taskTime`
3. 记录每条报工的 `executorName` 用于展示

### 步骤4：关联并分类

对步骤2中的**每一个计划**：
- 如果 `plan.id` 在步骤3的聚合结果中 → 取其 `taskTime` 总和
- 如果不在 → 实际报工为 0（**零报工**）

然后按判定标准分为零报工、极低报工、正常三类。

### 步骤5：输出报告

## 三、输出格式

```markdown
## 报工排查报告

**时间范围**：2026-04-01 ~ 2026-06-30
**计划总数**：N 个
**实际报工记录数**：M 条（type=1）

| 分类 | 数量 | 占比 |
|------|------|------|
| 🔴 零报工 | X | X% |
| 🟡 极低报工（< 20h） | Y | Y% |
| 正常（≥ 20h） | Z | Z% |
```

### 🔴 零报工明细

```markdown
| # | 计划ID | 计划标题 | 客户 | 合同 | 计划类型 | 执行人 | 计划时间 | 状态 |
|---|--------|---------|------|------|---------|--------|---------|------|
```

### 🟡 极低报工明细

```markdown
| # | 计划ID | 计划标题 | 客户 | 合同 | 计划类型 | 报工人 | 工时 | 计划时间 | 状态 |
|---|--------|---------|------|------|---------|--------|------|---------|------|
```

## 四、输出规则

> **⚠️ 定时任务调用时：日期合理性自检（防 catch-up 补跑误发，2026-08 起强制）**
>
> 本技能被「每月 1 号」月初（770c0c67）和「每月 22-31 号周一」月末（bdbfeeb0）定时任务调用并发送邮件。**非预期触发（gateway 停机后 catch-up 补跑、jobs.json 恢复、手动运行）会在错误日期执行**，此时查询范围错误且会误发邮件。**调用方 cron 的 prompt 已含日期自检**（月初=1 号 / 月末=22-31 号周一，非运行日直接 `[SILENT] exit 0`），运行本技能前必须先通过该自检；若作为独立命令被手动调用，也先确认查询意图。

1. **必须完整读取**：statistics 和 plan list 的 JSON 输出必须通过临时文件 + `python3` 完整解析，不得依赖终端截断。完成后删除临时文件。
2. **Top N 截断**：零报工或极低报工超过 30 条时，仅展示前 30 条并标注「还有 X 条未展示，可要求查看完整列表」。
3. **阈值可调**：用户指定了阈值（如「不足 10 小时」）时，使用用户指定的阈值替代默认的 20h。
4. **未来计划**：计划 `startDate` 晚于当前日期且状态为「未开始」时，在报告中单独列出（不计入零报工统计），标注「尚未到执行时间」。

## 五、邮件发送（强制约定）

> **本技能不直接发邮件**——邮件发送由 cron / 调用方使用
> `~/.hermes/skills/enmo_support_skill/skills/report-quality-report/scripts/send_report_email.py`
> 完成。本节定义收发件人配置与约束，避免硬编码。

### 5.1 收发件配置文件（唯一权威）

- 本技能所有邮件场景的 `to` / `cc` 必须从
  `~/.config/enmo_support_skill/recipients/low-hour-report.json` 读取
- 文件不存在 / `profiles.<name>` 缺失 / `to` 为空 → **禁止发送**，先按下方示例补齐
- 发件人 / SMTP / IMAP 来自 `~/.config/enmo_support_skill/email.json`（脚本默认解析路径）

### 5.2 已预置 profile

| Profile | 用途 | to | cc |
|---|---|---|---|
| `month_start_low_hour` | 月初实施计划报工通知（主管群发） | 5 大区主管 | 老板 |
| `month_end_self_check` | 月末实施计划报工自查（仅自己） | 老板 | — |
| `alert` | 校验 FAIL、发送异常等运维通知 | 老板 | — |

新增场景（如某团队专项排查）时追加 `profiles.<name>` 即可，**禁止在 cron prompt 或 SKILL.md 中写死邮箱**。

### 5.3 调用方契约

```bash
# 1. 先列出已有 profile（dry-run，不发邮件）
python3 ~/.hermes/skills/enmo_support_skill/skills/report-quality-report/scripts/send_report_email.py \
    --config ~/.config/enmo_support_skill/recipients/low-hour-report.json \
    --list-profiles

# 2. 正式发送（按 profile）
python3 ~/.hermes/skills/enmo_support_skill/skills/report-quality-report/scripts/send_report_email.py \
    --profile month_start_low_hour \
    --config ~/.config/enmo_support_skill/recipients/low-hour-report.json \
    --subject "..." \
    --body-html /tmp/plan_body.html \
    --attach /path/to/零报工实施计划_xxx.xlsx \
    --body-require "各位主管" \
    --verify
```

- 缺 `--profile` 或 `--config` 指向的 profile 字段为空 → 脚本 sys.exit(1)，**禁止**
- `--to` / `--cc` 仅作调试覆盖，**正式发送禁止使用**
- 月初 / 月末 cron 的 prompt 已带日期合理性自检（非预期触发 → `[SILENT]` 退出）
5. **已逾期计划**：状态为「已逾期未结束」的正常计入统计。
