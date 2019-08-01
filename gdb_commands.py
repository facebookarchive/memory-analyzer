#!/usr/bin/env python3
"""Module containing all of the custom GDB commands to be used for memory analysis.
This is equivalent to a GDB command file, and can only be called from a GDB process."""

import gdb
import os
import sys

TEMPLATES_PATH = os.path.abspath(os.path.dirname(sys.argv[0])) + "/templates"

def lock_GIL(func):
    def wrapper(*args):
        out = gdb.execute("call PyGILState_Ensure()", to_string=True)
        gil_value = next((x for x in out.split() if x.startswith('$')), "$1")
        print(gil_value)
        func(*args)
        call = "call PyGILState_Release(" + gil_value + ")"
        gdb.execute(call)

    return wrapper


def alter_path(func):
    def wrapper(*args):
        append_str = "import sys; sys.path.append('{path}')".format(path=EXTRACTED_PAR_PATH)
        gdb.execute('call PyRun_SimpleString("{append_str}")'.format(append_str=append_str))
        func(*args)
        remove_str = "sys.path.remove('{path}')".format(path=EXTRACTED_PAR_PATH)
        gdb.execute('call PyRun_SimpleString("{remove_str}")'.format(remove_str=remove_str))
    return wrapper


class FileCommand(gdb.Command):
    def __init__(self):
        super(FileCommand, self).__init__("file_command", gdb.COMMAND_NONE)

    @lock_GIL
    def invoke(self, filename, from_tty):
        cmd_string = "with open('{filename}') as f: exec(f.read())".format(filename=filename)
        gdb.execute('call PyRun_SimpleString("{cmd_str}")'.format(cmd_str=cmd_string))


FileCommand()
pid = gdb.selected_inferior().pid
gdb.execute("file_command {TEMPLATES_PATH}/rendered_template-{pid}.py.out".format(TEMPLATES_PATH=TEMPLATES_PATH, pid=pid))
