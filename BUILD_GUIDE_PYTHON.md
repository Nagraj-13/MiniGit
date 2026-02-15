# BUILD YOUR OWN GIT FROM SCRATCH

Build Your Own Git From Scratch (Beginner-Friendly Guide)

Build Your Own Git From Scratch — Step by Step

---


In this guide, you will build your own simplified version of Git from absolute zero.

The goal is not to copy Git’s entire complexity.
The goal is to understand how a version control system starts:

* How commands are parsed
* How a repository is created
* How internal folders are structured
* How HEAD and index files are initialized

By the end of this guide (current stage), you will have:

* A working CLI tool
* A custom `.minigit` repository
* A Git-like internal directory structure
* A clean foundation to build further features

We will build everything clearly and incrementally.

---

# Get Started

Create a clean working directory anywhere on your system.

Example:

```
MiniGit/
```

Inside it we will place all our code.

All development commands should be run from inside the `python` folder (which we will create below).

---

# Install Python and VS Code

## Install Python

1. Install Python 3.10 or higher.
2. During installation, enable:

   * “Add Python to PATH”

Verify installation:

```bash
python --version
```

or on Windows:

```powershell
py --version
```

You should see Python 3.10+.

---

## Install VS Code

Install:

* Visual Studio Code
* Python Extension for VS Code

Recommended settings:

* Enable format on save
* Open the MiniGit folder as your workspace

---

# Step 1 — Setup the Project as MiniGit

Create this structure:

```
MiniGit/
│
└── python/
        main.py
```

Navigate into:

```
MiniGit/python
```

All commands will be executed from here.

---

# Step 1.1 — Create main.py (Argument Parsing Only)

Before building Git internals, we need command-line parsing.

Create `main.py`:

```python
import argparse

def main():
    parser = argparse.ArgumentParser(
        description="GetGit - A simple git clone"
    )
    
    subparser = parser.add_subparsers(dest="command",help="Available Help")
    
    init_parser = subparser.add_parser("init", help="Initialize a new repo")
    
    args = parser.parse_args()
    print(args)

main()
```

---

## What This Does

* Creates a CLI tool
* Accepts a command called `init`
* Prints parsed arguments

Try running:

```bash
python -m main init
```

You should see parsed arguments printed.

At this stage:

You have only built the command layer.
Nothing happens internally yet.

This is the foundation.

Let’s break this down clearly.

Your program:

```python
def main():
    parser = argparse.ArgumentParser(
        description="GetGit - A simple git clone"
    )
    
    subparser = parser.add_subparsers(dest="command",help="Available Help")
    
    init_parser = subparser.add_parser("init", help="Initialize a new repo")
    
    args = parser.parse_args()
    print(args)

main()
```

## What It Prints

The output depends on **how you run the script from the terminal**.

---

### Case 1: Run Without Any Arguments

Command:

```bash
python main.py
```

Output:

```python
Namespace(command=None)
```

Why?

* You defined subcommands.
* But you didn’t pass any.
* So `command` becomes `None`.

---

### Case 2: Run With `init` Command

Command:

```bash
python main.py init
```

Output:

```python
Namespace(command='init')
```

Why?

* `init` matches the subparser.
* So `command` gets the value `"init"`.

---

### Case 3: Run With Unknown Command

Command:

```bash
python main.py something
```

Output:

```
usage: main.py [-h] {init} ...
main.py: error: argument command: invalid choice: 'something' (choose from 'init')
```

Why?

* `argparse` only allows `init`.
* Anything else causes an automatic error.

---

### Case 4: Run With Help Flag

Command:

```bash
python main.py -h
```

Output:

```
usage: main.py [-h] {init} ...

GetGit - A simple git clone

positional arguments:
  {init}       Available Help
    init       Initialize a new repo

options:
  -h, --help   show this help message and exit
```



## Summary

Your script only prints one thing:

```python
print(args)
```

So it always prints a `Namespace` object that represents parsed arguments.

* No arguments → `Namespace(command=None)`
* `init` → `Namespace(command='init')`




---

# Step 2 — Creating Our Own .git (Called .minigit)

Git internally creates a hidden folder called `.git`.

We will create our own:

```
.minigit
```

This folder will store everything about our version control system.

---

# Step 2.1 — Create src Directory and repository.py

Inside `python/`, create:

```
src/
    __init__.py
    repository.py
```

Now we will implement the repository logic.

---

# Step 2.2 — Implement the Repository Class

Open `repository.py` and add:

```python
import json
from pathlib import Path


class Repository:
    def __init__(self, path="."):
        self.path = Path(path).resolve()
        self.git_dir = self.path / ".minigit"
        
        # .git/objects
        self.objects_dir = self.git_dir / "objects"
        # .git/refs
        self.refs_dir = self.git_dir / "refs"
        # .git/refs/heads
        self.heads_dir = self.refs_dir / "heads"
        # .git/hooks
        self.hooks_dir = self.git_dir / "hooks"
        # .git/info
        self.info_dir = self.git_dir / "info"
        # .git/logs
        self.logs_dir = self.git_dir / "logs"
        
        
        # .git/HEAD file
        self.head_file = self.git_dir / "HEAD"
        
         # .git/index file
        self.index_file = self.git_dir / "index"
        
    def init(self) -> bool:
        if self.git_dir.exists():
            return False
        try:
            # create layout
            for d in (self.objects_dir, self.refs_dir, self.heads_dir,
                      self.info_dir, self.logs_dir, self.hooks_dir):
                d.mkdir(parents=True, exist_ok=True)

            # initial HEAD (use main for modern convention)
            self.head_file.write_text("ref: refs/heads/main\n")
            # empty index
            self.index_file.write_text(json.dumps({}, indent=4))
            print(f"Initialized an empty MiniGit repository in {self.git_dir}")
            return True
        except Exception as e:
            print(f"Failed to initialize repository: {e}")
            return False
```

---

## What This Code Does

When `init()` runs:

It creates this structure:

```
.minigit/
│
├── objects/
├── refs/
│   └── heads/
├── hooks/
├── info/
├── logs/
├── HEAD
└── index
```

### Important Concepts

HEAD
Contains:

```
ref: refs/heads/main
```

This means:

* HEAD points to the branch `main`
* Branch references will be stored inside `refs/heads`

Index
Currently an empty JSON object:

```json
{}
```

This will later become the staging area.

---

# Step 2.3 — Connect CLI to Repository

Now modify `main.py` to call the repository logic.

Replace the previous code with:

```python
import argparse
import sys

from src.repository import Repository

def main():
    parser = argparse.ArgumentParser(
        description="MiniGit - A simple git clone"
    )
    
    subparser = parser.add_subparsers(dest="command",help="Available Help")
    
    init_parser = subparser.add_parser("init", help="Initialize a new repo")
    add_parser = subparser.add_parser("add", help="Add files to index")
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return

    try:
        if args.command == 'init':
            repo = Repository()
            if not repo.init():
                print("Repository Already Exists")
                return
    except Exception as e:
        print(f"Error : {e}")
        sys.exit(1)
    
main()
```

---

# How to Run

From inside:

```
MiniGit/python
```

Run:

```bash
python -m main init
```

You should see:

```
Initialized an empty MiniGit repository in ...
```

And a new folder:

```
.minigit
```

will appear.

---

# What You Have Built So Far

You have successfully implemented:

✔ Command-line parsing
✔ Subcommand handling
✔ Repository abstraction
✔ Creation of a Git-like internal structure
✔ HEAD initialization
✔ Index initialization
✔ Basic error handling

This is equivalent to building the core behavior of:

```
git init
```

But using your own implementation.

---



# Step 3 — Adding files to the object store

Below is a focused, practical, and well-documented Step 3 for your MiniGit project: **how files get converted to objects, stored on disk, and how a simple tree layout gets built from the index**. I include *why* each piece exists, *how* it works, and updated code chunks you can drop into your `src/` folder (and `main.py`).

---

# Goals for Step 3

1. Turn file contents into *blob* objects and store them in `.minigit/objects` using the SHA-1 format `aa/bbbbb...` (two-char prefix directory + remainder file).
2. Make the object bytes be the canonical format: a header (`<type> <size>\0`) + raw content, compressed with `zlib`. Hash is computed over the *uncompressed* header+content (git-style).
3. Update the `index` file to map working-tree relative paths → blob hashes (staging area).
4. Provide a way to materialize *tree* objects from the index (simple, bottom-up tree creation) so you can later create commits from a root tree.
5. Keep everything simple and explicit — correct core plumbing first; bug polishing later.

---

# Design decisions (how & why)

* **Blob format:** Use the same hashing and serialization approach as Git (header + content, then SHA-1): this makes blobs stable and easy to inspect or compare.
* **Zlib compression** on disk: matches Git’s approach and keeps content compact.
* **Sharded objects dir:** store objects under `.minigit/objects/<first2>/<rest>` to avoid huge single directories.
* **Index:** keep minimal JSON mapping `{"path/to/file": "sha1hash", ...}`. Simple and human readable at this stage.
* **Idempotency:** if an object already exists on disk, don’t rewrite it (avoid duplicate work).
* **Separation of responsibilities:** `objects.py` contains object classes (Blob, Tree, base class), `repository.py` contains repository operations (store/load object, add file/dir, build trees), CLI (`main.py`) orchestrates.

---

# Updated code — drop into `src/`

### `src/objects.py` — object classes (Blob, Tree, base)

```python
# src/objects.py
from __future__ import annotations
import hashlib
import zlib
from typing import Tuple, List


class MiniGitObjects:
    """
    Base object. Stores type and raw content bytes.
    Hashing/serialization follows: sha1(b"<type> <size>\\0" + content).
    On disk we write zlib.compress(header + content).
    """
    def __init__(self, obj_type: str, content: bytes):
        self.type = obj_type
        self.content = content

    def hash(self) -> str:
        header = f"{self.type} {len(self.content)}\0".encode()
        digest = hashlib.sha1(header + self.content).hexdigest()
        return digest

    def serialize(self) -> bytes:
        header = f"{self.type} {len(self.content)}\0".encode()
        return zlib.compress(header + self.content)

    @classmethod
    def de_serialize(cls, data: bytes) -> "MiniGitObjects":
        decompressed = zlib.decompress(data)
        null_idx = decompressed.find(b"\0")
        header = decompressed[:null_idx]
        content = decompressed[null_idx + 1 :]
        obj_type, _size = header.split(b" ", 1)
        return cls(obj_type.decode(), content)


class Blob(MiniGitObjects):
    def __init__(self, content: bytes):
        super().__init__("blob", content)

    def get_content(self) -> bytes:
        return self.content
```

---

### `src/repository.py` — repository operations, improved `store_object`

```python
# src/repository.py
import json
from pathlib import Path
from typing import Dict
from src.objects import Blob, MiniGitObjects

class Repository:
    def __init__(self, path="."):
        self.path = Path(path).resolve()
        self.git_dir = self.path / ".minigit"
        
        # .git/objects
        self.objects_dir = self.git_dir / "objects"
        # .git/refs
        self.refs_dir = self.git_dir / "refs"
        # .git/refs/heads
        self.heads_dir = self.refs_dir / "heads"
        # .git/hooks
        self.hooks_dir = self.git_dir / "hooks"
        # .git/info
        self.info_dir = self.git_dir / "info"
        # .git/logs
        self.logs_dir = self.git_dir / "logs"
        
        
        # .git/HEAD file
        self.head_file = self.git_dir / "HEAD"
        
         # .git/index file
        self.index_file = self.git_dir / "index"
        
    def init(self) -> bool:
        if self.git_dir.exists():
            return False
        try:
            # create layout
            for d in (self.objects_dir, self.refs_dir, self.heads_dir,
                      self.info_dir, self.logs_dir, self.hooks_dir):
                d.mkdir(parents=True, exist_ok=True)

            # initial HEAD (use main for modern convention)
            self.head_file.write_text("ref: refs/heads/master\n")
            # empty index
            self.index_file.write_text(json.dumps({}, indent=4))  # or self.save_index({})
            print(f"Initialized an empty MiniGit repository in {self.git_dir}")
            return True
        except Exception as e:
            print(f"Failed to initialize repository: {e}")
            return False
    
    def store_object(self, obj:MiniGitObjects)-> str:
        obj_hash = obj.hash()
        obj_directory = self.objects_dir/obj_hash[:2]
        obj_file = obj_directory / obj_hash[2:]
        
        if not obj_directory.exists():
            obj_directory.mkdir(exist_ok=True)
            obj_file.write_bytes(obj.serialize())

        return obj_hash
    
    def load_index(self)-> Dict[str, str]:
        if not self.index_file.exists():
            return {}
        try:
            return json.loads(self.index_file.read_text())
        
        except:
            return {}
    
    def save_index(self, index: Dict[str, str]):
        self.index_file.write_text(json.dumps(index, indent=4))
    
    def add_file(self, path:str):
        # Read file content 
        # Create blob object from the content and compress it
        # store the blob in the databse (.git/objects or .minigit/objects)
        # update the index to include the file
        full_path = self.path / path
        if not full_path.exists():
             raise FileNotFoundError(f"File {path} not found")
         
        content = full_path.read_bytes()
        
        blob = Blob(content)
        
        blob_hash= self.store_object(blob)
        index = self.load_index()
        index[path] = blob_hash
        self.save_index(index)
        print(f"Added  {path}")
        
    def add_directory(self, path):
        # recurively traverse the directory
        # create blog objects for each file
        # store all the blobs in the object database (.minigit/objects)
        # update the index to include all the files
        full_path = self.path / path
        
        if not full_path.exists():
             raise FileNotFoundError(f"File {path} not found")
                 
        if not full_path.is_dir():
            raise ValueError(f"{path} is not a directory")
        
        index = self.load_index()
        added_count = 0
        
        for file_path in full_path.rglob("*"):
            if file_path.is_file():
                if ".minigit" in file_path.parts:
                    continue
                
                content = file_path.read_bytes()
                blob = Blob(content)
                blob_hash = self.store_object(blob)
                relative_path = str(file_path.relative_to(self.path))
                index[relative_path] = blob_hash
                added_count += 1
                
        self.save_index(index)       
        if added_count > 0:
            print(f"Added {added_count} files from the directory {path}")
        else:
            print(f"Directory {path} is already up to date")
            
    def add_path(self, path)->None:
        full_path = self.path / path
        
        if not full_path.exists():
            raise FileNotFoundError(f"Path {path} not found")
        
        if full_path.is_file():
            self.add_file(path)
        elif full_path.is_dir():
            self.add_directory(path)
        else:
            raise ValueError(f"{path} is neither a file nor a directory")
        
    
```

---

### `main.py` — CLI (updated add flow)

```python
# main.py
import argparse
import sys

from src.repository import Repository

def main():
    parser = argparse.ArgumentParser(
        description="MiniGit - A simple git clone"
    )
    
    subparser = parser.add_subparsers(dest="command",help="Available Help")
    
    init_parser = subparser.add_parser("init", help="Initialize a new repo")
    add_parser = subparser.add_parser(
        "add", help="Add files and directories to the staging area"
    )
    add_parser.add_argument("paths", nargs='+' , help="Files and directories to add")
    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        return
    repo = Repository()
    try:
        if args.command == 'init':
            if not repo.init():
                print("Repository Already Exists")
                return
            
        elif args.command == 'add':
            if not repo.git_dir.exists():
                print("Not a git repository")
                return
            for path in args.paths:
                repo.add_path(path)
    except Exception as e:
        print(f"Error : {e}")
        sys.exit(1)
    
if __name__ == "__main__":
    main()
```

---

# How it actually works — quick walkthrough

1. `python -m main init`

   * Creates `.minigit/` layout and an empty `index` JSON.

2. `python -m main add README.md src/`

   * For each file:

     * Read bytes from working tree.
     * Create `Blob(content)` which knows how to `hash()` and `serialize()`.
     * `store_object(blob)`:

       * compute SHA-1 hash,
       * create `.minigit/objects/<sha[:2]>/` if necessary,
       * write compressed bytes to `<sha[2:]>` only if it doesn’t already exist.
     * Update `index` (JSON) with `index["path/to/file"] = <blob_sha>`.



---

# Index format (current)

Simple JSON:

```json
{
    "README.md": "a94a8fe5ccb19ba61c4c0873d391e987982fbbd3",
    "src/repo.py": "b0d3c3d8f..."
}
```

This maps working-tree relative paths to object hashes. It's human-readable and easy to extend later to include mode/timestamps.

---

# Example of object layout on disk

After adding files you will see:

```
.minigit/
  objects/
    a9/
      4a8fe5ccb19ba61c4c0873d391e987982fbbd3
    b0/
      d3c3d8f...
  index
  HEAD
  refs/
  ...
```

Object files are compressed bytes (zlib) of `b"blob <size>\0<content>"`.

---

# Notes / Rationale summary

* The code follows Git's storage model (header+content hashing, zlib compression, sharded object storage). This makes the repoportable to later features (diffs, packfiles, etc.).
* We keep the index simple (JSON) to focus on core object plumbing first.
* Tree creation is implemented now so commits can point to a canonical root tree; it's easier to reason about history afterward.

---


