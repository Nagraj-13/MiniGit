"""
MiniGit CLI — a simplified Git clone for learning.

Usage:
    python main.py <command> [options]

Commands:
    init        Initialise a new repository
    add         Stage files or directories
    commit      Record a new commit
    status      Show working-tree status
    diff        Show unstaged changes (index vs working tree)
    log         Show commit history
    branch      List, create, or delete branches
    checkout    Switch branches (optionally create)
    gc          Run garbage collection on loose objects
    cat-file    Inspect a stored object (plumbing)
    hash-object Hash a file and optionally store it (plumbing)
"""

import argparse
import sys

from src.repository import Repository


def _require_repo(repo: Repository) -> bool:
    """Return True if the repo is initialised, printing an error otherwise."""
    if not repo.git_dir.exists():
        print("fatal: not a minigit repository (or any parent up to mount point /)")
        return False
    return True


def main() -> None:
    parser = argparse.ArgumentParser(
        description="MiniGit — A simplified Git clone",
    )
    sub = parser.add_subparsers(dest="command", help="Available commands")

    # -- init --
    sub.add_parser("init", help="Initialise a new repository")

    # -- add --
    add_p = sub.add_parser("add", help="Stage files and directories")
    add_p.add_argument("paths", nargs="+", help="Paths to stage")

    # -- commit --
    commit_p = sub.add_parser("commit", help="Record a new commit")
    commit_p.add_argument("-m", "--message", required=True, help="Commit message")
    commit_p.add_argument("--author", help="Author name and email")

    # -- status --
    sub.add_parser("status", help="Show working-tree status")

    # -- diff --
    sub.add_parser("diff", help="Show unstaged changes")

    # -- log --
    log_p = sub.add_parser("log", help="Show commit history")
    log_p.add_argument(
        "-n", "--max-count", type=int, default=10,
        help="Maximum number of commits to show",
    )

    # -- branch --
    branch_p = sub.add_parser("branch", help="List, create, or delete branches")
    branch_p.add_argument("name", nargs="?", help="Branch name to create")
    branch_p.add_argument(
        "-d", "--delete-branch", action="store_true",
        help="Delete the named branch",
    )

    # -- checkout --
    checkout_p = sub.add_parser("checkout", help="Switch branches")
    checkout_p.add_argument("branch", help="Branch to switch to")
    checkout_p.add_argument(
        "-b", "--create-branch", action="store_true",
        help="Create the branch before switching",
    )

    # -- gc --
    sub.add_parser("gc", help="Run garbage collection")

    # -- cat-file --
    catfile_p = sub.add_parser("cat-file", help="Display object contents")
    catfile_p.add_argument("object_hash", help="SHA-1 hash of the object")

    # -- hash-object --
    hashobj_p = sub.add_parser("hash-object", help="Hash a file as a blob")
    hashobj_p.add_argument("file", help="File to hash")
    hashobj_p.add_argument(
        "-w", "--write", action="store_true", default=True,
        help="Write the object to the store (default: True)",
    )

    # -----------------------------------------------------------------
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    repo = Repository()

    try:
        if args.command == "init":
            if not repo.init():
                print("Repository already exists")

        elif args.command == "add":
            if not _require_repo(repo):
                return
            for path in args.paths:
                repo.add_path(path)

        elif args.command == "commit":
            if not _require_repo(repo):
                return
            author = args.author or "MiniGit user <user@minigit>"
            repo.commit(args.message, author)

        elif args.command == "status":
            if not _require_repo(repo):
                return
            repo.status()

        elif args.command == "diff":
            if not _require_repo(repo):
                return
            repo.diff()

        elif args.command == "log":
            if not _require_repo(repo):
                return
            repo.log(args.max_count)

        elif args.command == "branch":
            if not _require_repo(repo):
                return
            repo.branch(args.name, args.delete_branch)

        elif args.command == "checkout":
            if not _require_repo(repo):
                return
            repo.checkout(args.branch, args.create_branch)

        elif args.command == "gc":
            if not _require_repo(repo):
                return
            repo.gc()

        elif args.command == "cat-file":
            if not _require_repo(repo):
                return
            repo.cat_file(args.object_hash)

        elif args.command == "hash-object":
            if not _require_repo(repo):
                return
            repo.hash_object(args.file, write=args.write)

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
