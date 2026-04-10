# Commit Sync

The sync skill is triggered by commit-related moments, but it no longer mirrors commit history into `.dev-assets/`.

It should:

1. summarize only what this commit should leave behind
2. update only the memory sections directly affected by this commit
3. update lightweight commit metadata when needed
4. leave detailed implementation history in Git
