#!/usr/bin/env python3
# Copyright (c) Facebook, Inc. and its affiliates.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

import builtins
import imp
import os
import sys
from unittest import TestCase, mock

# Because we cannot `import gdb` except for modules called via GDB, we must
# mock the `import gdb` in gdb_commands.
mock_gdb = mock.MagicMock()
sys.modules["gdb"] = mock_gdb

if True:
    from .. import gdb_commands  # isort: skip doesn't appear to work


class GdbCommandsTests(TestCase):

    # def test_alter_path_strings(self):
    #     func = mock.Mock()
    #     wrap = gdb_commands.alter_path(func)
    #     wrap()
    #     first_str = "import sys; sys.path.append('test_path')"
    #     call_1 = f'call PyRun_SimpleString("{first_str}")'
    #     second_str = "sys.path.remove('test_path')"
    #     call_2 = f'call PyRun_SimpleString("{second_str}")'
    #     mock_calls = [mock.call(call_1), mock.call(call_2)]
    #     mock_gdb.execute.assert_has_calls(mock_calls)

    @mock.patch("sys.stdout.write")
    def test_lock_GIL(self, mock_write):
        func = mock.Mock()
        mock_gdb.execute.return_value = (
            "[New Thread 0x7f48e4dd7700 (LWP 2640572)]\n$2 = PyGILState_UNLOCKED\n"
        )
        wrap = gdb_commands.lock_GIL(func)
        wrap()
        call_1 = "call (void*) PyGILState_Ensure()"
        call_2 = "call (void) PyGILState_Release($2)"
        mock_calls = [mock.call(call_1, to_string=True), mock.call(call_2)]
        mock_gdb.execute.assert_has_calls(mock_calls)
        mock_write.assert_has_calls([mock.call("$2"), mock.call("\n")])

    @mock.patch("sys.stdout.write")
    def test_lock_GIL_weird_return(self, mock_write):
        func = mock.Mock()
        mock_gdb.execute.return_value = "[New Thread 0x7f48e4dd7700 (LWP 2640572)]"
        wrap = gdb_commands.lock_GIL(func)
        wrap()
        call_1 = "call (void*) PyGILState_Ensure()"
        call_2 = "call (void) PyGILState_Release($1)"
        mock_calls = [mock.call(call_1, to_string=True), mock.call(call_2)]
        mock_gdb.execute.assert_has_calls(mock_calls)
        mock_write.assert_has_calls([mock.call("$1"), mock.call("\n")])
