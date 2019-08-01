#!/usr/bin/env python3	
import builtins	
import imp
import os
import sys
from unittest import TestCase, mock	
	
	
# Because we cannot `import gdb` except for modules called via GDB, we must	
# mock the `import gdb` in gdb_commands.	
orig_import = __import__	
mock_gdb = mock.MagicMock()	
	
	
def import_mock(name, *args):	
    if name == "gdb":	
        return mock_gdb	
    return orig_import(name, *args)	
	
	
with mock.patch("builtins.__import__", side_effect=import_mock):	
    # Hacks to import gdb_commands with the .gdb extension	
    current_path = os.path.abspath(os.path.dirname(sys.argv[0]))
    filepath = f"{current_path}/gdb_commands.py"	
    gdb_commands = imp.load_source("gdb_commands", filepath)	
	
	
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
	
    def test_lock_GIL(self):	
        func = mock.Mock()	
        mock_gdb.execute.return_value = (	
            "[New Thread 0x7f48e4dd7700 (LWP 2640572)]\n$2 = PyGILState_UNLOCKED\n"	
        )	
        wrap = gdb_commands.lock_GIL(func)	
        wrap()	
        call_1 = "call PyGILState_Ensure()"	
        call_2 = "call PyGILState_Release($2)"	
        mock_calls = [mock.call(call_1, to_string=True), mock.call(call_2)]	
        mock_gdb.execute.assert_has_calls(mock_calls)	
	
    def test_lock_GIL_weird_return(self):	
        func = mock.Mock()	
        mock_gdb.execute.return_value = "[New Thread 0x7f48e4dd7700 (LWP 2640572)]"	
        wrap = gdb_commands.lock_GIL(func)	
        wrap()	
        call_1 = "call PyGILState_Ensure()"	
        call_2 = "call PyGILState_Release($1)"	
        mock_calls = [mock.call(call_1, to_string=True), mock.call(call_2)]	
        mock_gdb.execute.assert_has_calls(mock_calls)
