#!/usr/bin/env python3
# Copyright (c) Facebook, Inc. and its affiliates.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

import os
import pickle
import sys
import tempfile
from unittest import TestCase, mock

import objgraph
from jinja2 import Environment, FileSystemLoader
from pympler import muppy, summary  # noqa

from .. import analysis_utils


class ObjGraphTemplateTests(TestCase):
    template_name = "analysis.py.template"
    filename = "some_filename"
    templates_path = f"{os.path.abspath(os.path.dirname(__file__))}/../templates/"
    pid = 1234
    specific_refs = ["str", "int"]

    def setUp(self):
        self.items = [
            ["builtins.test1", 1, 10000],
            ["__main__.test2", 3, 5],
            ["ast._things.test3", 10, 1024],
        ]
        # TODO: Add tests for summary obj and the _repr
        mock_summ = mock.patch.object(summary, "summarize", return_value=self.items)
        mock_summ.start()
        self.addCleanup(mock_summ.stop)

    def tearDown(self):
        if os.path.isfile(f"{self.templates_path}rendered_template.py.out"):
            os.remove(f"{self.templates_path}rendered_template.py.out")

    def test_with_no_references(self):
        template = analysis_utils.render_template(
            self.template_name,
            self.templates_path,
            0,
            self.pid,
            [],
            self.filename,
            None,
        )
        with mock.patch("builtins.open", mock.mock_open(), create=True) as mock_fifo:
            exec(template)
        mock_fifo.assert_called_with(f"/tmp/memanz_pipe_{self.pid}", "wb")
        output_bytes = pickle.dumps(self.items)
        mock_fifo().write.assert_called_with(output_bytes)

    @mock.patch.object(objgraph, "show_backrefs")
    @mock.patch.object(objgraph, "show_refs")
    def test_with_num_references(self, mock_refs, mock_back_refs):
        template = analysis_utils.render_template(
            self.template_name,
            self.templates_path,
            1,
            self.pid,
            [],
            self.filename,
            None,
        )
        with mock.patch("builtins.open", mock.mock_open(), create=True) as mock_fifo:
            exec(template, {})
        handler = mock_fifo()
        output_bytes = pickle.dumps(self.items)
        handler.write.assert_called_with(output_bytes)
        dirname = os.path.dirname(os.path.abspath(self.filename))
        self.assertEqual(
            self.items,
            [
                [
                    "builtins.test1",
                    1,
                    10000,
                    f"{dirname}/ref_1234_test1.png",
                    f"{dirname}/backref_1234_test1.png",
                ],
                ["ast._things.test3", 10, 1024],
                ["__main__.test2", 3, 5],
            ],
        )

    @mock.patch.object(objgraph, "show_backrefs")
    @mock.patch.object(objgraph, "show_refs")
    def test_with_specific_references(self, mock_refs, mock_back_refs):
        with tempfile.TemporaryDirectory() as d:
            template = analysis_utils.render_template(
                self.template_name,
                self.templates_path,
                0,
                self.pid,
                ["test3"],
                self.filename,
                d,
            )
            self.assertEqual(1, len(os.listdir(d)), os.listdir(d))

        with mock.patch("builtins.open", mock.mock_open(), create=True) as mock_fifo:
            exec(template, {})
        handler = mock_fifo()
        output_bytes = pickle.dumps(self.items)
        handler.write.assert_called_with(output_bytes)
        dirname = os.path.dirname(os.path.abspath(self.filename))
        self.assertEqual(
            self.items,
            [
                ["builtins.test1", 1, 10000],
                ["__main__.test2", 3, 5],
                [
                    "ast._things.test3",
                    10,
                    1024,
                    f"{dirname}/ref_1234_test3.png",
                    f"{dirname}/backref_1234_test3.png",
                ],
            ],
        )
