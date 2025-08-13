# Development Workflow

## Pre-commit Validation Setup

 **Husky + Pre-commit hooks are now configured!**

### What happens on every commit:
1. **ESLint** - Code quality and style validation
2. **Tests** - All vitest unit tests must pass
3. **Build** - Frontend must build successfully
4. **Dependency check** - Ensures all packages are installed

### Commands you can run locally:

```bash
# Run full validation (same as pre-commit)
npm run validate

# Individual checks
npm run lint          # ESLint only
npm run test         # Tests only  
npm run build        # Build only

# Force run pre-commit check
npm run precommit
```

### How this saves GitHub Action tokens:

- **Before**: Broken code reached CI, wasting tokens on failed builds
- **Now**: Issues caught locally before commit, CI only runs on clean code

### If pre-commit fails:
1. Fix the reported issues
2. Stage your changes: `git add .`
3. Commit again: `git commit -m "your message"`

### Emergency bypass (use sparingly):
```bash
git commit -m "your message" --no-verify
```

## Testing Infrastructure

- **Framework**: Vitest + Testing Library
- **Coverage**: Available with `npm run test:coverage`  
- **E2E**: Playwright tests in `/tests` directory
- **Test files**: `/src/test/*.{test,spec}.{js,jsx}`

## Commands Reference

- `npm run validate` - Full validation suite
- `npm run dev` - Start development server
- `npm run build` - Production build
- `npm run test` - Interactive test mode
- `npm run test:run` - Single test run
- `npm run lint` - ESLint check