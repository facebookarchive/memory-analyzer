#!/usr/bin/env python3
# Copyright (c) Facebook, Inc. and its affiliates.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

import curses
import os
import pickle
import subprocess

import click
import prettytable

from . import memanz_curses


def readable_size(i, snapshot=False):
    """
    Pretty-print the integer `i` as a human-readable size representation.
    """
    degree = 0
    while i > 1024:
        i = i / float(1024)
        degree += 1
    scales = ["B", "KB", "MB", "GB", "TB", "EB"]
    if snapshot:
        return f"{i:+.2f}{scales[degree]:>5}"
    return f"{i:.2f}{scales[degree]:>5}"


def init_table(references, snapshot):
    pt = prettytable.PrettyTable()
    field_names = ["Object", "Count", "Size"]
    if references:
        field_names.extend(["References", "Backwards References"])
    if snapshot:
        field_names[1] += " Diff"
        field_names[2] += " Diff"
    pt.field_names = field_names
    pt.align["Object"] = "l"
    pt.align[pt.field_names[1]] = "r"
    pt.align[pt.field_names[2]] = "r"
    return pt


def format_summary_output(page):
    """
    Formats in prettytable style the pympler summary.
    """
    references = False
    items = page.data
    if not items:
        items = [[f"No data to display for pid {page.pid}.", 0, 0]]
    if any(len(item) == 5 for item in items):
        references = True
    snapshot = "Snapshot Differences" in page.title
    pt = init_table(references, snapshot)
    items.sort(key=lambda x: x[2], reverse=True)
    for sublist in items:
        if snapshot:
            sublist[1] = f"{sublist[1]:+}"
        sublist[2] = readable_size(sublist[2], snapshot)
        if len(sublist) != len(pt.field_names):
            # Fill in missing data with "".
            sublist.extend(["" for _ in range(len(pt.field_names) - len(sublist))])
        pt.add_row(sublist)
    return pt


def table_as_list_of_strings(table):
    string_table = table.get_string()
    return string_table.split("\n")


def get_pages(filename):
    """
    Read each pickled object in the given file as a page.
    The objects will be lists of lists.
    """
    with open(filename, "rb") as fd:
        while True:
            try:
                yield pickle.load(fd)
            except EOFError:
                break
            except pickle.UnpicklingError:
                raise


def view(stdscr, pages):
    """
    Format the data in a list of pretty tables that will be the pages of the
    curses UI, then activate the nCurses UI.
    """
    pages_as_tables = []
    titles = []
    for page in pages:
        titles.append(page.title)
        table = format_summary_output(page)
        pages_as_tables.append(table_as_list_of_strings(table))
    if pages_as_tables:
        win = memanz_curses.Window(stdscr, pages_as_tables, titles)
        win.run()


def initiate_curses(items):
    curses.wrapper(view, items)


def echo_error(msg, *args, **kwargs):
    click.echo(click.style(f"ERROR: {msg}", fg="red"), *args, **kwargs)


def echo_info(msg, *args, **kwargs):
    click.echo(click.style(f"{msg}", fg="green"), *args, **kwargs)
