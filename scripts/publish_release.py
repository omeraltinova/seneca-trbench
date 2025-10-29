#!/usr/bin/env python3
"""
Release publisher script for Turkish Benchmark System.
Copies whitelisted files to Github/ directory, excluding sensitive data.
"""

import os
import shutil
from pathlib import Path

# Project root (parent of Github/)
PROJECT_ROOT = Path(__file__).parent.parent.parent
GITHUB_DIR = PROJECT_ROOT / "Github"

# Whitelist of files/directories to copy
WHITELIST = [
    # Core Python files
    "benchmark.py",
    "evaluator.py",
    "judge.py",
    "reporter.py",
    "model_registry.py",
    "rescore.py",
    "compare_results.py",
    "analyze_saq.py",
    "full_analysis.py",
    
    # Comparison scripts
    "run_comparison_test.py",
    "run_gpt5_comparison.py",
    "run_claude_comparison.py",
    
    # Data files
    "MCQ-Türkçe Benchmark.json",
    "SAQ-Türkçe-Benchmark.json",
    
    # Documentation
    "README.md",
    "QUICK_START.md",
    "USAGE_GUIDE.md",
    "CONTRIBUTING.md",
    "INDEX.md",
    "MODELS.md",
    "LICENSE",
    
    # Configuration
    "requirements.txt",
    "install.sh",
    
    # Modules
    "models/",
    "utils/",
]

# Files to exclude even if in whitelist directories
EXCLUDE_PATTERNS = [
    "__pycache__",
    "*.pyc",
    "*.pyo",
    "*.log",
    ".DS_Store",
    "models/models--",  # Exclude downloaded models
    "models/.locks",    # Exclude lock files
]


def should_exclude(path: Path) -> bool:
    """Check if file should be excluded."""
    for pattern in EXCLUDE_PATTERNS:
        if pattern in str(path):
            return True
    return False


def copy_file_or_dir(src: Path, dst: Path):
    """Copy file or directory, creating parent dirs as needed."""
    if src.is_file():
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        print(f"✓ Copied: {src.relative_to(PROJECT_ROOT)}")
    elif src.is_dir():
        for item in src.rglob("*"):
            if should_exclude(item):
                continue
            if item.is_file():
                rel_path = item.relative_to(src)
                dest_file = dst / rel_path
                dest_file.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(item, dest_file)
                print(f"✓ Copied: {item.relative_to(PROJECT_ROOT)}")


def main():
    """Main release publisher."""
    print("=" * 60)
    print("Turkish Benchmark - Release Publisher")
    print("=" * 60)
    print()
    
    # Ensure Github dir exists
    GITHUB_DIR.mkdir(exist_ok=True)
    
    # Copy whitelisted files
    print("Copying whitelisted files...")
    for item in WHITELIST:
        src = PROJECT_ROOT / item
        if not src.exists():
            print(f"⚠ Skipped (not found): {item}")
            continue
        
        # Determine destination
        if src.is_dir():
            dst = GITHUB_DIR / item.rstrip("/")
        else:
            dst = GITHUB_DIR / item
        
        copy_file_or_dir(src, dst)
    
    print()
    print("=" * 60)
    print("✓ Release package ready in Github/")
    print("=" * 60)
    print()
    print("Next steps:")
    print("1. Review Github/ directory")
    print("2. Test: cd Github && python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt")
    print("3. Push to GitHub or create release ZIP")


if __name__ == "__main__":
    main()

