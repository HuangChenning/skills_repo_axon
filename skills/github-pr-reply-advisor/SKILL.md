---
name: github-pr-reply-advisor
description: Workflow for drafting professional and technically-justified GitHub Pull Request replies. Analyzed reviewer comments against code changes to determine if a suggestion is fixed or should be refuted. Generates structured, non-duplicate replies with verification context.
---

# GitHub PR Reply Advisor

This skill provides a systematic workflow for drafting professional, technically rigorous replies to GitHub Pull Request comments. It ensures every comment is addressed without duplication and with clear verification evidence.

## What I Do

1. **Retrieve PR Context** - Get all review comments and the current code state.
2. **Filter & Anti-Duplication** - Identify which comments are already replied to or resolved.
3. **Analyze Comment vs. Code** - Compare the reviewer's suggestion against the latest code changes.
4. **Determine Reply Strategy** - Choose between `FIXED` (accepted and implemented) or `REFUTE` (technically justified disagreement).
5. **Generate Response** - Produce a professional, structured reply for each pending comment.
6. **Post Replies** - Reply to each comment thread individually using the correct API.
7. **Output Checklist** - Provide a status summary of all addressed threads.

## Workflow

### Step 1: Initialize and Check Out PR
```bash
gh pr checkout <PR_NUMBER>
```

### Step 2: Fetch All Review Comments
Fetch all comments with thread metadata to identify which ones need a reply.
```bash
gh api --paginate repos/:owner/:repo/pulls/:id/comments | jq '.[] | {id: .id, user: .user.login, body, path, line, in_reply_to_id, diff_hunk}'
```

### Step 3: Filter Pending Comments (Anti-Duplication)
For each comment thread:
- Inspect `in_reply_to_id` to group comments into threads.
- If the latest comment in a thread is from the **ASSISTANT/USER** (you), mark it as **ALREADY_REPLIED**.
- If the comment is outdated (commit_id doesn't match current head), mark it as **OUTDATED** but still evaluate if the logic applies.
- Only process threads where the last message is from a **REVIEWER**.

### Step 4: Analyze and Draft Replies
For each **PENDING** thread:
1. **Locate Code**: Use `view_file` to see the current state of the lines mentioned in `path`.
2. **Evaluate**:
   - **Case A: Fixed**: If the code now reflects the reviewer's suggestion.
   - **Case B: Refuted**: If the suggestion is technically incorrect, out of scope, or better handled differently.
3. **Drafting**: Use professional, polite, and technically precise language.

### Step 5: Post Replies to Each Comment Thread

> [!IMPORTANT]
> **必须回复到每个评论线程中，而不是只发布一个总览性的 review。**
> 每个评论都需要单独的 reply comment，以便作者和评审者能清楚看到每条评论的处理状态。

#### 正确的回复方法

使用 REST API 的 `in_reply_to` 参数回复到每个评论线程：

```bash
# 回复到评论 ID 3006537516
gh api repos/:owner/:repo/pulls/:pr_number/comments \
  -X POST \
  -F body="Thank you for the suggestion. I have fixed this in commit xxx..." \
  -F in_reply_to=<comment_id>
```

#### 示例：批量回复多条评论

```bash
# 回复到评论 #1
gh api repos/enmotech/db-ops-skills/pulls/31/comments \
  -X POST \
  -F body="Fixed in commit 3e9f125. Changed X to Y." \
  -F in_reply_to=3006537516

# 回复到评论 #2
gh api repos/enmotech/db-ops-skills/pulls/31/comments \
  -X POST \
  -F body="Thank you for catching this. Added file=sys.stderr." \
  -F in_reply_to=3006537536
```

#### 错误做法

❌ **不要**只发布一个总览性的 review：
```bash
# 错误：这不是回复到每个评论线程
gh api repos/:owner/:repo/pulls/:pr_number/reviews -X POST \
  -F body="All comments addressed in commit xxx." \
  -F event="COMMENT"
```

✅ **正确**：逐条回复每个评论线程，然后再发布一个可选的总结 review。

### Step 6: Verify Replies

发布回复后，验证每个线程的最后一 条评论是否来自你：

```bash
gh api repos/:owner/:repo/pulls/:pr_number/comments | jq '
[.[] | {id, user: .user.login, in_reply_to_id}]
| group_by(if .in_reply_to_id then .in_reply_to_id else .id end)
| map({thread_id: .[0].in_reply_to_id // .[0].id, last_user: .[-1].user})'
```

## Reply Templates

### 🟢 Strategy: FIXED
Use when the suggestion has been implemented. Include the specific logic or file location as evidence.
> "Thank you for the suggestion. I have implemented this by [action] in [file:line]. This ensures [benefit/correctness]."

### 🔴 Strategy: REFUTE
Use when you disagree with the suggestion. Provide a strong technical rationale.
> "I understand the concern regarding [topic]. However, I have chosen to [current approach] because [technical reason]. [Optional: Alternative consideration]."

## Output Checklist Contract

After processing all comments, you MUST output a summary table. The `Comment ID` should be the unique identifier (e.g., `r2983403169`) extracted from the comment URL.

| Comment ID | Author | File:Line | Strategy | Status |
|-----------|--------|-----------|----------|--------|
| r2983403169 | user1  | path/to:12 | FIXED    | REPLIED |
| r2983403170 | user2  | path/to:45 | REFUTE   | REPLIED |
| r2983403171 | user1  | path/to:8  | -        | SKIPPED (Already Replied) |

## Quality Guidelines

- **No Duplication**: Never reply to a thread you or the user have already responded to.
- **Technical Rigor**: Always verify the code state before claiming something is "Fixed".
- **Tone**: Maintain a "collaborative expert" tone—avoid being overly submissive or unnecessarily argumentative.
- **Conciseness**: Keep replies focused on the technical point.
- **Reply to Each Thread**: Each comment thread must receive an individual reply, not a single summary review.

## Usage Example

```text
/pr-reply-advisor 31
```
*(Analyzes PR #31, groups threads, identifies 5 pending comments, drafts 5 unique replies, posts each reply to the correct thread, and shows the checklist.)*
