#!/usr/bin/env python3
# Copyright (c) Facebook, Inc. and its affiliates.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.
"""Module containing all of the custom GDB commands to be used for memory analysis.
This is equivalent to a GDB command file, and can only be called from a GDB process."""

import os
import sys

import gdb

TEMPLATES_PATH = os.getenv("MEMORY_ANALYZER_TEMPLATES_PATH")


def lock_GIL(func):
    def wrapper(*args):
        out = gdb.execute("call (void*) PyGILState_Ensure()", to_string=True)
        gil_value = next((x for x in out.split() if x.startswith("$")), "$1")
        print("GIL", gil_value)
        func(*args)
        call = "call (void) PyGILState_Release(" + gil_value + ")"
        gdb.execute(call)

    return wrapper


class FileCommand(gdb.Command):
    def __init__(self):
        super(FileCommand, self).__init__("file_command", gdb.COMMAND_NONE)

    @lock_GIL
    def invoke(self, filename, from_tty):
        cmd_string = "with open('{filename}') as f: exec(f.read())".format(
            filename=filename
        )
        gdb.execute(
            'call (void) PyRun_SimpleString("{cmd_str}")'.format(cmd_str=cmd_string)
        )


FileCommand()
pid = gdb.selected_inferior().pid
gdb.execute(
    "file_command {TEMPLATES_PATH}/rendered_template-{pid}.py.out".format(
        TEMPLATES_PATH=TEMPLATES_PATH, pid=pid
    )
)
