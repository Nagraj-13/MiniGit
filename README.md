# MiniGit — Build Your Own Git From Scratch

A minimal, educational reimplementation of core Git features in Python,
designed to teach how distributed version control works under the hood.

> ⚠️ This is for learning purposes only. It is **not** a full replacement for Git.

---

## 📌 Features

| Command        | Description                                  |
|----------------|----------------------------------------------|
| `init`         | Initialise a new `.minigit` repository       |
| `add`          | Stage files and directories                  |
| `commit`       | Record a new commit snapshot                 |
| `status`       | Show staged, unstaged, untracked & deleted   |
| `diff`         | Show line-by-line changes (index vs working) |
| `log`          | Display commit history                       |
| `branch`       | List, create, or delete branches             |
| `checkout`     | Switch branches (with optional `-b` create)  |
| `gc`           | Garbage-collect unreachable objects           |
| `cat-file`     | Inspect a stored object (plumbing)           |
| `hash-object`  | Hash a file as a blob (plumbing)             |

### Additional Capabilities

- **`.minigitignore`** — place a file at the repo root to ignore patterns (like `.gitignore`)
- **Cross-platform** — paths are normalised to POSIX format internally

---

## 🛠 Requirements

- Python 3.10+
- No external dependencies (standard library only)

---

## 🚀 Getting Started

### Installation

```bash
# Clone this project
git clone https://github.com/Nagraj-13/MiniGit
cd MiniGit/python

# Install as a command (recommended)
pip install -e .

# Now you can use 'minigit' from anywhere!
minigit --help
```

### Quick Start

```bash
# Go to any project folder
cd my-project

# Initialise a repository
minigit init

# Stage files
minigit add main.py src/

# Commit
minigit commit -m "Initial commit"

# Check status
minigit status

# View history
minigit log

# Show changes
minigit diff
```

> **Without installing:** You can also run directly with `python main.py <command>` from the `python/` folder.

### Running Tests

```bash
cd python
python test_minigit.py
```

This runs 38 automated tests covering every command in an isolated temp directory.

---

## 📂 Project Structure

```
python/
├── main.py                  # CLI entry point
└── src/
    ├── __init__.py
    ├── objects.py            # Blob, Tree, Commit data model
    ├── object_store.py       # Object I/O (store, load, delete)
    ├── index_manager.py      # Staging area + .minigitignore
    ├── branch_manager.py     # HEAD, refs, checkout, tree ops
    └── repository.py         # High-level facade
```

### Repository Layout (`.minigit/`)

```
.minigit/
├── objects/          # Content-addressable object store
│   ├── ab/           # First 2 chars of SHA-1
│   │   └── cdef...   # Remaining 38 chars
├── refs/
│   └── heads/        # Branch pointers (master, feature, etc.)
├── hooks/
├── info/
├── logs/
├── HEAD              # Points to current branch
└── index             # JSON staging area
```

---

## 🧩 Core Concepts

### Objects

Git (and MiniGit) stores everything as content-addressable objects:

| Type     | Description                         |
|----------|-------------------------------------|
| **Blob** | Raw file content                    |
| **Tree** | Directory listing (mode/name/hash)  |
| **Commit** | Snapshot + parent(s) + metadata   |

Each object is stored as:
```
zlib.compress(b"<type> <size>\0<content>")
```
And identified by `sha1(b"<type> <size>\0<content>")`.

### Branching & HEAD

`HEAD` contains a symbolic ref:
```
ref: refs/heads/master
```
Each branch file under `refs/heads/` contains the SHA-1 of its tip commit.

### `.minigitignore`

Create a `.minigitignore` file at your repo root:
```
__pycache__/
*.pyc
.env
node_modules/
```
Patterns use `fnmatch` glob syntax. Directory patterns end with `/`.

---

## 🔧 Command Reference

### Porcelain Commands

```bash
# Initialise
minigit init

# Stage
minigit add <file_or_dir> [...]

# Commit
minigit commit -m "message" [--author "Name <email>"]

# Status
minigit status

# Diff (index vs working tree)
minigit diff

# Log
minigit log [-n 20]

# Branches
minigit branch                    # list
minigit branch feature            # create
minigit branch -d feature         # delete

# Checkout
minigit checkout feature          # switch
minigit checkout -b new-branch    # create + switch

# Garbage collection
minigit gc
```

### Plumbing Commands

```bash
# Inspect an object
minigit cat-file <sha1-hash>

# Hash a file
minigit hash-object <file>
```

---

## 🧠 What You'll Learn

- How Git stores data as content-addressable objects
- How SHA-1 hashing identifies objects
- How commits reference trees and parent commits
- How refs and HEAD work together
- How the staging area (index) functions
- How branching and checkout restore the working directory
- How garbage collection finds and removes orphaned objects

---

## ❗ Limitations

- No networking (push/pull/clone)
- No merge conflict resolution
- No packfiles or delta compression
- No reflogs or stash
- Not optimised for large repositories

---

## 📜 License

Educational use only. Extend and modify as needed.
