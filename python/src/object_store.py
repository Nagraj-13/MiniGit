"""
Object store — reading and writing MiniGit objects on disk.

Objects live under  .minigit/objects/<sha[:2]>/<sha[2:]>
and are stored as zlib-compressed  b"<type> <size>\\0<content>".
"""

from pathlib import Path
from typing import Optional, Set

from src.objects import MiniGitObject


class ObjectStore:
    """Low-level object I/O against .minigit/objects/."""

    def __init__(self, objects_dir: Path):
        self.objects_dir = objects_dir

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------

    def store(self, obj: MiniGitObject) -> str:
        """
        Persist *obj* to disk (idempotent) and return its SHA-1 hex hash.
        """
        obj_hash = obj.hash()
        obj_directory = self.objects_dir / obj_hash[:2]
        obj_file = obj_directory / obj_hash[2:]

        if not obj_directory.exists():
            obj_directory.mkdir(parents=True, exist_ok=True)

        if not obj_file.exists():
            obj_file.write_bytes(obj.serialize())

        return obj_hash

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    def load(self, obj_hash: str) -> MiniGitObject:
        """
        Read and deserialize the object identified by *obj_hash*.

        Raises FileNotFoundError if the object does not exist on disk.
        """
        obj_dir = self.objects_dir / obj_hash[:2]
        obj_file = obj_dir / obj_hash[2:]

        if not obj_file.exists():
            raise FileNotFoundError(f"Object {obj_hash} not found")

        return MiniGitObject.deserialize(obj_file.read_bytes())

    def exists(self, obj_hash: str) -> bool:
        """Return True if *obj_hash* is stored on disk."""
        obj_file = self.objects_dir / obj_hash[:2] / obj_hash[2:]
        return obj_file.exists()

    # ------------------------------------------------------------------
    # Enumeration (used by GC)
    # ------------------------------------------------------------------

    def list_all_hashes(self) -> Set[str]:
        """
        Return the set of all object hashes currently stored on disk.
        """
        hashes: Set[str] = set()
        if not self.objects_dir.exists():
            return hashes

        for prefix_dir in self.objects_dir.iterdir():
            if not prefix_dir.is_dir() or len(prefix_dir.name) != 2:
                continue
            for obj_file in prefix_dir.iterdir():
                if obj_file.is_file():
                    hashes.add(prefix_dir.name + obj_file.name)

        return hashes

    def delete(self, obj_hash: str) -> bool:
        """
        Remove *obj_hash* from disk.  Returns True if it existed.
        Also cleans up the prefix directory if it becomes empty.
        """
        obj_dir = self.objects_dir / obj_hash[:2]
        obj_file = obj_dir / obj_hash[2:]

        if not obj_file.exists():
            return False

        obj_file.unlink()

        # Remove empty prefix directory
        try:
            if obj_dir.exists() and not any(obj_dir.iterdir()):
                obj_dir.rmdir()
        except OSError:
            pass

        return True
