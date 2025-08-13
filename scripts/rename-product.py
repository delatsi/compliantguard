#!/usr/bin/env python3
"""
Product Rename Script for ThemisGuard

This script performs a comprehensive search and replace across the entire codebase
to change the product name from ThemisGuard to a new name.

Usage:
    python scripts/rename-product.py --old-name "ThemisGuard" --new-name "NewProductName"

Features:
- Preserves case variations (themisguard, ThemisGuard, THEMISGUARD)
- Updates file names and directory names
- Handles special cases (URLs, database names, etc.)
- Creates backup before changes
- Dry-run mode for preview
- Rollback capability
"""

import argparse
import json
import os
import re
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple


class ProductRenamer:
    def __init__(self, old_name: str, new_name: str, dry_run: bool = False):
        self.old_name = old_name
        self.new_name = new_name
        self.dry_run = dry_run
        self.project_root = Path(__file__).parent.parent
        self.backup_dir = (
            self.project_root
            / "backups"
            / f"rename-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        )

        # Generate case variations
        self.replacements = self._generate_replacements()

        # Files to skip
        self.skip_patterns = {
            ".git/*",
            "node_modules/*",
            "__pycache__/*",
            "*.pyc",
            ".aws-sam/*",
            "backups/*",
            "scripts/rename-product.py",  # Don't rename this script
        }

        # File extensions to process
        self.text_extensions = {
            ".py",
            ".js",
            ".jsx",
            ".ts",
            ".tsx",
            ".json",
            ".yaml",
            ".yml",
            ".md",
            ".txt",
            ".html",
            ".css",
            ".scss",
            ".toml",
            ".cfg",
            ".ini",
            ".env",
            ".gitignore",
            ".dockerignore",
        }

    def _generate_replacements(self) -> Dict[str, str]:
        """Generate all case variations of the name change"""
        old = self.old_name
        new = self.new_name

        return {
            # Exact case
            old: new,
            # All lowercase
            old.lower(): new.lower(),
            # All uppercase
            old.upper(): new.upper(),
            # Pascal case
            old.title(): new.title(),
            # Camel case (first letter lowercase)
            old[0].lower() + old[1:]: new[0].lower() + new[1:],
            # Snake case
            self._to_snake_case(old): self._to_snake_case(new),
            # Kebab case
            self._to_kebab_case(old): self._to_kebab_case(new),
            # URL friendly
            old.lower().replace(" ", ""): new.lower().replace(" ", ""),
        }

    def _to_snake_case(self, text: str) -> str:
        """Convert to snake_case"""
        return re.sub(r"(?<!^)(?=[A-Z])", "_", text).lower()

    def _to_kebab_case(self, text: str) -> str:
        """Convert to kebab-case"""
        return re.sub(r"(?<!^)(?=[A-Z])", "-", text).lower()

    def _should_skip_file(self, file_path: Path) -> bool:
        """Check if file should be skipped"""
        rel_path = file_path.relative_to(self.project_root)

        for pattern in self.skip_patterns:
            if file_path.match(pattern) or str(rel_path).startswith(
                pattern.rstrip("/*")
            ):
                return True

        return False

    def _is_text_file(self, file_path: Path) -> bool:
        """Check if file is a text file that should be processed"""
        return file_path.suffix.lower() in self.text_extensions

    def _create_backup(self):
        """Create backup of the entire project"""
        if self.dry_run:
            print(f"[DRY RUN] Would create backup at: {self.backup_dir}")
            return

        print(f"Creating backup at: {self.backup_dir}")
        self.backup_dir.mkdir(parents=True, exist_ok=True)

        # Copy entire project except excluded directories
        for item in self.project_root.iterdir():
            if item.name not in {
                ".git",
                "node_modules",
                "__pycache__",
                ".aws-sam",
                "backups",
            }:
                if item.is_dir():
                    shutil.copytree(item, self.backup_dir / item.name)
                else:
                    shutil.copy2(item, self.backup_dir / item.name)

        print("✅ Backup created successfully")

    def _find_files_to_process(self) -> List[Path]:
        """Find all files that need to be processed"""
        files = []

        for file_path in self.project_root.rglob("*"):
            if file_path.is_file() and not self._should_skip_file(file_path):
                if self._is_text_file(file_path) or self._contains_old_name_in_filename(
                    file_path
                ):
                    files.append(file_path)

        return files

    def _contains_old_name_in_filename(self, file_path: Path) -> bool:
        """Check if filename contains the old product name"""
        filename = file_path.name.lower()
        return self.old_name.lower() in filename

    def _process_file_content(self, file_path: Path) -> Tuple[bool, int]:
        """Process file content and return (changed, num_replacements)"""
        if not self._is_text_file(file_path):
            return False, 0

        try:
            # Read file content
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()

            original_content = content
            total_replacements = 0

            # Apply all replacements
            for old_text, new_text in self.replacements.items():
                if old_text in content:
                    content = content.replace(old_text, new_text)
                    replacements_count = original_content.count(old_text)
                    total_replacements += replacements_count

                    if not self.dry_run:
                        print(
                            f"  - Replaced '{old_text}' → '{new_text}' ({replacements_count} times)"
                        )

            if total_replacements > 0:
                if not self.dry_run:
                    with open(file_path, "w", encoding="utf-8") as f:
                        f.write(content)

                return True, total_replacements

        except Exception as e:
            print(f"❌ Error processing {file_path}: {e}")

        return False, 0

    def _rename_file_if_needed(self, file_path: Path) -> Path:
        """Rename file if it contains the old product name"""
        old_name = file_path.name
        new_name = old_name

        # Apply name replacements
        for old_text, new_text in self.replacements.items():
            if old_text in new_name:
                new_name = new_name.replace(old_text, new_text)

        if old_name != new_name:
            new_path = file_path.parent / new_name

            if self.dry_run:
                print(f"[DRY RUN] Would rename: {file_path} → {new_path}")
                return file_path
            else:
                print(f"📝 Renaming file: {old_name} → {new_name}")
                file_path.rename(new_path)
                return new_path

        return file_path

    def _update_special_files(self):
        """Handle special file updates that need custom logic"""

        # Update package.json name field
        package_json = self.project_root / "frontend" / "package.json"
        if package_json.exists():
            self._update_package_json(package_json)

        # Update SAM template stack names
        sam_config = self.project_root / "samconfig.toml"
        if sam_config.exists():
            self._update_sam_config(sam_config)

        # Update README title
        readme = self.project_root / "README.md"
        if readme.exists():
            self._update_readme(readme)

    def _update_package_json(self, package_json_path: Path):
        """Update package.json with new product name"""
        if self.dry_run:
            print(f"[DRY RUN] Would update package.json name field")
            return

        try:
            with open(package_json_path, "r") as f:
                data = json.load(f)

            if "name" in data and self.old_name.lower() in data["name"]:
                old_name = data["name"]
                data["name"] = data["name"].replace(
                    self.old_name.lower(), self.new_name.lower()
                )
                print(f"📦 Updated package.json name: {old_name} → {data['name']}")

                with open(package_json_path, "w") as f:
                    json.dump(data, f, indent=2)

        except Exception as e:
            print(f"❌ Error updating package.json: {e}")

    def _update_sam_config(self, sam_config_path: Path):
        """Update SAM config stack names"""
        if self.dry_run:
            print(f"[DRY RUN] Would update SAM config stack names")
            return

        try:
            with open(sam_config_path, "r") as f:
                content = f.read()

            # Update stack names
            old_stack_pattern = self.old_name.lower() + "-api"
            new_stack_pattern = self.new_name.lower() + "-api"

            if old_stack_pattern in content:
                content = content.replace(old_stack_pattern, new_stack_pattern)
                print(
                    f"📋 Updated SAM stack names: {old_stack_pattern} → {new_stack_pattern}"
                )

                with open(sam_config_path, "w") as f:
                    f.write(content)

        except Exception as e:
            print(f"❌ Error updating SAM config: {e}")

    def _update_readme(self, readme_path: Path):
        """Update README with new product name"""
        if self.dry_run:
            print(f"[DRY RUN] Would update README title")
            return

        try:
            with open(readme_path, "r") as f:
                content = f.read()

            # Update main title (assuming it's the first # heading)
            lines = content.split("\n")
            for i, line in enumerate(lines):
                if line.startswith(f"# {self.old_name}"):
                    lines[i] = f"# {self.new_name}"
                    print(f"📖 Updated README title: {self.old_name} → {self.new_name}")
                    break

            with open(readme_path, "w") as f:
                f.write("\n".join(lines))

        except Exception as e:
            print(f"❌ Error updating README: {e}")

    def run(self):
        """Execute the complete renaming process"""
        print(
            f"🔄 {'DRY RUN: ' if self.dry_run else ''}Renaming product from '{self.old_name}' to '{self.new_name}'"
        )
        print(f"📁 Project root: {self.project_root}")
        print()

        # Create backup (unless dry run)
        if not self.dry_run:
            self._create_backup()

        # Find files to process
        print("🔍 Finding files to process...")
        files_to_process = self._find_files_to_process()
        print(f"📄 Found {len(files_to_process)} files to process")
        print()

        # Process file contents and rename files
        total_files_changed = 0
        total_replacements = 0

        for file_path in files_to_process:
            rel_path = file_path.relative_to(self.project_root)

            # Process file content
            content_changed, num_replacements = self._process_file_content(file_path)

            # Rename file if needed
            new_file_path = self._rename_file_if_needed(file_path)

            if content_changed or new_file_path != file_path:
                if content_changed:
                    print(f"✏️  {rel_path} ({num_replacements} replacements)")
                total_files_changed += 1
                total_replacements += num_replacements

        # Handle special files
        print("\n🔧 Updating special configuration files...")
        self._update_special_files()

        # Summary
        print(f"\n{'🎯 DRY RUN COMPLETE' if self.dry_run else '✅ RENAMING COMPLETE'}")
        print(f"📊 Files processed: {total_files_changed}")
        print(f"🔄 Total replacements: {total_replacements}")

        if not self.dry_run:
            print(f"💾 Backup location: {self.backup_dir}")
            print("\n📋 Next steps:")
            print("1. Test the application thoroughly")
            print("2. Update any external references (domains, documentation)")
            print("3. Update Stripe product names if needed")
            print("4. Commit changes to git")
        else:
            print("\n🚀 Run without --dry-run to apply changes")


def create_rollback_script(backup_dir: Path, project_root: Path):
    """Create a rollback script"""
    rollback_script = project_root / "scripts" / "rollback-rename.sh"

    script_content = f"""#!/bin/bash
# Rollback script generated by rename-product.py
# This will restore the project from backup

BACKUP_DIR="{backup_dir}"
PROJECT_ROOT="{project_root}"

echo "🔄 Rolling back product rename..."
echo "📁 Backup source: $BACKUP_DIR"
echo "📁 Target: $PROJECT_ROOT"

# Confirmation prompt
read -p "Are you sure you want to rollback? This will overwrite current files. (y/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Rollback cancelled"
    exit 1
fi

# Remove current files (except .git and backups)
find "$PROJECT_ROOT" -maxdepth 1 -not -name ".git" -not -name "backups" -not -name "." -exec rm -rf {{}} + 2>/dev/null || true

# Restore from backup
cp -r "$BACKUP_DIR"/* "$PROJECT_ROOT/"

echo "✅ Rollback complete"
echo "🔍 Please verify the restoration and test your application"
"""

    with open(rollback_script, "w") as f:
        f.write(script_content)

    rollback_script.chmod(0o755)
    print(f"📜 Rollback script created: {rollback_script}")


def main():
    parser = argparse.ArgumentParser(
        description="Rename product across entire codebase"
    )
    parser.add_argument(
        "--old-name", required=True, help="Current product name (e.g., 'ThemisGuard')"
    )
    parser.add_argument(
        "--new-name", required=True, help="New product name (e.g., 'NewProductName')"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Preview changes without applying them"
    )

    args = parser.parse_args()

    # Validation
    if args.old_name == args.new_name:
        print("❌ Error: Old name and new name are the same")
        return

    if not re.match(r"^[a-zA-Z][a-zA-Z0-9]*$", args.new_name):
        print(
            "❌ Error: New name should start with a letter and contain only alphanumeric characters"
        )
        return

    # Run renamer
    renamer = ProductRenamer(args.old_name, args.new_name, args.dry_run)
    renamer.run()

    # Create rollback script if not dry run
    if not args.dry_run:
        create_rollback_script(renamer.backup_dir, renamer.project_root)


if __name__ == "__main__":
    main()
