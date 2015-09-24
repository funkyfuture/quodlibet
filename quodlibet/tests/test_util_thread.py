# -*- coding: utf-8 -*-
# Copyright 2015 Christoph Reiter
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation

import threading

from tests import TestCase

from gi.repository import Gtk

from quodlibet.util.thread import call_async, call_async_background, \
    Cancellable, terminate_all


class Tcall_async(TestCase):

    def test_main(self):
        cancel = Cancellable()

        data = []

        def func():
            data.append(threading.current_thread().name)

        def callback(result):
            data.append(threading.current_thread().name)

        call_async(func, cancel, callback)
        Gtk.main_iteration()
        while Gtk.events_pending():
            Gtk.main_iteration()

        call_async_background(func, cancel, callback)
        Gtk.main_iteration()
        while Gtk.events_pending():
            Gtk.main_iteration()

        main_name = threading.current_thread().name
        self.assertEqual(len(data), 4)
        self.assertNotEqual(data[0], main_name)
        self.assertEqual(data[1], main_name)
        self.assertNotEqual(data[2], main_name)
        self.assertEqual(data[3], main_name)

    def test_cancel(self):
        def func():
            assert 0

        def callback(result):
            assert 0

        cancel = Cancellable()
        cancel.cancel()
        call_async(func, cancel, callback)
        Gtk.main_iteration()
        while Gtk.events_pending():
            Gtk.main_iteration()

    def test_terminate_all(self):
        terminate_all()