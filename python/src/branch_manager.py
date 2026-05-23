"""
Branch manager — HEAD, refs, checkout, and tree operations.

Manages:
  - HEAD file (current branch pointer)
  - Branch refs under refs/heads/
  - Checkout (switching branches and restoring working directory)
  - Building trees from the index and walking trees
"""

from pathlib import Path
from typing import Dict, List, Optional, Set

from src.objects import Blob, Commit, MiniGitObject, Tree
from src.object_store import ObjectStore


class BranchManager:
    """Manages branches, HEAD, checkout, and tree operations."""

    def __init__(
        self,
        repo_path: Path,
        head_file: Path,
        heads_dir: Path,
        object_store: ObjectStore,
    ):
        self.repo_path = repo_path
        self.head_file = head_file
        self.heads_dir = heads_dir
        self.object_store = object_store

    # ------------------------------------------------------------------
    # HEAD / branch refs
    # ------------------------------------------------------------------

    def get_current_branch(self) -> str:
        """Return the name of the current branch (or 'HEAD' if detached)."""
        if not self.head_file.exists():
            return "master"
        head_content = self.head_file.read_text().strip()
        if head_content.startswith("ref: refs/heads/"):
            return head_content[16:]
        return "HEAD"  # detached HEAD

    def get_branch_commit(self, branch: str) -> Optional[str]:
        """Return the commit hash at the tip of *branch*, or None."""
        branch_file = self.heads_dir / branch
        if branch_file.exists():
            return branch_file.read_text().strip()
        return None

    def set_branch_commit(self, branch: str, commit_hash: str) -> None:
        """Point *branch* to *commit_hash*."""
        branch_file = self.heads_dir / branch
        branch_file.write_text(commit_hash + "\n")

    def set_head(self, branch: str) -> None:
        """Update HEAD to point to *branch*."""
        self.head_file.write_text(f"ref: refs/heads/{branch}\n")

    def list_branches(self) -> List[str]:
        """Return sorted list of all branch names."""
        branches = []
        if not self.heads_dir.exists():
            return branches
        for branch_file in self.heads_dir.iterdir():
            if branch_file.is_file() and not branch_file.name.startswith("."):
                branches.append(branch_file.name)
        return sorted(branches)

    def delete_branch(self, branch_name: str) -> bool:
        """Delete a branch ref.  Returns True if it existed."""
        branch_file = self.heads_dir / branch_name
        if branch_file.exists():
            branch_file.unlink()
            return True
        return False

    # ------------------------------------------------------------------
    # Tree building (index → tree objects)
    # ------------------------------------------------------------------

    def create_tree_from_index(self, index: Dict[str, str]) -> str:
        """
        Build tree objects from a flat index mapping and return the
        root tree hash.  Handles nested directories recursively.
        """
        if not index:
            tree = Tree()
            return self.object_store.store(tree)

        dirs: Dict = {}
        files: Dict[str, str] = {}

        for file_path, blob_hash in index.items():
            parts = file_path.split("/")

            if len(parts) == 1:
                files[parts[0]] = blob_hash
            else:
                dir_name = parts[0]
                if dir_name not in dirs:
                    dirs[dir_name] = {}

                current = dirs[dir_name]
                for part in parts[1:-1]:
                    if part not in current:
                        current[part] = {}
                    current = current[part]
                current[parts[-1]] = blob_hash

        def _build_tree(entries_dict: Dict) -> str:
            tree = Tree()
            for name, value in entries_dict.items():
                if isinstance(value, str):
                    tree.add_entry("100644", name, value)
                elif isinstance(value, dict):
                    subtree_hash = _build_tree(value)
                    tree.add_entry("40000", name, subtree_hash)
            return self.object_store.store(tree)

        root_entries = {**files}
        for dir_name, dir_content in dirs.items():
            root_entries[dir_name] = dir_content

        return _build_tree(root_entries)

    # ------------------------------------------------------------------
    # Tree walking
    # ------------------------------------------------------------------

    def get_files_from_tree(self, tree_hash: str, prefix: str = "") -> Set[str]:
        """Recursively collect all file paths from a tree."""
        files: Set[str] = set()
        try:
            tree_obj = self.object_store.load(tree_hash)
            tree = Tree.from_content(tree_obj.content)
            for mode, name, obj_hash in tree.entries:
                full_name = f"{prefix}{name}"
                if mode.startswith("100"):
                    files.add(full_name)
                elif mode.startswith("400"):
                    files.update(
                        self.get_files_from_tree(obj_hash, f"{full_name}/")
                    )
        except Exception as e:
            print(f"Warning: could not read tree {tree_hash}: {e}")
        return files

    def build_index_from_tree(self, tree_hash: str, prefix: str = "") -> Dict[str, str]:
        """Reconstruct a flat index dict from a tree hierarchy."""
        index: Dict[str, str] = {}
        try:
            tree_obj = self.object_store.load(tree_hash)
            tree = Tree.from_content(tree_obj.content)
            for mode, name, obj_hash in tree.entries:
                full_name = f"{prefix}{name}"
                if mode.startswith("100"):
                    index[full_name] = obj_hash
                elif mode.startswith("400"):
                    sub_index = self.build_index_from_tree(
                        obj_hash, f"{full_name}/"
                    )
                    index.update(sub_index)
        except Exception as e:
            print(f"Warning: could not read tree {tree_hash}: {e}")
        return index

    # ------------------------------------------------------------------
    # Checkout / restore
    # ------------------------------------------------------------------

    def checkout(
        self,
        branch: str,
        create_branch: bool,
        save_index_fn,
    ) -> None:
        """
        Switch to *branch* (creating it first if *create_branch* is True).

        *save_index_fn* is a callable(Dict) used to persist the new index
        after restoring files.
        """
        previous_branch = self.get_current_branch()
        file_to_clear: Set[str] = set()
        previous_commit_hash = None

        try:
            previous_commit_hash = self.get_branch_commit(previous_branch)
            if previous_commit_hash:
                prev_obj = self.object_store.load(previous_commit_hash)
                prev_commit = Commit.from_content(prev_obj.content)
                if prev_commit.tree_hash:
                    file_to_clear = self.get_files_from_tree(prev_commit.tree_hash)
        except Exception:
            file_to_clear = set()

        branch_file = self.heads_dir / branch
        if not branch_file.exists():
            if create_branch:
                if previous_commit_hash:
                    self.set_branch_commit(branch, previous_commit_hash)
                    print(f"Created new branch '{branch}'")
                else:
                    print("No commits yet — cannot create a new branch")
                    return
            else:
                print(f"Branch '{branch}' not found")
                print(
                    f"Use: python main.py checkout -b {branch}  to create and switch"
                )
                return

        self.set_head(branch)
        self._restore_working_directory(branch, file_to_clear, save_index_fn)
        print(f"Switched to branch '{branch}'")

    def _restore_working_directory(
        self,
        branch: str,
        file_to_clear: Set[str],
        save_index_fn,
    ) -> None:
        """Remove old tracked files, restore target branch's files, rebuild index."""
        target_commit_hash = self.get_branch_commit(branch)
        if not target_commit_hash:
            return

        # Remove files from the previous branch
        for rel_path in sorted(file_to_clear):
            file_path = self.repo_path / rel_path
            try:
                if file_path.is_file():
                    file_path.unlink()
                elif file_path.is_dir() and not any(file_path.iterdir()):
                    file_path.rmdir()
            except Exception:
                pass

        target_obj = self.object_store.load(target_commit_hash)
        target_commit = Commit.from_content(target_obj.content)

        if target_commit.tree_hash:
            self._restore_tree(target_commit.tree_hash, self.repo_path)
            new_index = self.build_index_from_tree(target_commit.tree_hash)
            save_index_fn(new_index)
        else:
            save_index_fn({})

    def _restore_tree(self, tree_hash: str, path: Path) -> None:
        """Recursively write tree entries to the working directory."""
        tree_obj = self.object_store.load(tree_hash)
        tree = Tree.from_content(tree_obj.content)

        for mode, name, obj_hash in tree.entries:
            file_path = path / name
            if mode.startswith("100"):
                blob_obj = self.object_store.load(obj_hash)
                file_path.write_bytes(blob_obj.content)
            elif mode.startswith("400"):
                file_path.mkdir(exist_ok=True)
                self._restore_tree(obj_hash, file_path)

    # ------------------------------------------------------------------
    # Branch command (list / create / delete)
    # ------------------------------------------------------------------

    def branch(self, branch_name: Optional[str], delete: bool = False) -> None:
        """Handle the 'branch' CLI command."""
        if delete and branch_name:
            if self.delete_branch(branch_name):
                print(f"Deleted branch '{branch_name}'")
            else:
                print(f"Branch '{branch_name}' not found")
            return

        current_branch = self.get_current_branch()

        if branch_name:
            current_commit = self.get_branch_commit(current_branch)
            if current_commit:
                self.set_branch_commit(branch_name, current_commit)
                print(f"Created branch '{branch_name}'")
            else:
                print("No commits yet — cannot create a new branch")
        else:
            for branch in self.list_branches():
                marker = "* " if branch == current_branch else "  "
                print(f"{marker}{branch}")
