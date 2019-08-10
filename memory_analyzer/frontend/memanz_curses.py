#!/usr/bin/env python3
# Copyright (c) Facebook, Inc. and its affiliates.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

"""
This can either be run standalone with an already generated file (so the user
does not have to run the memory analyzer multiple times), or it can be launched
directly by the memory analyzer.
"""

import curses
from collections import namedtuple

UP_KEYS = [curses.KEY_UP, ord("w"), ord("k"), ord("H"), curses.KEY_PPAGE]
DOWN_KEYS = [curses.KEY_DOWN, ord("s"), ord("j"), ord("G"), curses.KEY_NPAGE]
RIGHT_KEYS = [curses.KEY_RIGHT, ord("d"), ord("l")]
LEFT_KEYS = [curses.KEY_LEFT, ord("a"), ord("h")]


class Window:
    UP = -1
    DOWN = 1

    def __init__(self, stdscr, pages, titles):
        self.top = 0
        self.position = self.top
        self.pages = pages
        self.page_titles = titles
        self.cur_page = 0
        self.window = stdscr
        self.height = curses.LINES - 1
        self.width = curses.COLS - 1
        self.bottom = len(self.cur_page.items)
        curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_WHITE)

    @property
    def cur_page(self):
        return self._cur_page

    @cur_page.setter
    def cur_page(self, pos):
        page = namedtuple("Page", "pos items title")
        self._cur_page = page(
            pos=pos, items=self.pages[pos], title=self.page_titles[pos]
        )
        return self._cur_page

    def status_bar_render(self):
        statusbarstr = (
            f"{self.cur_page.title} | Navigate with arrows or wasd | Press 'q' to exit"
        )
        self.window.attron(curses.color_pair(1))
        self.window.addstr(self.height, 0, statusbarstr)
        self.window.addstr(
            self.height, len(statusbarstr), " " * (self.width - len(statusbarstr))
        )
        self.window.attroff(curses.color_pair(1))

    def run(self):
        self.display()
        self.user_input()

    def display(self):
        self.window.erase()
        for idx, item in enumerate(
            self.cur_page.items[self.position : self.position + self.height - 1]
        ):
            self.window.addstr(idx, 0, item)
        self.status_bar_render()
        self.window.refresh()

    def scroll_up(self, user_select):
        if (
            user_select in [curses.KEY_UP, ord("w"), ord("k")]
            and self.position != self.top
        ):
            self.position += self.UP
        elif user_select == ord("H") and self.position != self.top:
            self.position = self.top
        elif user_select == curses.KEY_PPAGE and self.position != self.top:
            if self.position - self.height > self.top:
                self.position = self.position - self.height
            else:
                self.position = self.top

    def scroll_down(self, user_select):
        if (
            user_select in [curses.KEY_DOWN, ord("s"), ord("j")]
            and self.position + self.height <= self.bottom
        ):
            self.position += self.DOWN
        elif user_select == ord("G") and self.position + self.height != self.bottom:
            self.position = self.bottom - self.height + 1
        elif user_select == curses.KEY_NPAGE:
            if self.position + self.height < self.bottom - self.height:
                self.position = self.position + self.height
            else:
                self.position = self.bottom - self.height + 1

    def scroll_right(self, user_select):
        if len(self.pages) != self.cur_page.pos + 1:
            self.cur_page = self.cur_page.pos + 1
            self.bottom = len(self.cur_page.items)

    def scroll_left(self, user_select):
        if self.cur_page.pos != 0:
            self.cur_page = self.cur_page.pos - 1
            self.bottom = len(self.cur_page.items)

    def user_input(self):
        user_select = self.window.getch()
        while user_select != ord("q"):
            self.status_bar_render()
            if self.bottom > self.height:
                if user_select in UP_KEYS:
                    self.scroll_up(user_select)
                elif user_select in DOWN_KEYS:
                    self.scroll_down(user_select)
            if user_select in RIGHT_KEYS:
                self.scroll_right(user_select)
            elif user_select in LEFT_KEYS:
                self.scroll_left(user_select)

            self.display()
            user_select = self.window.getch()
