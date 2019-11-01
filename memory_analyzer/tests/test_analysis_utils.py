#!/usr/bin/env python3
# Copyright (c) Facebook, Inc. and its affiliates.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

import os
import pickle
import subprocess
import sys
from unittest import TestCase, mock

from .. import analysis_utils


class AnalysisUtilsTest(TestCase):
    PID = 123
    CURRENT_PATH = os.path.abspath(f"{os.path.dirname(__file__)}/..")

    def setUp(self):
        self.gdb = analysis_utils.GDBObject(
            self.PID, self.CURRENT_PATH, sys.executable, "/tmp"
        )
        self.filepath = os.path.abspath(
            f"{os.path.dirname(__file__)}/../gdb_commands.py"
        )
        self.executable = sys.executable
        # Swallow the info messages
        patch_info = mock.patch("memory_analyzer.frontend.frontend_utils.echo_info")
        self.mock_info = patch_info.start()
        self.addCleanup(self.mock_info.stop)

    @mock.patch("memory_analyzer.analysis_utils.copyfile")
    @mock.patch("memory_analyzer.analysis_utils.subprocess.Popen", autospec=True)
    def test_command_string_built_correctly(self, mock_sub, _):
        with mock.patch("builtins.open", mock.mock_open()):
            self.gdb.unpickle_pipe = mock.MagicMock()
            self.gdb.run_analysis()
        cmd_list = [
            "gdb",
            "-q",
            self.executable,
            "-p",
            f"{self.PID}",
            "-ex",
            "set trace-commands on",
            "-batch-silent",
            "-ex",
            f"set directories {self.CURRENT_PATH}",
            "-ex",
            f'py sys.path.append("{self.CURRENT_PATH}")',
            "-x",
            f"{self.filepath}",
        ]
        mock_sub.assert_called_with(cmd_list, stderr=subprocess.DEVNULL)
        calls = [
            mock.call(f"Analyzing pid {self.PID}"),
            mock.call(f"Setting up GDB for pid {self.PID}"),
        ]
        self.mock_info.assert_has_calls(calls)

    @mock.patch("memory_analyzer.analysis_utils.copyfile")
    @mock.patch("memory_analyzer.analysis_utils.subprocess.Popen", autospec=True)
    def test_command_string_built_correctly_debug_mode(self, mock_sub, _):
        with mock.patch("builtins.open", mock.mock_open()):
            self.gdb.unpickle_pipe = mock.MagicMock()
            self.gdb.run_analysis(debug=True)
        cmd_list = [
            "gdb",
            "-q",
            self.executable,
            "-p",
            f"{self.PID}",
            "-ex",
            "set trace-commands on",
            "-batch",
            "-ex",
            f"set directories {self.CURRENT_PATH}",
            "-ex",
            f'py sys.path.append("{self.CURRENT_PATH}")',
            "-x",
            f"{self.filepath}",
        ]
        mock_sub.assert_called_with(cmd_list, stderr=sys.stderr)
        calls = [
            mock.call(f"Analyzing pid {self.PID}"),
            mock.call(f"Setting up GDB for pid {self.PID}"),
        ]
        self.mock_info.assert_has_calls(calls)

    @mock.patch("memory_analyzer.analysis_utils.pickle.load")
    @mock.patch("memory_analyzer.frontend.frontend_utils.echo_error")
    def test_unpickle_pipe_errors(self, mock_echo, mock_pickle):
        mock_pickle.side_effect = NameError("Random Exception")
        with self.assertRaises(NameError):
            self.gdb.unpickle_pipe("Fifo Data")
        mock_echo.assert_called_with(
            "NameError occurred during analysis: Random Exception"
        )

    @mock.patch("memory_analyzer.analysis_utils.pickle.load")
    @mock.patch("memory_analyzer.frontend.frontend_utils.echo_error")
    def test_unpickle_pipe_unpickle_errors(self, mock_echo, mock_pickle):
        mock_pickle.side_effect = pickle.UnpicklingError("Error")
        with self.assertRaises(pickle.UnpicklingError):
            self.gdb.unpickle_pipe("Fifo Data")
        mock_echo.assert_called_with("Error retrieving data from process: Error")

    @mock.patch("memory_analyzer.analysis_utils.pickle.load")
    @mock.patch("memory_analyzer.frontend.frontend_utils.echo_error")
    def test_read_items_exception(self, mock_echo, mock_pickle):
        mock_pickle.return_value = AttributeError("Whats up")
        with self.assertRaises(AttributeError):
            self.gdb.unpickle_pipe("Fifo Data")
        mock_echo.assert_called_with(
            "AttributeError occurred during analysis: Whats up"
        )

    @mock.patch("memory_analyzer.analysis_utils.pickle.load")
    @mock.patch("memory_analyzer.frontend.frontend_utils.echo_error")
    def test_snapshot_diff_error(self, mock_echo, mock_pickle):
        mock_pickle.side_effect = pickle.UnpicklingError("Error")
        with mock.patch("builtins.open", mock.mock_open()):
            out = analysis_utils.snapshot_diff(["Item"], "filename")
        mock_echo.assert_called_with("Error unpickling the data from filename: Error")
        self.assertIsNone(out)
