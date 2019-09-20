#!/usr/bin/env python3
# Copyright (c) Facebook, Inc. and its affiliates.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

from tempfile import NamedTemporaryFile
from unittest import TestCase, mock

from .. import analysis_utils
from ..frontend import frontend_utils


class FrontendUtilsTest(TestCase):
    def test_readable_size_correct_no_snapshot(self):
        scales = ["B", "KB", "MB", "GB", "TB", "EB"]
        original_val = 10
        for i in range(6):
            val = original_val * (1024 ** i)
            string_val = frontend_utils.readable_size(val)
            correct_output = f"10.00{scales[i]:>5}"
            self.assertEqual(string_val, correct_output)

    def test_readable_size_correct_with_snapshot(self):
        scales = ["B", "KB", "MB", "GB", "TB", "EB"]
        original_val = 10
        for i in range(6):
            val = original_val * (1024 ** i)
            string_val = frontend_utils.readable_size(val, True)
            correct_output = f"+10.00{scales[i]:>5}"
            self.assertEqual(string_val, correct_output)

    def test_readable_size_neg_input(self):
        original_val = -10
        string_val = frontend_utils.readable_size(original_val)
        correct_output = "-10.00    B"
        self.assertEqual(string_val, correct_output)

    def test_readable_size_invalid_input(self):
        original_val = "10"
        with self.assertRaises(TypeError):
            frontend_utils.readable_size(original_val)

    def test_init_table_field_names(self):
        pt = frontend_utils.init_table(references=False, snapshot=False)
        self.assertEqual(pt.field_names, ["Object", "Count", "Size"])
        pt = frontend_utils.init_table(references=False, snapshot=True)
        self.assertEqual(pt.field_names, ["Object", "Count Diff", "Size Diff"])
        pt = frontend_utils.init_table(references=True, snapshot=False)
        self.assertEqual(
            pt.field_names,
            ["Object", "Count", "Size", "References", "Backwards References"],
        )
        pt = frontend_utils.init_table(references=True, snapshot=True)
        self.assertEqual(
            pt.field_names,
            ["Object", "Count Diff", "Size Diff", "References", "Backwards References"],
        )

    def test_init_table_alignment(self):
        pt = frontend_utils.init_table(references=False, snapshot=False)
        self.assertEqual(pt._align, {"Object": "l", "Count": "r", "Size": "r"})
        pt = frontend_utils.init_table(references=True, snapshot=False)
        self.assertEqual(
            pt._align,
            {
                "Object": "l",
                "Count": "r",
                "Size": "r",
                "References": "c",
                "Backwards References": "c",
            },
        )
        pt = frontend_utils.init_table(references=True, snapshot=True)
        self.assertEqual(
            pt._align,
            {
                "Object": "l",
                "Count Diff": "r",
                "Size Diff": "r",
                "References": "c",
                "Backwards References": "c",
            },
        )
        pt = frontend_utils.init_table(references=False, snapshot=True)
        self.assertEqual(
            pt._align, {"Object": "l", "Count Diff": "r", "Size Diff": "r"}
        )

    def test_format_output_default(self):
        items = analysis_utils.RetrievedObjects(
            pid=1234,
            title="Analysis of pid 1234",
            data=[["Item 1", 10, 1024], ["Item 2", 1000, 1_048_576]],
        )
        correct_items = [
            ["Item 2", 1000, "1024.00   KB"],
            ["Item 1", 10, "1024.00    B"],
        ]
        pt = frontend_utils.format_summary_output(items)
        self.assertEqual(pt._rows, correct_items)

    def test_format_output_no_data(self):
        items = analysis_utils.RetrievedObjects(
            pid=1234, title="Analysis of pid 1234", data=None
        )
        correct_items = [[f"No data to display for pid 1234.", 0, "0.00    B"]]
        pt = frontend_utils.format_summary_output(items)
        self.assertEqual(pt._rows, correct_items)

    def test_format_output_snapshot(self):
        items = analysis_utils.RetrievedObjects(
            pid=1234,
            title="Snapshot Differences",
            data=[["Item 1", 10, 1024], ["Item 2", 1000, 1_048_576]],
        )
        correct_items = [
            ["Item 2", "+1000", "+1024.00   KB"],
            ["Item 1", "+10", "+1024.00    B"],
        ]
        pt = frontend_utils.format_summary_output(items)
        self.assertEqual(pt._rows, correct_items)

    def test_format_output_with_references(self):
        items = analysis_utils.RetrievedObjects(
            pid=1234,
            title="Analysis of pid 1234",
            data=[
                ["Item 1", 10, 1034, "filename.png", "filename2.png"],
                ["Item 2", 1000, 10042],
            ],
        )
        updated_items = [
            ["Item 2", 1000, frontend_utils.readable_size(10042), "", ""],
            [
                "Item 1",
                10,
                frontend_utils.readable_size(1034),
                "filename.png",
                "filename2.png",
            ],
        ]
        pt = frontend_utils.format_summary_output(items)
        self.assertEqual(pt._rows, items.data)
        self.assertEqual(items.data, updated_items)
