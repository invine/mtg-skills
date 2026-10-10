#!/usr/bin/env python3
"""Compile scripts and run the skill's offline regressions; no network or bytecode files."""
import sys
import unittest
from pathlib import Path

sys.dont_write_bytecode = True
directory = Path(__file__).resolve().parent
for source in directory.glob("*.py"):
    compile(source.read_text(), str(source), "exec")
suite = unittest.defaultTestLoader.discover(str(directory), pattern="test_*.py")
result = unittest.TextTestRunner(verbosity=2).run(suite)
sys.exit(0 if result.wasSuccessful() else 1)
