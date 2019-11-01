#!/usr/bin/env python3
# Copyright (c) Facebook, Inc. and its affiliates.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

import os
import subprocess
import sys
import tempfile
import time
import unittest


class IntegrationTest(unittest.TestCase):
    def test_works_at_all(self):
        output_name = tempfile.mktemp()
        print(output_name)

        # This tells us that everything important was packaged if we tox
        # installed an sdist, but doesn't tell us anything if this was setup.py
        # develop'd in a git repo.
        os.chdir("/")

        self.assertFalse(os.path.exists(output_name))
        with open("/proc/sys/kernel/yama/ptrace_scope") as f:
            value = f.read().strip()

        self.assertEqual("0", value, "/proc/sys/kernel/yama/ptrace_scope should be 0")

        # Presumably this is a virtualenv python executable that has objgraph
        # and pympler
        try:
            child = subprocess.Popen(
                [sys.executable, "-c", "import sys; sys.stdin.readline()"],
                stdin=subprocess.PIPE,
            )
            # TODO figure out how we can ensure setup is done; right now we're
            # just relying on it taking a while to launch/attach
            analyzer = subprocess.Popen(
                ["memory_analyzer", "run", "-q", "-f", output_name, str(child.pid)]
            )
            rc = analyzer.wait(5)
        finally:
            child.communicate(b"\n")

        self.assertEqual(0, rc)
        self.assertTrue(os.path.exists(output_name))
        # TODO verify pickle has some strs


if __name__ == "__main__":
    unittest.main()
