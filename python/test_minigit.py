"""
MiniGit - Automated Test Suite

Tests all MiniGit commands in an isolated temp directory.
Works on any machine — no hardcoded paths.

Usage:
    # From the python/ folder of the cloned repo:
    cd python
    python test_minigit.py

    # Or from anywhere, pass the path to the python/ folder:
    python test_minigit.py /path/to/minigit/python
"""

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


# ------------------------------------------------------------------
# Config
# ------------------------------------------------------------------

# Reconfigure stdout for Windows console compatibility
import io
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

PASS = "[PASS]"
FAIL = "[FAIL]"
results = []


def run(cmd: str, cwd: str) -> tuple[int, str]:
    """Run a shell command and return (returncode, output)."""
    result = subprocess.run(
        cmd, shell=True, cwd=cwd,
        capture_output=True, text=True,
    )
    output = result.stdout + result.stderr
    return result.returncode, output.strip()


def check(test_name: str, condition: bool, detail: str = ""):
    status = PASS if condition else FAIL
    results.append((test_name, condition))
    msg = f"  {status}  {test_name}"
    if detail and not condition:
        msg += f"\n         Detail: {detail}"
    print(msg)


# ------------------------------------------------------------------
# Main test flow
# ------------------------------------------------------------------

def main():
    # Determine source location
    if len(sys.argv) > 1:
        source_dir = Path(sys.argv[1]).resolve()
    else:
        source_dir = Path(__file__).parent.resolve()

    main_py = source_dir / "main.py"
    src_dir = source_dir / "src"

    if not main_py.exists() or not src_dir.exists():
        print(f"Error: Cannot find main.py and src/ in {source_dir}")
        print("Usage: python test_minigit.py <path-to-minigit-python-folder>")
        sys.exit(1)

    # Create a temp directory for testing
    test_dir = Path(tempfile.mkdtemp(prefix="minigit_test_"))
    print(f"\n{'='*60}")
    print(f"  MiniGit Test Suite")
    print(f"  Source:    {source_dir}")
    print(f"  Test dir:  {test_dir}")
    print(f"{'='*60}\n")

    try:
        # Copy source files into test dir
        shutil.copy2(main_py, test_dir / "main.py")
        shutil.copytree(src_dir, test_dir / "src")

        td = str(test_dir)

        # ============================================================
        # TEST 1: init
        # ============================================================
        print("--- 1. init ---")
        code, out = run("python main.py init", td)
        check("init creates repository", code == 0 and "Initialized" in out)
        check(".minigit/ directory exists", (test_dir / ".minigit").is_dir())
        check("HEAD file exists", (test_dir / ".minigit" / "HEAD").exists())
        check("objects/ dir exists", (test_dir / ".minigit" / "objects").is_dir())

        # Double init should fail gracefully
        code, out = run("python main.py init", td)
        check("re-init shows 'already exists'", "already exists" in out.lower())

        # ============================================================
        # TEST 2: add files
        # ============================================================
        print("\n--- 2. add ---")
        (test_dir / "hello.txt").write_text("Hello World\n")
        (test_dir / "readme.md").write_text("# Test Project\n")
        (test_dir / "data").mkdir(exist_ok=True)
        (test_dir / "data" / "notes.txt").write_text("Some notes\n")

        code, out = run("python main.py add hello.txt", td)
        check("add single file", code == 0 and "Added" in out)

        code, out = run("python main.py add readme.md data", td)
        check("add file + directory", code == 0)

        # ============================================================
        # TEST 3: status (pre-commit)
        # ============================================================
        print("\n--- 3. status (pre-commit) ---")
        code, out = run("python main.py status", td)
        check("status shows branch", "On branch master" in out)
        check("status shows new files", "new file" in out)
        check("status shows hello.txt staged", "hello.txt" in out)

        # ============================================================
        # TEST 4: commit
        # ============================================================
        print("\n--- 4. commit ---")
        code, out = run('python main.py commit -m "Initial commit"', td)
        check("commit succeeds", code == 0 and "master" in out)

        # Double commit (no changes) should be rejected
        code, out = run('python main.py commit -m "No changes"', td)
        check("duplicate commit rejected", "clean" in out.lower())

        # ============================================================
        # TEST 5: log
        # ============================================================
        print("\n--- 5. log ---")
        code, out = run("python main.py log", td)
        check("log shows commit", "commit" in out.lower())
        check("log shows author", "Author" in out)
        check("log shows message", "Initial commit" in out)

        # ============================================================
        # TEST 6: status (post-commit, clean)
        # ============================================================
        print("\n--- 6. status (post-commit) ---")
        code, out = run("python main.py status", td)
        check("status is clean after commit",
              "new file" not in out or "Nothing to commit" in out)

        # ============================================================
        # TEST 7: diff
        # ============================================================
        print("\n--- 7. diff ---")
        # Modify a tracked file
        (test_dir / "hello.txt").write_text("Hello World - CHANGED!\n")
        code, out = run("python main.py diff", td)
        check("diff detects modification", "---" in out and "+++" in out)
        check("diff shows old content", "Hello World" in out)
        check("diff shows new content", "CHANGED" in out)

        # ============================================================
        # TEST 8: hash-object
        # ============================================================
        print("\n--- 8. hash-object ---")
        code, out = run("python main.py hash-object hello.txt", td)
        check("hash-object returns hash", code == 0 and len(out.strip()) == 40)
        saved_hash = out.strip()

        # ============================================================
        # TEST 9: cat-file
        # ============================================================
        print("\n--- 9. cat-file ---")
        code, out = run(f"python main.py cat-file {saved_hash}", td)
        check("cat-file shows type", "type: blob" in out)
        check("cat-file shows content", "CHANGED" in out)

        # ============================================================
        # TEST 10: branch
        # ============================================================
        print("\n--- 10. branch ---")
        code, out = run("python main.py branch feature", td)
        check("create branch", "Created" in out)

        code, out = run("python main.py branch", td)
        check("list branches shows feature", "feature" in out)
        check("list branches shows current", "* master" in out or "*  master" in out
              or "* master" in out)

        # ============================================================
        # TEST 11: checkout
        # ============================================================
        print("\n--- 11. checkout ---")
        code, out = run("python main.py checkout feature", td)
        check("checkout switches branch", "Switched" in out and "feature" in out)

        # Add a file on feature branch
        (test_dir / "feature_file.txt").write_text("Feature work\n")
        run("python main.py add feature_file.txt", td)
        run('python main.py commit -m "Feature commit"', td)

        # Switch back
        code, out = run("python main.py checkout master", td)
        check("checkout back to master", "Switched" in out and "master" in out)
        check("feature_file.txt gone on master",
              not (test_dir / "feature_file.txt").exists())

        # Switch to feature again
        code, out = run("python main.py checkout feature", td)
        check("feature_file.txt restored on feature",
              (test_dir / "feature_file.txt").exists())

        # ============================================================
        # TEST 12: checkout -b (create + switch)
        # ============================================================
        print("\n--- 12. checkout -b ---")
        code, out = run("python main.py checkout -b hotfix", td)
        check("checkout -b creates and switches", "Created" in out and "Switched" in out)

        # ============================================================
        # TEST 13: branch -d
        # ============================================================
        print("\n--- 13. branch -d ---")
        run("python main.py checkout master", td)
        code, out = run("python main.py branch -d hotfix", td)
        check("branch -d deletes", "Deleted" in out)

        code, out = run("python main.py branch", td)
        check("deleted branch gone from list", "hotfix" not in out)

        # ============================================================
        # TEST 14: gc
        # ============================================================
        print("\n--- 14. gc ---")
        code, out = run("python main.py gc", td)
        check("gc runs successfully", code == 0)
        check("gc reports results", "unreachable" in out.lower() or "clean" in out.lower()
              or "reachable" in out.lower())

        # ============================================================
        # TEST 15: .minigitignore
        # ============================================================
        print("\n--- 15. .minigitignore ---")
        (test_dir / "__pycache__").mkdir(exist_ok=True)
        (test_dir / "__pycache__" / "test.pyc").write_text("bytecode")
        (test_dir / "debug.log").write_text("log data")
        (test_dir / ".minigitignore").write_text("__pycache__/\n*.log\n")

        code, out = run("python main.py status", td)
        check("__pycache__ excluded from status", "__pycache__" not in out or "test.pyc" not in out)
        check("*.log excluded from status", "debug.log" not in out)

        # ============================================================
        # TEST 16: error handling
        # ============================================================
        print("\n--- 16. error handling ---")
        code, out = run("python main.py add nonexistent.txt", td)
        check("add missing file gives error", code != 0 or "Error" in out or "not found" in out.lower())

        code, out = run("python main.py cat-file 0000000000000000000000000000000000000000", td)
        check("cat-file invalid hash gives error", code != 0 or "Error" in out or "not found" in out.lower())

    finally:
        # Cleanup
        shutil.rmtree(test_dir, ignore_errors=True)

    # ============================================================
    # Summary
    # ============================================================
    print(f"\n{'='*60}")
    passed = sum(1 for _, ok in results if ok)
    total = len(results)
    print(f"  Results: {passed}/{total} tests passed")
    if passed == total:
        print("  ALL TESTS PASSED!")
    else:
        print("  Failed tests:")
        for name, ok in results:
            if not ok:
                print(f"    FAILED: {name}")
    print(f"{'='*60}\n")

    sys.exit(0 if passed == total else 1)


if __name__ == "__main__":
    main()
