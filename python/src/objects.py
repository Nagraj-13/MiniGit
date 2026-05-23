"""
MiniGit object model.

Defines the three core Git object types:
  - Blob  : raw file content
  - Tree  : directory listing (mode, name, hash entries)
  - Commit: snapshot metadata (tree, parents, author, message)

All objects follow Git's canonical format:
  header = b"<type> <size>\0"
  full   = header + content
  hash   = sha1(full).hexdigest()
  disk   = zlib.compress(full)
"""

from __future__ import annotations

import hashlib
import time
from typing import List, Optional, Tuple

import zlib


# ---------------------------------------------------------------------------
# Base object
# ---------------------------------------------------------------------------

class MiniGitObject:
    """
    Base class for all MiniGit objects.

    Stores an object type string and raw content bytes.
    Provides hashing (SHA-1) and serialization (zlib) following
    the Git object format.
    """

    def __init__(self, obj_type: str, content: bytes):
        self.type = obj_type
        self.content = content

    def hash(self) -> str:
        """Return the SHA-1 hex digest of the canonical object bytes."""
        header = f"{self.type} {len(self.content)}\0".encode()
        return hashlib.sha1(header + self.content).hexdigest()

    def serialize(self) -> bytes:
        """Return zlib-compressed canonical bytes for on-disk storage."""
        header = f"{self.type} {len(self.content)}\0".encode()
        return zlib.compress(header + self.content)

    @classmethod
    def deserialize(cls, data: bytes) -> MiniGitObject:
        """Decompress *data* and return a generic MiniGitObject."""
        decompressed = zlib.decompress(data)
        null_idx = decompressed.find(b"\0")
        header = decompressed[:null_idx]
        content = decompressed[null_idx + 1:]
        obj_type, _size = header.split(b" ", 1)
        return cls(obj_type.decode(), content)

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} type={self.type} hash={self.hash()[:8]}...>"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, MiniGitObject):
            return NotImplemented
        return self.hash() == other.hash()

    def __hash__(self) -> int:
        return hash(self.hash())


# ---------------------------------------------------------------------------
# Blob
# ---------------------------------------------------------------------------

class Blob(MiniGitObject):
    """A blob stores raw file content."""

    def __init__(self, content: bytes):
        super().__init__("blob", content)

    def get_content(self) -> bytes:
        return self.content


# ---------------------------------------------------------------------------
# Tree
# ---------------------------------------------------------------------------

class Tree(MiniGitObject):
    """
    A tree stores directory entries.

    Each entry is a tuple of (mode, name, obj_hash):
      - mode:     file mode string, e.g. "100644" or "40000"
      - name:     file or directory basename
      - obj_hash: 40-char hex SHA-1 of the referenced object

    Binary format per entry: b"<mode> <name>\0<20-byte-raw-hash>"
    """

    def __init__(self, entries: Optional[List[Tuple[str, str, str]]] = None):
        self.entries: List[Tuple[str, str, str]] = entries or []
        content = self._serialize_entries()
        super().__init__("tree", content)

    def _serialize_entries(self) -> bytes:
        """Build the binary tree content from entries (sorted by name)."""
        content = b""
        for mode, name, obj_hash in sorted(self.entries):
            content += f"{mode} {name}\0".encode()
            content += bytes.fromhex(obj_hash)
        return content

    def add_entry(self, mode: str, name: str, obj_hash: str) -> None:
        """Append an entry and recompute content bytes."""
        self.entries.append((mode, name, obj_hash))
        self.content = self._serialize_entries()

    @classmethod
    def from_content(cls, content: bytes) -> Tree:
        """Parse binary tree content into a Tree with populated entries."""
        tree = cls()
        i = 0
        while i < len(content):
            null_idx = content.find(b"\0", i)
            if null_idx == -1:
                break
            mode_name = content[i:null_idx].decode()
            mode, name = mode_name.split(" ", 1)
            if null_idx + 21 > len(content):
                raise ValueError("Corrupted tree object: unexpected end of data")
            obj_hash = content[null_idx + 1: null_idx + 21].hex()
            tree.entries.append((mode, name, obj_hash))
            i = null_idx + 21
        return tree


# ---------------------------------------------------------------------------
# Commit
# ---------------------------------------------------------------------------

class Commit(MiniGitObject):
    """
    A commit stores a snapshot reference plus metadata.

    Fields:
      tree_hash     – SHA-1 of the root tree
      parent_hashes – list of parent commit SHA-1s (empty for initial commit)
      author        – author identity string
      committer     – committer identity string
      message       – commit message body
      timestamp     – Unix epoch seconds
    """

    def __init__(
        self,
        tree_hash: str,
        parent_hashes: List[str],
        author: str,
        committer: str,
        message: str,
        timestamp: Optional[int] = None,
    ):
        self.tree_hash = tree_hash
        self.parent_hashes = parent_hashes
        self.author = author
        self.committer = committer
        self.message = message
        self.timestamp = timestamp or int(time.time())

        content = self._serialize_commit()
        super().__init__("commit", content)

    def _serialize_commit(self) -> bytes:
        """Build the commit body text and encode to bytes."""
        lines = [f"tree {self.tree_hash}"]
        for parent_hash in self.parent_hashes:
            lines.append(f"parent {parent_hash}")
        lines.append(f"author {self.author} {self.timestamp} +0000")
        lines.append(f"committer {self.committer} {self.timestamp} +0000")
        lines.append("")
        lines.append(self.message)
        return "\n".join(lines).encode()

    @classmethod
    def from_content(cls, content: bytes) -> Commit:
        """Parse commit body bytes into a Commit object."""
        lines = content.decode().split("\n")
        tree_hash = None
        parent_hashes: List[str] = []
        author = None
        committer = None
        message_start = 0
        timestamp = None

        for i, line in enumerate(lines):
            if line.startswith("tree "):
                tree_hash = line[5:]
            elif line.startswith("parent "):
                parent_hashes.append(line[7:])
            elif line.startswith("author "):
                author_parts = line[7:].rsplit(" ", 2)
                author = author_parts[0] if len(author_parts) >= 1 else "Unknown"
                if len(author_parts) >= 2:
                    try:
                        timestamp = int(author_parts[1])
                    except ValueError:
                        timestamp = None
            elif line.startswith("committer "):
                committer_parts = line[10:].rsplit(" ", 2)
                committer = committer_parts[0] if len(committer_parts) >= 1 else "Unknown"
            elif line == "":
                message_start = i + 1
                break

        message = "\n".join(lines[message_start:])
        return cls(tree_hash, parent_hashes, author, committer, message, timestamp)