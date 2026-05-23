"""
Repository — the main facade for MiniGit.

Composes ObjectStore, IndexManager, and BranchManager to expose
high-level operations: init, commit, status, diff, log, gc, etc.
"""

import difflib
import json
import time
from pathlib import Path
from typing import Dict, List, Optional

from src.objects import Blob, Commit, MiniGitObject, Tree
from src.object_store import ObjectStore
from src.index_manager import IndexManager
from src.branch_manager import BranchManager


class Repository:
    """
    High-level MiniGit repository.

    All public methods correspond 1-to-1 with CLI commands.
    """

    def __init__(self, path: str = "."):
        self.path = Path(path).resolve()
        self.git_dir = self.path / ".minigit"

        # Directory layout
        self.objects_dir = self.git_dir / "objects"
        self.refs_dir = self.git_dir / "refs"
        self.heads_dir = self.refs_dir / "heads"
        self.hooks_dir = self.git_dir / "hooks"
        self.info_dir = self.git_dir / "info"
        self.logs_dir = self.git_dir / "logs"

        # Key files
        self.head_file = self.git_dir / "HEAD"
        self.index_file = self.git_dir / "index"

        # Sub-modules (lazily valid — callers must check git_dir.exists())
        self.objects = ObjectStore(self.objects_dir)
        self.index = IndexManager(self.path, self.index_file, self.objects)
        self.branches = BranchManager(
            self.path, self.head_file, self.heads_dir, self.objects
        )

    # ------------------------------------------------------------------
    # init
    # ------------------------------------------------------------------

    def init(self) -> bool:
        """Create the .minigit directory layout.  Returns False if it exists."""
        if self.git_dir.exists():
            return False
        try:
            for d in (
                self.objects_dir, self.refs_dir, self.heads_dir,
                self.info_dir, self.logs_dir, self.hooks_dir,
            ):
                d.mkdir(parents=True, exist_ok=True)

            self.head_file.write_text("ref: refs/heads/master\n")
            self.index.save({})
            print(f"Initialized empty MiniGit repository in {self.git_dir}")
            return True
        except Exception as e:
            print(f"Failed to initialize repository: {e}")
            return False

    # ------------------------------------------------------------------
    # add (delegated)
    # ------------------------------------------------------------------

    def add_path(self, path: str) -> None:
        """Stage a file or directory."""
        self.index.add_path(path)

    # ------------------------------------------------------------------
    # commit
    # ------------------------------------------------------------------

    def commit(self, message: str, author: str = "MiniGit user <user@minigit>") -> Optional[str]:
        """Create a new commit from the current index."""
        idx = self.index.load()
        if not idx:
            print("Nothing to commit, working tree clean")
            return None

        tree_hash = self.branches.create_tree_from_index(idx)

        current_branch = self.branches.get_current_branch()
        parent_commit = self.branches.get_branch_commit(current_branch)
        parent_hashes = [parent_commit] if parent_commit else []

        # Detect no-change commits
        if parent_commit:
            parent_obj = self.objects.load(parent_commit)
            parent_data = Commit.from_content(parent_obj.content)
            if tree_hash == parent_data.tree_hash:
                print("Nothing to commit, working tree clean")
                return None

        commit_obj = Commit(
            tree_hash=tree_hash,
            parent_hashes=parent_hashes,
            author=author,
            committer=author,
            message=message,
        )
        commit_hash = self.objects.store(commit_obj)
        self.branches.set_branch_commit(current_branch, commit_hash)

        short = commit_hash[:7]
        print(f"[{current_branch} {short}] {message}")
        return commit_hash

    # ------------------------------------------------------------------
    # checkout (delegated)
    # ------------------------------------------------------------------

    def checkout(self, branch: str, create_branch: bool) -> None:
        """Switch branches (creating if *create_branch* is True)."""
        self.branches.checkout(branch, create_branch, self.index.save)

    # ------------------------------------------------------------------
    # branch (delegated)
    # ------------------------------------------------------------------

    def branch(self, branch_name: Optional[str], delete: bool = False) -> None:
        """List, create, or delete branches."""
        self.branches.branch(branch_name, delete)

    # ------------------------------------------------------------------
    # log
    # ------------------------------------------------------------------

    def log(self, max_count: int = 10) -> None:
        """Print commit history for the current branch."""
        current_branch = self.branches.get_current_branch()
        commit_hash = self.branches.get_branch_commit(current_branch)

        if not commit_hash:
            print("No commits yet")
            return

        count = 0
        while commit_hash and count < max_count:
            commit_obj = self.objects.load(commit_hash)
            commit = Commit.from_content(commit_obj.content)

            print(f"commit {commit_hash}")
            print(f"Author: {commit.author}")
            print(f"Date:   {time.ctime(commit.timestamp)}")
            print(f"\n    {commit.message}\n")

            commit_hash = commit.parent_hashes[0] if commit.parent_hashes else None
            count += 1

    # ------------------------------------------------------------------
    # status
    # ------------------------------------------------------------------

    def status(self) -> None:
        """Print working-tree status (staged, unstaged, untracked, deleted)."""
        current_branch = self.branches.get_current_branch()
        print(f"On branch {current_branch}")

        idx = self.index.load()
        current_commit_hash = self.branches.get_branch_commit(current_branch)

        # Files from the last commit's tree
        committed_files: Dict[str, str] = {}
        if current_commit_hash:
            try:
                commit_obj = self.objects.load(current_commit_hash)
                commit = Commit.from_content(commit_obj.content)
                if commit.tree_hash:
                    committed_files = self.branches.build_index_from_tree(commit.tree_hash)
            except Exception:
                committed_files = {}

        # Current working-tree state
        working_files: Dict[str, str] = {}
        for item in self._get_all_files():
            rel_path = item.relative_to(self.path).as_posix()
            try:
                blob = Blob(item.read_bytes())
                working_files[rel_path] = blob.hash()
            except Exception:
                continue

        staged = []
        unstaged = []
        untracked = []
        deleted = []

        # Staged changes: differences between index and last commit
        for file_path in set(idx.keys()) | set(committed_files.keys()):
            idx_hash = idx.get(file_path)
            committed_hash = committed_files.get(file_path)

            if idx_hash and not committed_hash:
                staged.append(("new file", file_path))
            elif idx_hash and committed_hash and idx_hash != committed_hash:
                staged.append(("modified", file_path))
            elif not idx_hash and committed_hash:
                staged.append(("deleted", file_path))

        # Unstaged changes: differences between working tree and index
        for file_path, working_hash in working_files.items():
            if file_path in idx and working_hash != idx[file_path]:
                unstaged.append(file_path)

        # Untracked files
        for file_path in working_files:
            if file_path not in idx and file_path not in committed_files:
                untracked.append(file_path)

        # Deleted from working tree but still in index
        for file_path in idx:
            if file_path not in working_files:
                deleted.append(file_path)

        # -- Output --
        if staged:
            print("\nChanges to be committed:")
            for status_label, fp in sorted(staged):
                print(f"    {status_label}:   {fp}")

        if unstaged:
            print("\nChanges not staged for commit:")
            for fp in sorted(unstaged):
                print(f"    modified:   {fp}")

        if deleted:
            print("\nDeleted files:")
            for fp in sorted(deleted):
                print(f"    deleted:    {fp}")

        if untracked:
            print("\nUntracked files:")
            for fp in sorted(untracked):
                print(f"    {fp}")

        if not staged and not unstaged and not deleted and not untracked:
            print("\nNothing to commit, working tree clean")

    # ------------------------------------------------------------------
    # diff
    # ------------------------------------------------------------------

    def diff(self) -> None:
        """
        Show unified diff between the index (staged) and the working tree.

        For each file in the index that has changed on disk, print a
        unified diff.  New untracked files are not shown (use status).
        """
        idx = self.index.load()
        has_diff = False

        for rel_path, blob_hash in sorted(idx.items()):
            file_path = self.path / rel_path
            if not file_path.exists():
                # File deleted from working tree
                try:
                    blob_obj = self.objects.load(blob_hash)
                    old_lines = blob_obj.content.decode(errors="replace").splitlines(keepends=True)
                except Exception:
                    old_lines = []

                diff_lines = difflib.unified_diff(
                    old_lines, [],
                    fromfile=f"a/{rel_path}",
                    tofile="/dev/null",
                )
                diff_text = "".join(diff_lines)
                if diff_text:
                    has_diff = True
                    print(diff_text)
                continue

            # Compare staged blob with working tree
            current_content = file_path.read_bytes()
            current_blob = Blob(current_content)

            if current_blob.hash() == blob_hash:
                continue  # unchanged

            # Load the staged version
            try:
                blob_obj = self.objects.load(blob_hash)
                old_content = blob_obj.content
            except FileNotFoundError:
                old_content = b""

            old_lines = old_content.decode(errors="replace").splitlines(keepends=True)
            new_lines = current_content.decode(errors="replace").splitlines(keepends=True)

            diff_lines = difflib.unified_diff(
                old_lines, new_lines,
                fromfile=f"a/{rel_path}",
                tofile=f"b/{rel_path}",
            )
            diff_text = "".join(diff_lines)
            if diff_text:
                has_diff = True
                print(diff_text)

        if not has_diff:
            print("No differences")

    # ------------------------------------------------------------------
    # gc  (garbage collection)
    # ------------------------------------------------------------------

    def gc(self) -> None:
        """
        Remove unreachable objects.

        Walks the reachability graph starting from every branch ref,
        traversing commit → parent commits → tree → blobs/subtrees.
        Any object not reachable is deleted.
        """
        reachable = self._get_reachable_objects()
        all_objects = self.objects.list_all_hashes()

        unreachable = all_objects - reachable

        for obj_hash in unreachable:
            self.objects.delete(obj_hash)

        if unreachable:
            print(f"Removed {len(unreachable)} unreachable objects")
        else:
            print("Nothing to clean up — all objects are reachable")

    def _get_reachable_objects(self) -> set:
        """Walk all branch tips and collect every reachable object hash."""
        reachable: set = set()

        for branch in self.branches.list_branches():
            commit_hash = self.branches.get_branch_commit(branch)
            while commit_hash and commit_hash not in reachable:
                reachable.add(commit_hash)
                try:
                    commit_obj = self.objects.load(commit_hash)
                    commit = Commit.from_content(commit_obj.content)
                    if commit.tree_hash:
                        self._walk_tree(commit.tree_hash, reachable)
                    commit_hash = commit.parent_hashes[0] if commit.parent_hashes else None
                except Exception:
                    break

        # Also include objects referenced by the current index
        idx = self.index.load()
        reachable.update(idx.values())

        return reachable

    def _walk_tree(self, tree_hash: str, reachable: set) -> None:
        """Recursively add a tree and all its children to *reachable*."""
        if tree_hash in reachable:
            return
        reachable.add(tree_hash)

        try:
            tree_obj = self.objects.load(tree_hash)
            tree = Tree.from_content(tree_obj.content)
            for mode, name, obj_hash in tree.entries:
                if mode.startswith("100"):
                    reachable.add(obj_hash)
                elif mode.startswith("400"):
                    self._walk_tree(obj_hash, reachable)
        except Exception:
            pass

    # ------------------------------------------------------------------
    # cat-file (plumbing)
    # ------------------------------------------------------------------

    def cat_file(self, obj_hash: str) -> None:
        """Print type, size, and content of an object."""
        obj = self.objects.load(obj_hash)
        print(f"type: {obj.type}")
        print(f"size: {len(obj.content)}")
        print()

        if obj.type == "blob":
            try:
                print(obj.content.decode())
            except UnicodeDecodeError:
                print(f"(binary data, {len(obj.content)} bytes)")
        elif obj.type == "tree":
            tree = Tree.from_content(obj.content)
            for mode, name, entry_hash in tree.entries:
                print(f"{mode} {name} {entry_hash}")
        elif obj.type == "commit":
            print(obj.content.decode())

    # ------------------------------------------------------------------
    # hash-object (plumbing)
    # ------------------------------------------------------------------

    def hash_object(self, file_path: str, write: bool = True) -> str:
        """
        Hash a file as a blob. If *write* is True, store it.
        Returns the SHA-1 hash.
        """
        full_path = self.path / file_path
        if not full_path.exists():
            raise FileNotFoundError(f"File {file_path} not found")

        blob = Blob(full_path.read_bytes())
        blob_hash = blob.hash()

        if write:
            self.objects.store(blob)

        print(blob_hash)
        return blob_hash

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_all_files(self) -> List[Path]:
        """Return all files in the working tree, excluding .minigit/."""
        files = []
        for item in self.path.rglob("*"):
            if ".minigit" in item.parts:
                continue
            if item.is_file():
                # Also respect .minigitignore
                rel_path = item.relative_to(self.path).as_posix()
                if not self.index.is_ignored(rel_path):
                    files.append(item)
        return files