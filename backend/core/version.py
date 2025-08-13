import json
import os
from pathlib import Path
from typing import Any, Dict


def get_version_info() -> Dict[str, Any]:
    """Get version information from version.json file"""
    try:
        # Look for version.json in the project root
        version_file = Path(__file__).parent.parent.parent / "version.json"

        if version_file.exists():
            with open(version_file, "r") as f:
                version_data = json.load(f)
        else:
            # Fallback version info
            version_data = {
                "app_version": "1.2.0",
                "api_version": "1.2.0",
                "build_date": "2025-01-13",
                "release_notes": "Development build",
            }

        # Add runtime information
        version_data.update(
            {
                "environment": os.getenv("ENVIRONMENT", "development"),
                "git_commit": os.getenv("GITHUB_SHA", "unknown")[:8]
                if os.getenv("GITHUB_SHA")
                else "local",
                "deployment_time": os.getenv("DEPLOYMENT_TIME", "unknown"),
            }
        )

        return version_data

    except Exception as e:
        # Fallback if anything goes wrong
        return {
            "app_version": "1.2.0",
            "api_version": "1.2.0",
            "build_date": "2025-01-13",
            "environment": os.getenv("ENVIRONMENT", "development"),
            "git_commit": "unknown",
            "deployment_time": "unknown",
            "error": str(e),
        }


# Cache version info on module load
_version_info = get_version_info()


def get_api_version() -> str:
    """Get just the API version string"""
    return _version_info.get("api_version", "1.2.0")


def get_full_version_info() -> Dict[str, Any]:
    """Get complete version information"""
    return _version_info.copy()
