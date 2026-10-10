#!/usr/bin/env python3
"""Install a repository-local test guard that chains existing hooks and checks outgoing revisions."""
import argparse
import io
import json
import os
import re
import shlex
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

SKILLS = {"review-mtg-limited-games", "build-mtg-limited-deck"}


def git(repo, *args):
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    return subprocess.check_output(["git", "-C", str(repo), *args], env=env)


def install(repo):
    repo = Path(git(repo, "rev-parse", "--show-toplevel").decode().strip())
    current = Path(git(repo, "rev-parse", "--path-format=absolute", "--git-path", "hooks").decode().strip())
    common = Path(git(repo, "rev-parse", "--path-format=absolute", "--git-common-dir").decode().strip())
    target = common / "mtg-validation-hooks"
    config = target / "chain.json"
    if current == target:
        current = Path(json.loads(config.read_text())["original_hooks"])
    target.mkdir(parents=True, exist_ok=True)
    config.write_text(json.dumps({"original_hooks": str(current)}))
    # Every existing non-pre-push hook keeps its original executable and behavior.
    if current.exists():
        for hook in current.iterdir():
            if hook.is_file() and os.access(hook, os.X_OK) and hook.name != "pre-push":
                destination = target / hook.name
                if destination.is_symlink():
                    destination.unlink()
                elif destination.exists() and not destination.read_text().startswith("#!/bin/sh\n# MTG hook forwarder\n"):
                    raise ValueError(f"Refusing to replace an unknown hook: {destination}")
                destination.write_text("#!/bin/sh\n# MTG hook forwarder\nexec " + shlex.quote(str(hook)) + ' "$@"\n')
                destination.chmod(0o755)
    command = [sys.executable, "-B", str(Path(__file__).resolve()), "run", str(repo), str(config)]
    wrapper = target / "pre-push"
    wrapper.write_text("#!/bin/sh\nexec " + " ".join(shlex.quote(s) for s in command) + ' "$@"\n')
    wrapper.chmod(0o755)
    git(repo, "config", "--local", "core.hooksPath", str(target))
    return {"installed": True, "hooks": str(target), "chained_hooks": str(current)}


def check_revision(repo, revision):
    if not re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", revision):
        raise ValueError("Expected the outgoing commit hash")
    files = git(repo, "ls-tree", "-r", "--name-only", revision).decode().splitlines()
    directories = []
    for name in files:
        if not name.endswith("/SKILL.md"):
            continue
        content = git(repo, "show", revision + ":" + name).decode()
        if any(re.search(r"^name:\s*" + re.escape(skill) + r"\s*$", content, re.M) for skill in SKILLS):
            directories.append(str(Path(name).parent))
    if not directories:
        return
    archive = git(repo, "archive", "--format=zip", revision, "--", *directories)
    with tempfile.TemporaryDirectory(prefix="mtg-validation-") as directory:
        root = Path(directory)
        with zipfile.ZipFile(io.BytesIO(archive)) as zipped:
            for item in zipped.infolist():
                if not (root / item.filename).resolve().is_relative_to(root):
                    raise ValueError("Unexpected archive path")
            zipped.extractall(root)
        env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        for relative in directories:
            scripts = root / relative / "scripts"
            for source in scripts.glob("*.py"):
                compile(source.read_text(), str(source), "exec")
            if list(scripts.glob("test_*.py")):
                subprocess.run([sys.executable, "-B", "-m", "unittest", "discover", "-s", str(scripts), "-p", "test_*.py"],
                               cwd=root, env=env, check=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    setup = sub.add_parser("install")
    setup.add_argument("repo", type=Path)
    run = sub.add_parser("run")
    run.add_argument("repo", type=Path)
    run.add_argument("config", type=Path)
    run.add_argument("hook_args", nargs="*")
    check = sub.add_parser("check-revision")
    check.add_argument("repo", type=Path)
    check.add_argument("revision")
    args = parser.parse_args()
    try:
        if args.command == "install":
            print(json.dumps(install(args.repo)))
        elif args.command == "check-revision":
            check_revision(args.repo, args.revision)
        else:
            payload = sys.stdin.buffer.read()
            revisions = set()
            for line in payload.decode().splitlines():
                fields = line.split()
                if len(fields) != 4:
                    raise ValueError("Unexpected pre-push input")
                if set(fields[1]) != {"0"}:
                    revisions.add(fields[1])
            for revision in sorted(revisions):
                check_revision(args.repo, revision)
            original = Path(json.loads(args.config.read_text())["original_hooks"]) / "pre-push"
            if original.is_file() and os.access(original, os.X_OK):
                return subprocess.run([str(original), *args.hook_args], input=payload).returncode
        return 0
    except (ValueError, OSError, SyntaxError, subprocess.CalledProcessError) as exc:
        print(f"MTG validation stopped the operation: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
