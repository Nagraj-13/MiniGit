"""
Index (staging area) manager for MiniGit.

Handles:
  - Loading / saving the JSON index file
  - Adding files and directories to the index
  - .minigitignore pattern filtering
"""

import fnmatch
import json
from pathlib import Path
from typing import Dict, List

from src.objects import Blob
from src.object_store import ObjectStore


class IndexManager:
    """Manages the staging area (index) and .minigitignore filtering."""

    def __init__(self, repo_path: Path, index_file: Path, object_store: ObjectStore):
        self.repo_path = repo_path
        self.index_file = index_file
        self.object_store = object_store
        self._ignore_patterns: List[str] = []
        self._load_ignore_patterns()

    # ------------------------------------------------------------------
    # .minigitignore
    # ------------------------------------------------------------------

    def _load_ignore_patterns(self) -> None:
        """Load patterns from .minigitignore at the repo root (if it exists)."""
        ignore_file = self.repo_path / ".minigitignore"
        if not ignore_file.exists():
            self._ignore_patterns = []
            return

        patterns: List[str] = []
        for line in ignore_file.read_text().splitlines():
            stripped = line.strip()
            if stripped and not stripped.startswith("#"):
                patterns.append(stripped)
        self._ignore_patterns = patterns

    def is_ignored(self, rel_path: str) -> bool:
        """
        Return True if *rel_path* should be ignored.

        Always ignores anything inside ``.minigit/``.
        Then checks each .minigitignore pattern using fnmatch.
        Directory patterns (ending with ``/``) match any path component.
        """
        # Always skip internal directory
        parts = rel_path.replace("\\", "/").split("/")
        if ".minigit" in parts:
            return True

        for pattern in self._ignore_patterns:
            # Directory pattern: e.g. "__pycache__/" matches any component
            if pattern.endswith("/"):
                dir_name = pattern.rstrip("/")
                if dir_name in parts:
                    return True
            else:
                # Match against the full relative path and the basename
                if fnmatch.fnmatch(rel_path, pattern):
                    return True
                if fnmatch.fnmatch(parts[-1], pattern):
                    return True

        return False

    # ------------------------------------------------------------------
    # Index I/O
    # ------------------------------------------------------------------

    def load(self) -> Dict[str, str]:
        """Load the index as a dict mapping relative paths to blob hashes."""
        if not self.index_file.exists():
            return {}
        try:
            return json.loads(self.index_file.read_text())
        except Exception:
            return {}

    def save(self, index: Dict[str, str]) -> None:
        """Persist *index* to disk as formatted JSON."""
        self.index_file.write_text(json.dumps(index, indent=2))

    # ------------------------------------------------------------------
    # Staging operations
    # ------------------------------------------------------------------

    def add_file(self, path: str) -> None:
        """Stage a single file by creating a blob and updating the index."""
        full_path = self.repo_path / path
        if not full_path.exists():
            raise FileNotFoundError(f"File {path} not found")

        # Normalise to posix separators for cross-platform consistency
        rel_path = Path(path).as_posix()

        if self.is_ignored(rel_path):
            print(f"Skipped (ignored): {rel_path}")
            return

        content = full_path.read_bytes()
        blob = Blob(content)
        blob_hash = self.object_store.store(blob)

        index = self.load()
        index[rel_path] = blob_hash
        self.save(index)
        print(f"Added {rel_path}")

    def add_directory(self, path: str) -> None:
        """Recursively stage all files in a directory."""
        full_path = self.repo_path / path
        if not full_path.exists():
            raise FileNotFoundError(f"Directory {path} not found")
        if not full_path.is_dir():
            raise ValueError(f"{path} is not a directory")

        index = self.load()
        added_count = 0

        for file_path in full_path.rglob("*"):
            if not file_path.is_file():
                continue

            relative_path = file_path.relative_to(self.repo_path).as_posix()

            if self.is_ignored(relative_path):
                continue

            content = file_path.read_bytes()
            blob = Blob(content)
            blob_hash = self.object_store.store(blob)

            if index.get(relative_path) != blob_hash:
                index[relative_path] = blob_hash
                added_count += 1

        self.save(index)
        if added_count > 0:
            print(f"Added {added_count} files from directory {path}")
        else:
            print(f"Directory {path} is already up to date")

    def add_path(self, path: str) -> None:
        """Stage a path — delegates to add_file or add_directory."""
        full_path = self.repo_path / path
        if not full_path.exists():
            raise FileNotFoundError(f"Path {path} not found")

        if full_path.is_file():
            self.add_file(path)
        elif full_path.is_dir():
            self.add_directory(path)
        else:
            raise ValueError(f"{path} is neither a file nor a directory")
