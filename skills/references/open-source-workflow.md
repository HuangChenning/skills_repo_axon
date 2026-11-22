# 开源贡献完整流程（与 git skills 衔接）

本流程由 **git-upstream-sync**、**git-commit-message**、**git-pr-creator**、**git-pr-cleanup** 等技能与手工步骤组成。

| 阶段 | 步骤 | 使用技能 / 操作 |
|------|------|-----------------|
| 准备 | Fork、Clone 自己的 fork | 手工 |
| 开始贡献 | 配置 upstream、从最新上游拉分支 | **git-upstream-sync** |
| 开发 | 改代码、提交（规范 message） | **git-commit-message** |
| 提 PR | Push 到 origin，生成 PR 标题与描述 | **git-pr-creator**（生成后由用户执行 `gh pr create` 或网页创建） |
| Review | 分析评论、根据评论修改、CI 失败排查 | **pr-comments-analyzer**、**receiving-code-review**、**github-actions-debugging** |
| 合并 | 上游合并 PR | 维护者操作 |
| 收尾 | 同步 fork、删已合并分支 | **git-pr-cleanup** |

维护本表时请同步更新所有引用此流程的 skill（如 git-upstream-sync、git-pr-cleanup）。

**维护者**：发版、起草 release notes、打 tag 等见 **git-release**。
