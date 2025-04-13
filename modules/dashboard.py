import os
import random
from fabric.utils import get_relative_path
from fabric.widgets.box import Box
from fabric.widgets.centerbox import CenterBox
from fabric.widgets.label import Label
from fabric.widgets.button import Button
from fabric.widgets.stack import Stack
from fabric.widgets.image import Image
import gi
gi.require_version('Gtk', '3.0')
gi.require_version('GdkPixbuf', '2.0')
from gi.repository import GLib, Gtk, Pango, GdkPixbuf
import modules.icons as icons
from modules.buttons import Buttons
from modules.widgets import Widgets
from modules.wallpapers import WallpaperSelector
from modules.kanban import Kanban
import config.data as data

class Dashboard(Box):
    def __init__(self, **kwargs):
        super().__init__(
            name="dashboard",
            orientation="v",
            spacing=8,
            h_align="fill",
            v_align="fill",
            h_expand=True,
            visible=True,
            all_visible=True,
        )

        self.notch = kwargs["notch"]
        self.notif_win = kwargs["notif_win"]

        self.widgets = Widgets(notif_win=self.notif_win)
        self.kanban = Kanban()
        self.wallpapers = WallpaperSelector()
        self.visible_child = self.widgets #only for reading rn

        self.stack = Stack(
            name="stack",
            transition_type="slide-left-right",
            transition_duration=500,
        )

        self.switcher = Gtk.StackSwitcher(
            name="switcher",
            spacing=8,
        )

        self.label_1 = Label(
            name="label-1",
            label="Widgets",
        )

        self.label_3 = Label(
            name="label-3",
            label="Kanban",
        )

        self.label_4 = Label(
            name="label-4",
            label="Wallpapers",
        )

        self.stack.add_titled(self.widgets, "widgets", "Widgets")
        self.stack.add_titled(self.kanban, "kanban", "Kanban")
        self.stack.add_titled(self.wallpapers, "wallpapers", "Wallpapers")

        self.switcher.set_stack(self.stack)
        self.switcher.set_hexpand(True)
        self.switcher.set_homogeneous(True)
        self.switcher.set_can_focus(True)
        
        # Add signal to detect when the visible child changes
        self.stack.connect("notify::visible-child", self.on_visible_child_changed)

        self.add(self.switcher)
        self.add(self.stack)

        self.show_all()

    def go_to_next_child(self):
        children = self.stack.get_children()
        current_index = self.get_current_index(children)
        next_index = (current_index + 1) % len(children)
        self.stack.set_visible_child(children[next_index])

    def go_to_previous_child(self):
        children = self.stack.get_children()
        current_index = self.get_current_index(children)
        previous_index = (current_index - 1 + len(children)) % len(children)
        self.stack.set_visible_child(children[previous_index])

    def get_current_index(self, children):
        current_child = self.stack.get_visible_child()
        return children.index(current_child) if current_child in children else -1

    def on_visible_child_changed(self, stack, param):
        visible = stack.get_visible_child()
        self.visible_child = visible
        if visible == self.wallpapers:
            self.wallpapers.search_entry.set_text("")
            self.wallpapers.search_entry.grab_focus()

    def go_to_section(self, section_name):
        """Navigate to a specific section in the dashboard."""
        if section_name == "widgets":
            self.stack.set_visible_child(self.widgets)
        elif section_name == "pins":
            self.stack.set_visible_child(self.pins)
        elif section_name == "kanban":
            self.stack.set_visible_child(self.kanban)
        elif section_name == "wallpapers":
            self.stack.set_visible_child(self.wallpapers)
        elif section_name == "coming-soon":
            self.stack.set_visible_child(self.coming_soon)
