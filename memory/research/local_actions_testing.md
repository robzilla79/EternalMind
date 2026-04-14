# Local Actions Testing Research

## Problem
Testing GitHub Actions workflows locally before pushing to production is important for:
- Catching syntax errors early
- Testing environment-specific issues
- Reducing CI/CD pipeline costs
- Faster iteration cycles

## Tools Evaluated

### 1. act (GitHub Actions Runner)
**Best for:** Most use cases

**Pros:**
- Official community tool
- Runs workflows locally using Docker
- Supports most GitHub Actions features
- Good documentation
- Active maintenance

**Cons:**
- Requires Docker
- Some actions may not work perfectly locally
- Network-dependent actions need careful handling

**Installation:**
```bash
# macOS
brew install act

# Go installation
go install github.com/nektos/act@latest
```

### 2. Atuin (Action Runner)
- Less mature, smaller community

## Best Practices

1. **Use `act` for most workflows** - it's the standard
2. **Test with `--dry-run` first** - see what would execute
3. **Cache logs** - useful for debugging and audit trails
4. **Use specific events** - `-e pull_request` vs `-e push`
5. **Clean up regularly** - `docker system prune`

## Implementation Notes

The ForgeCore CLI wraps `act` with:
- Logging to memory/ directory
- Run history tracking
- Easy cleanup commands
- Status checking

## References
- https://github.com/nektos/act
- https://act.cli.sh/
