# CompliantGuard Scripts

This directory contains utility scripts for managing CompliantGuard infrastructure and development.

## Development Scripts

### `setup-local-dev.sh`
Sets up local development environment with AWS DynamoDB connection.

**Usage:**
```bash
./scripts/setup-local-dev.sh
```

**What it does:**
- Creates DynamoDB table `themisguard-users`
- Sets up `.env` files for backend and frontend
- Installs Python and Node.js dependencies
- Provides startup instructions

## SSL & Domain Scripts

### `setup-ssl-cert.sh`
Creates SSL certificate for custom domain `compliantguard.datfunc.com`.

**Usage:**
```bash
./scripts/setup-ssl-cert.sh
```

**Requirements:**
- AWS CLI configured
- Access to datfunc.com DNS management

## Debugging Scripts

### `debug-frontend-stack.sh`
Debugs CloudFormation frontend stack deployment issues.

**Usage:**
```bash
./scripts/debug-frontend-stack.sh
```

**What it checks:**
- Frontend stack existence and status
- Stack outputs and resources
- CloudFront distribution resources

### `fix-cloudfront-manually.sh`
Checks and diagnoses manually created CloudFront distribution configuration.

**Usage:**
```bash
./scripts/fix-cloudfront-manually.sh
```

**What it checks:**
- CloudFront origin configuration
- S3 static website hosting
- Default root object settings
- Provides fix suggestions

## Other Utility Scripts

See the main `/scripts/` directory for additional utility scripts:
- `asset_crawler.py` - GCP asset discovery
- `developer_dashboard.py` - Development dashboard
- `executive_dashboard.py` - Executive metrics
- `violation_analyzer.py` - Compliance violation analysis
- `rename-product.py` - Product rebranding utility

## Usage Notes

1. **Make scripts executable:**
   ```bash
   chmod +x scripts/*.sh
   ```

2. **Run from project root:**
   ```bash
   # Good
   ./scripts/setup-local-dev.sh
   
   # Also works
   cd scripts && ./setup-local-dev.sh
   ```

3. **AWS credentials:** Most scripts require AWS CLI to be configured with appropriate permissions.

4. **Environment:** Scripts are designed to work in both development and production environments.