#!/usr/bin/env python3
# Copyright (c) Facebook, Inc. and its affiliates.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

import curses
from unittest import TestCase, mock

from ..frontend import memanz_curses


class MemanzCursesTest(TestCase):
    def setUp(self):
        self.mock_curses = mock.patch(
            "memory_analyzer.frontend.memanz_curses.curses"
        ).start()
        self.addCleanup(self.mock_curses.stop)
        self.mock_curses.LINES = 2
        self.mock_curses.COLS = 100
        self.mock_curses.KEY_DOWN = curses.KEY_DOWN
        self.mock_curses.KEY_UP = curses.KEY_UP
        self.mock_curses.KEY_PPAGE = curses.KEY_PPAGE
        self.mock_curses.KEY_NPAGE = curses.KEY_NPAGE
        self.mock_curses.KEY_RIGHT = curses.KEY_RIGHT
        self.mock_curses.KEY_LEFT = curses.KEY_LEFT
        self.statusbarstr = " | Navigate with arrows or wasd | Press 'q' to exit"
        self.pages = [["Page1", 10, 1024], ["Page2", 90, 100]]
        self.titles = ["Analysis of 1234", "Snapshot Differences"]
        self.win = memanz_curses.Window(self.mock_curses, self.pages, self.titles)

    def test_status_bar_render(self):
        self.win.status_bar_render()

    def test_user_input_scroll_up_and_down_wasd(self):
        self.win.window.getch.side_effect = [ord("s"), ord("q")]
        self.win.user_input()
        self.assertEqual(self.win.position, 1)
        self.win.window.getch.side_effect = [ord("w"), ord("q")]
        self.win.user_input()
        self.assertEqual(self.win.position, 0)

    def test_user_input_scroll_up_and_down_hjkl(self):
        self.win.window.getch.side_effect = [ord("j"), ord("q")]
        self.win.user_input()
        self.assertEqual(self.win.position, 1)
        self.win.window.getch.side_effect = [ord("k"), ord("q")]
        self.win.user_input()
        self.assertEqual(self.win.position, 0)

    def test_user_input_scroll_up_and_down_arrows(self):
        self.win.window.getch.side_effect = [self.mock_curses.KEY_DOWN, ord("q")]
        self.win.user_input()
        self.assertEqual(self.win.position, 1)
        self.win.window.getch.side_effect = [self.mock_curses.KEY_UP, ord("q")]
        self.win.user_input()
        self.assertEqual(self.win.position, 0)

    def test_user_input_attempt_to_scroll_up_off_window(self):
        self.assertEqual(self.win.position, 0)
        self.win.window.getch.side_effect = [self.mock_curses.KEY_UP, ord("q")]
        self.win.user_input()
        self.assertEqual(self.win.position, 0)
        self.win.window.getch.side_effect = [self.mock_curses.KEY_PPAGE, ord("q")]
        self.win.user_input()
        self.assertEqual(self.win.position, 0)

    def test_user_input_attempt_to_scroll_down_off_window(self):
        self.win.position = self.win.bottom
        self.win.window.getch.side_effect = [self.mock_curses.KEY_DOWN, ord("q")]
        self.win.user_input()
        self.assertEqual(self.win.position, self.win.bottom)
        self.win.window.getch.side_effect = [self.mock_curses.KEY_NPAGE, ord("q")]
        self.win.user_input()
        self.assertEqual(self.win.position, self.win.bottom)

    def test_page_left_and_right_arrows(self):
        self.win.window.getch.side_effect = [self.mock_curses.KEY_RIGHT, ord("q")]
        self.win.user_input()
        self.assertEqual(self.win.cur_page.pos, 1)
        self.assertEqual(self.win.cur_page.items, self.pages[1])
        self.win.window.getch.side_effect = [self.mock_curses.KEY_LEFT, ord("q")]
        self.win.user_input()
        self.assertEqual(self.win.cur_page.pos, 0)
        self.assertEqual(self.win.cur_page.items, self.pages[0])

    def test_page_left_and_right_wasd(self):
        self.win.window.getch.side_effect = [ord("d"), ord("q")]
        self.win.user_input()
        self.assertEqual(self.win.cur_page.pos, 1)
        self.assertEqual(self.win.cur_page.items, self.pages[1])
        self.win.window.getch.side_effect = [ord("a"), ord("q")]
        self.win.user_input()
        self.assertEqual(self.win.cur_page.pos, 0)
        self.assertEqual(self.win.cur_page.items, self.pages[0])

    def test_page_left_and_right_hjkl(self):
        self.win.window.getch.side_effect = [ord("l"), ord("q")]
        self.win.user_input()
        self.assertEqual(self.win.cur_page.pos, 1)
        self.assertEqual(self.win.cur_page.items, self.pages[1])
        self.win.window.getch.side_effect = [ord("h"), ord("q")]
        self.win.user_input()
        self.assertEqual(self.win.cur_page.pos, 0)
        self.assertEqual(self.win.cur_page.items, self.pages[0])

    def test_display_normal(self):
        self.mock_curses.LINES = 10
        win = memanz_curses.Window(self.mock_curses, self.pages, self.titles)
        win.position = 1
        win.display()
        win.window.addstr.assert_any_call(0, 0, 10)
        win.window.addstr.assert_any_call(1, 0, 1024)
        win.window.addstr.assert_any_call(9, 0, self.titles[0] + self.statusbarstr)

    def test_display_window_too_small_for_display(self):
        self.win.position = 1
        self.win.display()
        calls = [
            mock.call(
                self.mock_curses.LINES - 1, 0, self.titles[0] + self.statusbarstr
            ),
            mock.call(
                self.mock_curses.LINES - 1,
                len(self.titles[0] + self.statusbarstr),
                " "
                * (self.mock_curses.COLS - 1 - len(self.titles[0] + self.statusbarstr)),
            ),
        ]
        self.win.window.addstr.assert_has_calls(calls)

    def test_display_window_size_zero(self):
        self.mock_curses.LINES = 0
        win = memanz_curses.Window(self.mock_curses, self.pages, self.titles)
        win.position = 1
        win.display()
        win.window.addstr.assert_any_call(0, 0, 10)
        win.window.addstr.assert_any_call(-1, 0, self.titles[0] + self.statusbarstr)

    def test_set_cur_page(self):
        self.assertEqual(self.win.cur_page.items, self.pages[0])
        self.assertEqual(self.win.cur_page.pos, 0)
        self.win.cur_page = 1
        self.assertEqual(self.win.cur_page.items, self.pages[1])
        self.assertEqual(self.win.cur_page.pos, 1)

    def test_display_snapshot_page(self):
        self.mock_curses.LINES = 10
        win = memanz_curses.Window(self.mock_curses, self.pages, self.titles)
        win.cur_page = 1
        self.assertEqual(["Page2", 90, 100], win.cur_page.items)
        win.display()
        win.window.addstr.assert_any_call(0, 0, "Page2")
        win.window.addstr.assert_any_call(1, 0, 90)
        win.window.addstr.assert_any_call(2, 0, 100)
        win.window.addstr.assert_any_call(
            9, 0, "Snapshot Differences" + self.statusbarstr
        )
