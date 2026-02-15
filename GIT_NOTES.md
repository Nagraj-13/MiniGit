# Git Notes

## What is Git?

Git is a distributed version control system (DVCS) designed to track changes in source code during software development.

It allows multiple developers to work on the same project efficiently while keeping a complete history of changes.

---

## Why is Git Used?

Git is used to:

* Track changes in files over time
* Collaborate with multiple developers
* Maintain version history
* Create branches for feature development
* Merge code safely
* Roll back to previous versions when needed
* Manage large projects efficiently

Git is fast, reliable, and works offline because every developer has a full copy of the repository.

---

## Git CLI (Command Line Interface)

Git is primarily used through the command line.

Common commands:

* `git init` → Initialize a new repository
* `git add <file>` → Add file(s) to staging area
* `git commit -m "message"` → Save staged changes
* `git status` → Show current state
* `git log` → Show commit history
* `git branch` → List branches
* `git checkout <branch>` → Switch branches
* `git merge <branch>` → Merge branches
* `git clone <url>` → Copy remote repository
* `git push` → Send commits to remote
* `git pull` → Fetch and merge from remote

---

## The `.git` Folder

When you run `git init`, a hidden folder called `.git` is created.

This folder contains everything Git needs to manage the repository.

Important directories inside `.git`:

* `objects/` → Stores all data (commits, trees, blobs)
* `refs/` → Stores branch and tag references
* `HEAD` → Points to current branch
* `index` → Staging area metadata
* `logs/` → Tracks updates to refs
* `hooks/` → Custom scripts triggered by Git events
* `config` → Repository configuration

The working project files are NOT stored here directly — only metadata and object data are.

---

## How Git Internally Works

Git is content-addressable.

This means:

* Every file content is hashed.
* The hash becomes its identity.
* Git does not track files by name.
* Git tracks content by hash.

Git uses SHA-1 (historically) or SHA-256 (newer versions) to generate hashes.

---

## Git Object Model

Git stores everything as objects in compressed binary format.

Your statement:

> Git stores everything in objects in bytes format because the best way to represent image, text, video, files etc in bytes format.

### Verification & Explanation

This is conceptually correct.

All data inside a computer is ultimately represented as bytes. Git stores data in binary format because:

* Every file (text, image, video, etc.) can be represented as bytes.
* Binary storage is efficient.
* It allows compression.
* It ensures consistent hashing.

When Git stores an object:

1. It takes file content.
2. Adds a header (like `blob <size>\0`).
3. Hashes the result.
4. Compresses it using zlib.
5. Stores it in `.git/objects`.

Objects are stored as:

`.git/objects/ab/cdef123456...`

Where:

* First 2 characters of hash → folder name
* Remaining characters → file name

This prevents too many files in a single directory.

---

## Git Has Three Main Working Areas

### 1. Working Directory (Working Tree)

* Files on your disk.
* May be tracked or untracked.
* This is where you edit files.

---

### 2. Staging Area (Index)

You wrote:

> git add -> stores the working directory or entire content of added files in .git/objects it compress it in bytes and it maintains index where file content will be hashed and the first 2 characters of the hash will be created as folder and the rest hash will be created as a filename.

### Detailed Explanation

When you run `git add file.txt`:

1. Git reads the file contents.
2. Creates a blob object.
3. Hashes the content.
4. Compresses and stores it in `.git/objects`.
5. Updates the `index` file.

Important clarification:

The index does NOT store file contents.

The index stores:

* File path
* Blob hash
* File metadata (permissions, timestamps)

So the staging area is essentially a snapshot blueprint for the next commit.

---

### 3. Local Repository

The local repository is the `.git` directory.

When you commit:

* A tree object is created from the index.
* A commit object is created referencing that tree.
* The branch reference is updated.

Commit stores:

* Tree hash
* Parent commit hash
* Author
* Message
* Timestamp

---

## Additional Git Areas

### 4. Stash

`git stash` temporarily saves uncommitted changes.

It stores:

* Working directory state
* Index state

So you can switch branches safely.

---

### 5. Remote

A remote is another Git repository (usually on a server).

Common remote operations:

* `git push`
* `git pull`
* `git fetch`

Remote repositories allow collaboration.

---

### 6. Refs (References)

Refs are pointers to commits.

Examples:

* `refs/heads/main` → Local branch
* `refs/tags/v1.0` → Tag
* `refs/remotes/origin/main` → Remote branch

HEAD is a special ref that points to the current branch.

---

## Summary of Internal Flow

Working Directory → git add → Index → git commit → Local Repository → git push → Remote

Everything in Git is built on:

* Hashing
* Immutable objects
* References (pointers)
* Snapshots (not file diffs by default)

---

(Notes will continue to grow as more internal concepts are implemented.)
