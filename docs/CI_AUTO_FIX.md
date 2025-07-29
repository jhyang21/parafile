# CI/CD Auto-Fix Pipeline

## Overview

Our CI/CD pipeline now automatically fixes common code formatting and style issues instead of just failing when linting tools detect problems.

## How It Works

### Auto-Fix Process (Python 3.11 only)

When you push code or create a pull request, the pipeline will:

1. **Auto-Fix Phase**:
   - Run `black` to format code according to PEP 8
   - Run `isort` to organize import statements
   - Run `autopep8` to fix common flake8 style issues

2. **Auto-Commit Phase**:
   - If any changes were made, commit them with message: `Auto-fix: Apply black, isort, and autopep8 formatting`
   - Push changes back to the same branch (for direct pushes) or PR branch (for pull requests)

3. **Verification Phase**:
   - Re-run all linting tools to verify everything is properly formatted
   - Run `mypy` for type checking (manual fixes required if issues found)

### Check-Only Process (Python 3.9, 3.10)

For other Python versions, the pipeline runs in check-only mode to ensure compatibility.

## What Gets Auto-Fixed

- **Black**: Code formatting (line length, quotes, spacing, etc.)
- **isort**: Import statement organization and sorting
- **autopep8**: Common PEP 8 style violations that flake8 detects
- **mypy**: Type errors require manual intervention (NOT auto-fixed)

## Benefits

- **No More Formatting Failures**: Your code will be automatically formatted to project standards
- **Consistent Style**: All code follows the same formatting rules
- **Faster Development**: No need to manually run formatters before committing
- **Focus on Logic**: Spend time on actual code issues, not formatting

## Important Notes

- Auto-fixes only run on **Python 3.11** to avoid conflicts
- Changes are committed and pushed automatically
- For fork-based pull requests, auto-fixes are applied but not pushed (security measure)
- Type errors from mypy still require manual fixes
- The pipeline will still fail if there are remaining linting issues after auto-fixing

## Manual Override

If you need to run the formatters locally:

```bash
# Format your code manually
black .
isort .
autopep8 --in-place --recursive --aggressive --aggressive .

# Check for any remaining issues
flake8
mypy src/
```

## Workflow Permissions

The pipeline has been granted `contents: write` and `pull-requests: write` permissions to enable automatic commits. 