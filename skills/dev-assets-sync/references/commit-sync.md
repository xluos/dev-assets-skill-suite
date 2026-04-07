# Commit Sync

The sync skill is intended to trigger from commit-related user intent, similar to `commit-work`.

It should:

1. summarize the current session into reusable project facts before commit
2. write those facts into the right asset files instead of only refreshing git facts
3. record the new HEAD commit after commit if it has not been recorded yet
4. keep `commits.md` append-only
