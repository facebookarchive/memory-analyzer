#!/usr/bin/env python3
# Copyright (c) Facebook, Inc. and its affiliates.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

import errno
import io
import os
import pickle
import select
import stat
import subprocess
import sys
from contextlib import contextmanager
from shutil import copyfile
from typing import List

from attr import dataclass
from jinja2 import Environment, FileSystemLoader
from pympler import summary

from .frontend import frontend_utils


@dataclass
class RetrievedObjects:
    pid: int
    title: str
    data: List[List[int]]


class GDBObject:
    def __init__(self, pid, current_path, executable, template_out_path):
        """
        Args:

            pid: numeric pid of the target
            current_path: the directory containing gdb_commands.py
            executable: the binary passed as the first arg to gdb
            template_out_path: the location that analysis.py rendered templates
                end up in.
        """
        self.pid = pid
        self.fifo = f"/tmp/memanz_pipe_{self.pid}"
        self.current_path = current_path
        # These should all be the same, so safe for threads.
        os.putenv("MEMORY_ANALYZER_TEMPLATES_PATH", template_out_path)
        self.executable = executable

    def run_analysis(self, debug=False):
        self.create_pipe()
        frontend_utils.echo_info(f"Analyzing pid {self.pid}")
        command_file = f"{self.current_path}/gdb_commands.py"
        command = [
            "gdb",
            "-q",
            # Activates python for GDB.
            self.executable,
            "-p",
            f"{self.pid}",
            "-ex",
            "set trace-commands on",
            f"{'-batch' if debug else '-batch-silent'}",
            # This shouldn't be required since we specify absolute path, but
            # TODO this gives us a way to inject a path with objgraph on it.
            "-ex",
            # Lets gdb find the correct gdb_commands script.
            f"set directories {self.current_path}",
            "-ex",
            # Sets the correct path for gdb_commands, else C-API commands fail.
            f'py sys.path.append("{self.current_path}")',
            "-x",
            f"{command_file}",
        ]
        frontend_utils.echo_info(f"Setting up GDB for pid {self.pid}")
        proc = subprocess.Popen(
            command, stderr=sys.stderr if debug else subprocess.DEVNULL
        )
        with self.drain_pipe(proc) as data:
            retrieved_objs = RetrievedObjects(
                pid=self.pid,
                title=f"Analysis for {self.pid}",
                data=self.unpickle_pipe(data),
            )

        self._end_subprocess(proc)
        return retrieved_objs

    @contextmanager
    def drain_pipe(self, process):
        """
        We need this because by default, `open`s on named pipes block. If GDB or
        the injected GDB extension in Python crash, the process will never write
        to the pipe and we will block opening and `memory_analyzer` won't exit.
        """
        try:
            pipe = os.open(self.fifo, os.O_RDONLY | os.O_NONBLOCK)
            result = io.BytesIO()
            timeout = 0.1  # seconds

            partial_read = None
            while bool(partial_read) or process.poll() is None:
                ready_fds, _, _ = select.select([pipe], [], [], timeout)

                if len(ready_fds) > 0:
                    ready_fd = ready_fds[0]
                    try:
                        partial_read = os.read(ready_fd, select.PIPE_BUF)
                    except BlockingIOError:
                        partial_read = None

                    if partial_read:
                        result.write(partial_read)

            result.seek(0)
            yield result
            result.close()
        except Exception as e:
            frontend_utils.echo_error(f"Failed with {e}")
            self._end_subprocess(process)
            sys.exit(1)
        finally:
            os.close(pipe)

    def _end_subprocess(self, proc):
        try:
            proc.wait(5)
        except TimeoutError:
            proc.kill()

    def create_pipe(self):
        try:
            os.mkfifo(self.fifo)
            os.chmod(str(self.fifo), 0o666)
        except OSError as oe:
            if oe.errno != errno.EEXIST:
                raise

    def unpickle_pipe(self, fifo):
        frontend_utils.echo_info("Gathering data...")
        try:
            items = pickle.load(fifo)
            if items:
                if isinstance(items, Exception):
                    raise items
                return items
        except EOFError:
            return
        except pickle.UnpicklingError as e:
            frontend_utils.echo_error(f"Error retrieving data from process: {e}")
            raise
        except Exception as e:
            frontend_utils.echo_error(
                f"{type(e).__name__} occurred during analysis: {e}"
            )
            raise


def load_template(name, templates_path):
    env = Environment(autoescape=False, loader=FileSystemLoader(templates_path))
    return env.get_template(name)


def render_template(
    template_name,
    templates_path,
    num_refs,
    pid,
    specific_refs,
    output_path,
    template_out_dir,
):
    objgraph_template = load_template(template_name, templates_path)
    template = objgraph_template.render(
        num_refs=num_refs, pid=pid, specific_refs=specific_refs, output_path=output_path
    )
    # This path has to match the end of gdb_commands.py; the env var is set in
    # GDBObject constructor above.
    if template_out_dir:
        with open(
            os.path.join(template_out_dir, f"rendered_template-{pid}.py.out"), "w"
        ) as f:
            f.write(template)
    return template


def snapshot_diff(cur_items, snapshot_file):
    """
    Attempts to compare like PIDs. If like PIDS can't be found it will just compare
    the first PID listed to the first PID in the file. Any unmatched or non-first
    PIDs will be ignored because we don't know what to compare them to.
    """
    try:
        prev_items = list(frontend_utils.get_pages(snapshot_file))
    except pickle.UnpicklingError as e:
        frontend_utils.echo_error(
            f"Error unpickling the data from {snapshot_file}: {e}"
        )
        return None

    differences = []
    for cur_item in cur_items:
        for prev_item in prev_items:
            if cur_item.pid == prev_item.pid:
                diff = summary.get_diff(cur_item.data, prev_item.data)
                differences.append(
                    RetrievedObjects(
                        pid=cur_item.pid,
                        title=f"Snapshot Differences for {cur_item.pid}",
                        data=diff,
                    )
                )
    if not differences:
        diff = summary.get_diff(cur_items[0].data, prev_items[0].data)
        differences.append(
            RetrievedObjects(pid=0, title=f"Snapshot Differences", data=diff)
        )
    return differences
