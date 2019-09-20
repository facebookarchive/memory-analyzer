#!/usr/bin/env python3
# Copyright (c) Facebook, Inc. and its affiliates.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

import errno
from functools import partial
from unittest import TestCase, mock

import click

from memory_analyzer import memory_analyzer


class FakeOSError(OSError):
    def __init__(self, errno):
        super().__init__()
        self.errno = errno


def fake_kill(pid, sig, errno=None):
    if pid != 42:
        raise FakeOSError(errno)


class MainLibTests(TestCase):
    @mock.patch("memory_analyzer.memory_analyzer.os.geteuid")
    def test_is_root_passes(self, mock_geteuid):
        mock_geteuid.return_value = 0
        self.assertTrue(memory_analyzer.is_root())

    @mock.patch("memory_analyzer.memory_analyzer.os.geteuid")
    def test_is_root_fails(self, mock_geteuid):
        mock_geteuid.return_value = 42
        self.assertFalse(memory_analyzer.is_root())

    @mock.patch("memory_analyzer.memory_analyzer.os.kill")
    def test_validate_pids_with_valid_pids(self, mock_kill):
        ctx = param = mock.MagicMock()
        mock_kill.side_effect = fake_kill
        self.assertEqual([42], memory_analyzer.validate_pids(ctx, param, [42]))

    @mock.patch("memory_analyzer.memory_analyzer.os.geteuid")
    @mock.patch("memory_analyzer.memory_analyzer.os.kill")
    def test_validate_pids_kills_with_signal_value_zero(self, mock_kill, mock_geteuid):
        mock_geteuid.return_value = 42
        ctx = param = mock.MagicMock()

        memory_analyzer.validate_pids(ctx, param, [42, 314])

        mock_kill.assert_has_calls([mock.call(42, 0), mock.call(314, 0)])

    @mock.patch("memory_analyzer.memory_analyzer.os.geteuid")
    @mock.patch("memory_analyzer.memory_analyzer.os.kill")
    def test_validate_pids_with_an_invalid_pid_and_no_root(
        self, mock_kill, mock_geteuid
    ):
        mock_geteuid.return_value = 42
        ctx = param = mock.MagicMock()
        mock_kill.side_effect = partial(fake_kill, errno=errno.EPERM)

        with self.assertRaises(click.UsageError):
            memory_analyzer.validate_pids(ctx, param, [42, 314])

    @mock.patch("memory_analyzer.memory_analyzer.os.geteuid")
    @mock.patch("memory_analyzer.memory_analyzer.os.kill")
    def test_validate_pids_with_an_invalid_pid_and_error_is_not_permission_related(
        self, mock_kill, mock_geteuid
    ):
        mock_geteuid.return_value = 42
        ctx = param = mock.MagicMock()
        mock_kill.side_effect = partial(fake_kill, errno=errno.ESRCH)

        with self.assertRaises(click.BadParameter):
            memory_analyzer.validate_pids(ctx, param, [314])

    def test_check_positive_int_valid(self):
        ctx = param = mock.MagicMock()

        self.assertEqual(0, memory_analyzer.check_positive_int(ctx, param, 0))
        self.assertEqual(42, memory_analyzer.check_positive_int(ctx, param, 42))

    def test_check_positive_int_invalid(self):
        ctx = param = mock.MagicMock()

        with self.assertRaises(click.BadParameter):
            memory_analyzer.check_positive_int(ctx, param, -1)
