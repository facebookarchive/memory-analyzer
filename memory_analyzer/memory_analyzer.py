#!/usr/bin/env python3
# Copyright (c) Facebook, Inc. and its affiliates.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

import errno
import os
import pickle
import sys
import tempfile
from datetime import datetime
from functools import partial
from multiprocessing.pool import ThreadPool

import click
import pkg_resources

from . import analysis_utils
from .frontend import frontend_utils


def analyze_memory_launcher(
    pid, num_refs, specific_refs, debug, output_file, executable, template_out_path
):
    templates_path = (
        pkg_resources.resource_filename("memory_analyzer", "templates") + "/"
    )
    cur_path = os.path.dirname(__file__) + "/"  # not zip safe, for now
    gdb_obj = analysis_utils.GDBObject(pid, cur_path, executable, template_out_path)
    analysis_utils.render_template(
        f"analysis.py.template",
        templates_path,
        num_refs,
        pid,
        specific_refs,
        output_file,
        template_out_path,
    )
    return gdb_obj.run_analysis(debug)


def write_to_output_file(filename, items):
    with open(filename, "wb+") as outputf:
        for item in items:
            bytes_item = pickle.dumps(item)
            outputf.write(bytes_item)


def is_root():
    if os.geteuid() == 0:
        return True
    return False


def validate_pids(ctx, param, pids):
    for pid in pids:
        pid = int(pid)
        try:
            os.kill(pid, 0)
        except OSError as e:
            if e.errno == errno.EPERM and not is_root():
                msg = "Permission error, try running as root"
                raise click.UsageError(msg)

            msg = f"The given PID {pid} is not valid."
            raise click.BadParameter(msg)

    return pids


def check_positive_int(ctx, param, i):
    i = int(i)
    if i >= 0:
        return i
    msg = "The number of references cannot be negative."
    raise click.BadParameter(msg)


@click.group()
def cli():
    pass


@cli.command()
@click.argument("filename", type=click.Path(exists=True))
def view(filename):
    """
    Tool for viewing the output of the memory analyzer. Launches a UI.

    Argument:

        FILENAME: The filename of the snapshot to view.
    """
    try:
        pages = frontend_utils.get_pages(filename)
    except pickle.UnpicklingError as e:
        frontend_utils.echo_error(f"Error unpickling the data from {filename}: {e}")
        sys.exit(1)
    frontend_utils.initiate_curses(pages)


@cli.command()
@click.argument("pids", callback=validate_pids, nargs=-1)
@click.option(
    "-s",
    "--show-references",
    "num_refs",
    default=0,
    callback=check_positive_int,
    help="Shows the references of the X most common objects.\n\
    This is a costly operation, do not use a large number.",
)
@click.option(
    "-ss",
    "--show-specific-references",
    "specific_refs",
    multiple=True,
    default=[],
    help="Shows the references of all objects given.\n\
    This is a costly operation, be careful.",
)
@click.option(
    "--snapshot",
    type=click.Path(exists=True),
    help="The file containing snapshot information of previous run.",
)
@click.option(
    "-q",
    "--quiet",
    "quiet",
    is_flag=True,
    default=False,
    help="Don't enter UI after evaluation.",
)
@click.option(
    "-d",
    "--debug",
    "debug",
    is_flag=True,
    default=False,
    help="Show GDB output, for debugging the analyzer.",
)
@click.option("-f", "--output-file", type=str, help="File to output results to.")
@click.option(
    "--no-upload",
    is_flag=True,
    default=False,
    help="Do not upload reference graphs to phabricator.",
)
@click.option(
    "-e",
    "--exec",
    "executable",
    help="Python executable to use",
    default=f"{sys.executable}-dbg",
)
def run(
    pids,
    num_refs,
    specific_refs,
    snapshot,
    quiet,
    debug,
    output_file,
    no_upload,
    executable,
):
    """
    Tool for providing memory analysis on a running Python3 process.

    Argument:

        PIDS: The pid or list of pids of the running Python 3 process(es) to evaluate.


    Output:

        A binary file of the results. By default, after run completes the user
        will enter a UI for navigating the data. If references are set, png
        files will also be created and uploaded to phabricator.


        Unless otherwise set, the output files will reside in memory_analyzer_out/,
        which is created where the service is ran.
    """
    runtime = "{:%Y%m%d%H%M%S}".format(datetime.now())
    default_filename = f"memory_analyzer_out/memory_analyzer_snapshot-{runtime}"
    if not output_file:
        output_file = default_filename

    references = num_refs > 0 or specific_refs
    retrieved_objs = []
    # Create a folder for output
    if references or output_file == default_filename:
        os.makedirs(os.path.dirname(default_filename), exist_ok=True)
    template_out_path = tempfile.mkdtemp()

    # Make a new thread per PID
    worker_pool = ThreadPool(len(pids))
    target = partial(
        analyze_memory_launcher,
        num_refs=num_refs,
        specific_refs=specific_refs,
        debug=debug,
        output_file=output_file,
        executable=executable,
        template_out_path=template_out_path,
    )

    for result in worker_pool.imap_unordered(target, pids):
        if result.data is None:
            frontend_utils.echo_error(
                f"{result.title} returned no data!  Try rerunning with --debug"
            )
        else:
            retrieved_objs.append(result)
    if not retrieved_objs:
        frontend_utils.echo_error("No results to report")
        sys.exit(1)
    if snapshot:
        diffs = analysis_utils.snapshot_diff(retrieved_objs, snapshot)
        retrieved_objs.extend(diffs)

    frontend_utils.echo_info(f"Writing output to file {output_file}")
    write_to_output_file(output_file, retrieved_objs)
    if not quiet:
        frontend_utils.echo_info("Initializing frontend...")
        frontend_utils.initiate_curses(retrieved_objs)


if __name__ == "__main__":
    cli()
