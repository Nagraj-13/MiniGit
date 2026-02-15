# Simple Git Clone in Python

A minimal, educational reimplementation of core features from **Git**, inspired by how Git works internally.

This project is designed to  understand how distributed version control systems function under the hood — including object storage, hashing, commits, and basic repository structure.

> ⚠️ This is for learning purposes only. It is **not** a full replacement for Git.

---

## 📌 Project Goals

This project walks through building a lightweight version control system that:

* Initializes a repository
* Stores content as objects (blobs)
* Creates commits
* Maintains references (like branches)
* Calculates hashes using SHA-1
* Reads and writes objects from a `.minigit`-like directory

By the end, you'll understand the fundamental mechanisms behind Git’s object model.

---

## 🧠 What You’ll Learn

* How Git stores data as content-addressable objects
* How SHA-1 hashing identifies objects
* How commits reference trees and parents
* How refs and HEAD work
* How staging and object writing function conceptually

---

## 📂 Project Structure

```
minigit/
│
├── main.py           # Main CLI entry point        
└── README.md
```

---

## 🛠 Requirements

* Python 3.8+
* No external dependencies (standard library only)

---

## 🚀 Getting Started

### 1️⃣ Clone This Project

```bash
git clone <your-repo-url>
cd minigit
```

### 2️⃣ Initialize a Repository

```bash
python main.py init
```

This creates a structure similar to:

```
.minigit/
├── objects/
├── refs/
│   └── heads/
└── HEAD
```

---

## 🔎 Implemented Commands

### `init`

Initializes a new repository.

```bash
python pygit.py init
```

---

### `hash-object`

Creates a blob object and stores it.

```bash
python main.py hash-object file.txt
```

* Reads file contents
* Prepends object header
* Computes SHA-1 hash
* Compresses and stores in `.git/objects/`

---

### `cat-file`

Displays object content.

```bash
python pygit.py cat-file <sha>
```

---

### `commit`

Creates a commit object referencing a tree and parent.

```bash
python pygit.py commit -m "Initial commit"
```

---

### `log`

Shows commit history.

```bash
python pygit.py log
```

---

## 🧩 Core Concepts Explained

### 1. Objects

Git stores everything as objects:

| Type   | Description         |
| ------ | ------------------- |
| Blob   | File content        |
| Tree   | Directory structure |
| Commit | Snapshot + metadata |

Each object is stored as:

```
<type> <size>\0<content>
```

Then hashed with SHA-1.

---

### 2. Object Storage

Objects are stored as:

```
.git/objects/ab/cdef123456...
```

Where:

* `ab` = first 2 characters of hash
* remainder = filename

---

### 3. HEAD and Branches

HEAD points to a reference:

```
ref: refs/heads/main
```

The branch file contains the latest commit SHA.

---

## 🔐 Hashing Example

```python
import hashlib

data = b"blob 12\0Hello World\n"
sha = hashlib.sha1(data).hexdigest()
print(sha)
```

---

## 🧪 Suggested Learning Milestones

1. Implement `init`
2. Implement `hash-object`
3. Implement `cat-file`
4. Add tree support
5. Add commits
6. Add simple logging
7. Implement checkout
8. Add branching

---

## 📘 Recommended Reading

* Git object model documentation
* Pro Git book
* Git source code (for advanced learners)

---

## ❗ Limitations

This implementation:

* Does not support networking
* Does not implement full index/staging
* Does not handle merge conflicts
* Does not support packfiles
* Is not optimized

---

## 🏗 Future Improvements

* Add staging area
* Implement branching
* Add merge support
* Implement remote push/pull
* Add diff support

---

## 🎓 Educational Purpose

This project is ideal for:

* Backend engineers
* Systems programmers
* Students learning distributed systems
* Security engineers studying content-addressable storage

---

## 📜 License

Educational use only. Extend and modify as needed.

---

## ✨ Final Thoughts

Rebuilding even a small subset of Git is one of the best ways to understand:

* Content-addressable storage
* Immutable data models
* Merkle trees
* Distributed version control

Start small, build incrementally, and verify each layer before moving forward.

Happy building 🚀
