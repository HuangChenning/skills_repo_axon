---
name: github-actions-debugging
description: Guide for debugging failing GitHub Actions workflows. Use this skill whenever CI is failing, a workflow run is red, the user mentions GitHub Actions or workflow errors, or needs to debug a failing check on a PR. Triggers on "CI failed", "workflow failed", "Actions error", "debug the failing check", or "why did my workflow fail".
---

# GitHub Actions Debugging

This skill helps you debug failing GitHub Actions workflows in pull requests.

## Process

1. Use the `list_workflow_runs` tool to look up recent workflow runs for the pull request and their status (or `gh run list` / `gh run view` if MCP tools are unavailable)
2. Use the `summarize_job_log_failures` tool to get an AI summary of the logs for failed jobs
3. If you need more information, use the `get_job_logs` or `get_workflow_run_logs` tool to get the full failure logs
4. Try to reproduce the failure locally in your environment
5. Fix the failing build and verify the fix before committing changes

## Output (Required)

Always surface to the user: (1) which workflow run and job(s) failed, (2) a short summary of the failure reason, (3) suggested fix or next step. If a tool is unavailable, use `gh run list`, `gh run view <id>`, and log URLs so the user can inspect.

## Common issues

- **Missing environment variables**: Check that all required secrets are configured
- **Version mismatches**: Verify action versions and dependencies are compatible
- **Permission issues**: Ensure the workflow has the necessary permissions
- **Timeout issues**: Consider splitting long-running jobs or increasing timeout values
