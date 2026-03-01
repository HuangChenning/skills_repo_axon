---
name: pr-comments-analyzer
description: Analyze GitHub PR comments and provide structured recommendations for review. Use this skill whenever the user explicitly requests to analyze PR comments, review PR feedback, address PR comments, or needs help understanding and prioritizing review comments on a pull request. This skill provides systematic analysis of each comment with feasibility assessments and prioritized recommendations, but does NOT make any code changes automatically.
---

# PR Comments Analyzer

This skill helps you systematically analyze GitHub PR comments and provide structured, actionable recommendations. It does NOT make code changes automatically — all recommendations require user review and approval.

## When to Use This Skill

Use this skill when the user explicitly requests:
- "Analyze PR comments"
- "Review PR feedback"
- "Address PR comments"
- "Help me understand these review comments"
- "What should I do with these PR comments?"
- Similar explicit requests about PR comment analysis

## Workflow

### Step 1: Identify the PR

First, identify which PR to analyze. The user may provide:
- A PR number (e.g., "PR 123")
- A PR URL
- The current PR (if already checked out)

If the PR is not checked out, check it out:
```bash
gh pr checkout <pr-number>
```

### Step 2: Fetch PR Comments

Use the GitHub CLI to fetch all comments on the PR:

```bash
gh api --paginate repos/[owner]/[repo]/pulls/[pr-number]/comments | jq '.[] | {user: .user.login, body, path, line, original_line, created_at, in_reply_to_id, pull_request_review_id, commit_id}'
```

### Step 3: Analyze Each Comment Systematically

For EACH comment, perform the following analysis:

**a. Extract comment information:**
```
(index). From [user] on [file]:[lines] — [comment body]
```

**b. Analyze code context:**
- Read the target file and surrounding code (typically 10-20 lines around the mentioned line)
- Understand the current implementation
- Identify the scope of suggested changes

**c. Feasibility assessment:**

- **High Feasibility**: Simple, clear, low-risk changes
  - Code style/formatting fixes
  - Variable renaming
  - Adding missing error handling
  - Simple logic improvements
  - Documentation improvements

- **Medium Feasibility**: Moderate complexity changes
  - Refactoring small functions
  - Adding new utility methods
  - Improving error messages
  - Performance optimizations
  - Adding tests for existing code

- **Low Feasibility**: Complex or high-risk changes
  - Architectural changes
  - Complex business logic
  - Breaking changes
  - Requires extensive testing
  - Affects multiple files

**d. Generate recommendation:**
```
Recommendation: [APPLY/REVIEW/IGNORE]
Reasoning: [Detailed explanation]
Estimated Effort: [LOW/MEDIUM/HIGH]
Code Impact: [SMALL/MEDIUM/LARGE]
Priority: [HIGH/MEDIUM/LOW]
```

### Step 4: Generate Comprehensive Summary

After analyzing all comments, generate a structured summary:

```markdown
## PR Comments Analysis Summary

### Statistics
- Total Comments Reviewed: [number]
- Recommended to Apply: [number]
- Recommended to Ignore: [number]
- Requires Further Discussion: [number]

### Recommended Changes (by priority)

#### HIGH Priority - Apply First
1. [Comment #] - [Brief description] - Effort: [LOW/MEDIUM/HIGH]
   - File: [file_path]
   - Reason: [why it's important]
   - Impact: [code scope]

#### MEDIUM Priority - Consider Applying
1. [Comment #] - [Brief description] - Effort: [LOW/MEDIUM/HIGH]
   - File: [file_path]
   - Reason: [why it's beneficial]
   - Impact: [code scope]

#### LOW Priority - Optional
1. [Comment #] - [Brief description] - Effort: [LOW/MEDIUM/HIGH]
   - File: [file_path]
   - Reason: [nice to have]
   - Impact: [code scope]

### Recommended to Ignore
1. [Comment #] - [Brief description]
   - Reason: [why to ignore]
   - Alternative: [suggested approach if any]

### Requires Discussion
1. [Comment #] - [Brief description]
   - Issue: [what's unclear]
   - Questions: [what to ask reviewer]

### Implementation Plan
**Phase 1 (Quick Wins):** [list of HIGH priority, LOW effort items]
**Phase 2 (Moderate Changes):** [list of MEDIUM priority items]
**Phase 3 (Consider Later):** [list of LOW priority items]
```

## Analysis Criteria

### Feasibility Factors
- **Clarity**: How clear is the comment's intent?
- **Risk**: What's the risk of introducing bugs?
- **Scope**: How much code needs to be changed?
- **Testing**: How much testing is required?
- **Dependencies**: Will it affect other components?

### Priority Factors
- **Impact**: How much does it improve the code?
- **Urgency**: Is it blocking the PR merge?
- **Standards**: Does it violate coding standards?
- **Performance**: Does it affect performance?
- **Security**: Does it address security concerns?

## Important Constraints

1. **Read-only analysis**: This skill only analyzes and recommends. It does NOT make code changes.
2. **Context-aware**: Always read the actual code mentioned in comments before making recommendations.
3. **Prioritize by impact**: HIGH priority items are those that are important AND relatively easy to implement.
4. **Flag blockers**: Any comments that are explicitly blocking the PR merge should be marked HIGH priority regardless of effort.

## Output Format

Always present the analysis in the structured format shown above. Start with individual comment analysis, then provide the comprehensive summary with implementation phases.
