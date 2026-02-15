# MiniGit Implementation Notes

## Step 1 — Setup the Project as MiniGit

Project structure:

```
MiniGit/
│
└── python/
        main.py
```

All commands are executed from inside:

```
MiniGit/python
```

This ensures Python resolves modules correctly and keeps execution simple during early development.

---

## Step 1.1 — Building the Command Layer (Argument Parsing)

Before implementing Git internals like objects, refs, or the index, we first build the **CLI layer**.

`main.py`:

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

## What This Stage Achieves

At this stage, MiniGit:

* Becomes a CLI program
* Accepts subcommands
* Recognizes `init`
* Parses arguments correctly
* Prints parsed results

Important: **No repository logic exists yet.**

This layer only handles command interpretation.

In real Git, argument parsing is also separated from internal logic.

---

## Understanding `argparse` Internals

### 1. `ArgumentParser`

Creates the root CLI program.

It defines:

* Program description
* Help behavior
* Global options (if added later)

---

### 2. `add_subparsers(dest="command")`

This is critical.

It tells Python:

* The program supports subcommands
* The chosen subcommand will be stored in `args.command`

So internally:

If you run:

```
python main.py init
```

Then:

```
args.command == "init"
```

---

### 3. `add_parser("init")`

Defines a valid subcommand.

Right now, it has:

* No flags
* No additional arguments

It simply registers the word `init` as valid.

---

## Execution Behavior Analysis

### Case 1 — No Arguments

```
python main.py
```

Output:

```
Namespace(command=None)
```

Reason:

* A subcommand was expected.
* None was provided.
* So `command` defaults to `None`.

---

### Case 2 — Valid Subcommand

```
python main.py init
```

Output:

```
Namespace(command='init')
```

Reason:

* `init` matches a registered subparser.
* `command` is assigned the string `"init"`.

---

### Case 3 — Invalid Subcommand

```
python main.py something
```

Output:

```
usage: main.py [-h] {init} ...
main.py: error: argument command: invalid choice: 'something' (choose from 'init')
```

Reason:

* `argparse` automatically validates allowed choices.
* It prevents execution before internal logic runs.

This protects the system from invalid commands.

---

### Case 4 — Help Flag

```
python main.py -h
```

Displays auto-generated documentation.

This is an important feature because:

* You get CLI documentation for free.
* As commands grow, help scales automatically.

---

## Architectural Importance of This Step

Even though functionality is minimal, this step establishes:

* Command routing foundation
* Scalable CLI architecture
* Separation of interface and logic

Later, you will expand it like this:

```
if args.command == "init":
    # call repository initialization logic
```

This keeps MiniGit modular.

---
### Git Data Flow (Workdir → Index → Objects → Commit → Refs)
```
                    ┌────────────────────┐
                    │    Working Dir     │
                    │  (Your Filesystem) │
                    └─────────┬──────────┘
                              │
                              │  git add
                              ▼
                    ┌────────────────────┐
                    │       INDEX        │
                    │   (Staging Area)   │
                    │  path → blob hash  │
                    └─────────┬──────────┘
                              │
                              │  hash + write
                              ▼
                    ┌────────────────────┐
                    │      OBJECTS       │
                    │  blobs / trees     │
                    │  content-addressed │
                    └─────────┬──────────┘
                              │
                              │  git commit
                              ▼
                    ┌────────────────────┐
                    │       COMMIT       │
                    │ tree → snapshot    │
                    │ parent → previous  │
                    │ metadata + message │
                    └─────────┬──────────┘
                              │
                              │  update branch
                              ▼
                    ┌────────────────────┐
                    │        REFS        │
                    │ refs/heads/main    │
                    │ → commit hash      │
                    └─────────┬──────────┘
                              │
                              ▼
                    ┌────────────────────┐
                    │        HEAD        │
                    │ points to branch   │
                    └────────────────────┘
```



This  explains how data flows inside a Git-like version control system.

It represents the internal mechanics behind:

```
git add
git commit
```

---

# Linear View

```
Workdir
   │
   ▼
Index (staging area)
   │
   ▼
Objects (blobs + trees stored by hash)
   │
   ▼
Commit object (snapshot + metadata)
   │
   ▼
Refs (branch updated to new commit)
   │
   ▼
HEAD (points to current branch)
```

---

# Step-by-Step Explanation

## 1️⃣ Working Directory (Workdir)

This is your actual project folder.

* Files are created
* Files are modified
* Files are deleted

Nothing is tracked automatically.

Tracking begins only after `git add`.

---

## 2️⃣ Index (Staging Area)

The index records **which file versions will be included in the next commit**.

Conceptually:

```
{
  "app.py": "a1b2c3...",
  "README.md": "9f8e7d..."
}
```

It maps:

```
file path → blob hash
```

The index is not history.
It is a preparation area.

---

## 3️⃣ Objects (Content-Addressed Storage)

When a file is added:

1. Its contents are hashed.
2. A blob object is created.
3. It is stored under the objects directory.

Objects are:

* Immutable
* Identified by cryptographic hash
* Stored by content, not filename

There are three main object types:

* **Blob** → file content
* **Tree** → directory structure
* **Commit** → snapshot metadata

Important principle:

> Same content = same hash = no duplication.

---

## 4️⃣ Commit Object

A commit contains:

* Pointer to a tree (snapshot of project)
* Parent commit hash (except first commit)
* Author information
* Commit message
* Timestamp

Conceptually:

```
commit
  tree: abcd1234
  parent: 9f8e7d6c
  author: Name
  message: "Initial commit"
```

Commits are immutable.

Once created, they never change.

---

## 5️⃣ Refs (Branch Pointers)

A branch is just a file that contains:

```
<commit hash>
```

Example:

```
refs/heads/main → 3f4a6b...
```

When a new commit is created:

* The branch pointer is updated
* The commit object itself remains unchanged

---

## 6️⃣ HEAD

HEAD points to the current branch:

```
ref: refs/heads/main
```

HEAD does not store commit data directly (unless detached).

It simply says:

> “Follow this branch to find the latest commit.”

---

# Core Internal Principles

### 1. Objects Are Immutable

Once written, they are never modified.

### 2. Refs Are Movable

Branches move forward.
Commits stay fixed.

### 3. Commits Form a Linked Structure

Each commit points to its parent.

History is a chain:

```
C3 → C2 → C1 → (root)
```

---

## What Changes During Each Command

## When You Run `git add`

* File content is hashed
* Blob is stored in objects
* Index is updated

## When You Run `git commit`

* Tree object is created from index
* Commit object is created
* Branch ref is updated
* HEAD remains pointing to that branch

---

## Mental Model Summary

```
Edit files      → Working Directory
Stage files     → Index
Store content   → Objects
Create snapshot → Commit
Move branch     → Refs
Track current   → HEAD
```

---

### One-Sentence Summary

Git works by storing immutable, content-addressed objects and moving lightweight branch pointers to build a linked history of snapshots.
