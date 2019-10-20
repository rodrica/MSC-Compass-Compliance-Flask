# Contribute

## Git commits

Please use the `fix:` and `feat:` prefixes for each commit. A feat adds new functionality, or changes behavior in a non breaking way.
When introducing a breaking change, please add `BREAKING CHANGE:` to the footer.

Examples:

```text
fix: Ensure type is cast to string
```

```text
feat: Removing length option from user's api

BREAKING CHANGE: Removed length option from user's api
```

The idea is that we'll be using https://github.com/relekang/python-semantic-release for automated semver versioning.
At this time this isn't implemented yet.

## Pull requests

All work should be done in new branches and then merged into the master branch via a pull request (PR).
Only PRs were the CI pipeline succeeds will be merged.
