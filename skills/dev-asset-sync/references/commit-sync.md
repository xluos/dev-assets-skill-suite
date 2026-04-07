# Commit Sync

The sync skill is intended to trigger from commit-related user intent, similar to `commit-work`.

It should:

1. refresh working tree facts before commit
2. record the new HEAD commit after commit if it has not been recorded yet
3. keep `commits.md` append-only
