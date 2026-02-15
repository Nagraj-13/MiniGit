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
