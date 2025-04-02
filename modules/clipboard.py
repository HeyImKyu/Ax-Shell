import operator
from collections.abc import Iterator
from fabric.widgets.box import Box
from fabric.widgets.label import Label
from fabric.widgets.button import Button
from fabric.widgets.entry import Entry
from fabric.widgets.scrolledwindow import ScrolledWindow
from fabric.utils import idle_add, remove_handler, exec_shell_command_async
from gi.repository import GLib, Gdk
import modules.icons as icons
from config.data import CLIPBOARD_FILE
import os
import subprocess
from thefuzz import fuzz
from config.data import FUZZY_THRESHOLD
import sqlite3
import chardet

class Clipboard(Box):
    def __init__(self, **kwargs):
        super().__init__(
            name="clipboard",
            visible=False,
            all_visible=False,
            **kwargs,
        )

        self.notch = kwargs["notch"]
        self.selected_index = -1  # Track the selected item index

        self._arranger_handler: int = 0
        self._sorted_filtered_clipboard_entries = []

        self.viewport = Box(name="viewport", spacing=4, orientation="v")
        self.search_entry = Entry(
            name="search-entry",
            placeholder="Search Clipboard...",
            h_expand=True,
            notify_text=lambda entry, *_: self.arrange_viewport(entry.get_text()),
            on_activate=lambda entry, *_: self.on_search_entry_activate(entry.get_text()),
            on_key_press_event=self.on_search_entry_key_press,  # Handle key presses
        )
        self.search_entry.props.xalign = 0.5
        self.scrolled_window = ScrolledWindow(
            name="scrolled-window",
            spacing=10,
            min_content_size=(450, 105),
            max_content_size=(450, 705),
            child=self.viewport,
        )

        self.header_box = Box(
            name="header_box",
            spacing=10,
            orientation="h",
            children=[
                Button(
                    name="clear-clipboard-history-button",
                    child=Label(name="clear-clipboard-label", markup=icons.trash),
                    on_clicked=lambda *_: self.clear_clipboard_database(),
                ),
                self.search_entry,
                Button(
                    name="close-button",
                    child=Label(name="close-label", markup=icons.cancel),
                    tooltip_text="Exit",
                    on_clicked=lambda *_: self.close_clipboard()
                ),
            ],
        )

        self.launcher_box = Box(
            name="launcher-box",
            spacing=10,
            h_expand=True,
            orientation="v",
            children=[
                self.header_box,
                self.scrolled_window,
            ],
        )

        self.resize_viewport()

        self.add(self.launcher_box)
        self.show_all()

    def get_clipboard_history(self):
        self.create_db_if_not_exists(CLIPBOARD_FILE)

        conn = sqlite3.connect(CLIPBOARD_FILE)
        cursor = conn.cursor()
        cursor.execute('''SELECT id, contents FROM c ORDER BY id DESC LIMIT 20''')

        rtn = []
        for _ in range(20):
            try:
                output = cursor.fetchone()
                if output is None:
                    # no entries left
                    break
                rtn.append((output[0], output[1]))
            except:
                print(f"Skipping invalid UTF-8 entry")

        conn.close()

        return rtn

    def close_clipboard(self):
        self.viewport.children = []
        self.selected_index = -1  # Reset selection
        self.notch.force_close_notch()

    def open_clipboard(self):
        self.arrange_viewport()

    def arrange_viewport(self, query: str = ""):
        # remove_handler(self._arranger_handler) if self._arranger_handler else None
        self._all_clipboard_entries = self.get_clipboard_history()
        self.viewport.children = []
        self.selected_index = -1 # Clear selection when viewport changes
        
        filtered_sorted = sorted (
                [ # list comprehension to filter out mismatching entries # da wollen wir keine liste, sondern ein dict also {} ^^ right? i think so 
                (key, value)
                for key, value in self._all_clipboard_entries
                if fuzz.partial_ratio(
                    query.casefold(), value.casefold()
                ) >= FUZZY_THRESHOLD or query == ""
            ],
            key=lambda e: -(e[0])
        )
        
        self._sorted_filtered_clipboard_entries = filtered_sorted        
        filtered_entries_iter = iter(filtered_sorted)

        should_resize = operator.length_hint(filtered_entries_iter) == len(self._all_clipboard_entries)

        self._arranger_handler = idle_add(
            lambda clipboard_iter: self.add_next_clipboard_entry(clipboard_iter) or self.handle_arrange_complete(should_resize, query),
            filtered_entries_iter,
            pin=True,
        )

    def handle_arrange_complete(self, should_resize, query):
        if should_resize:
            self.resize_viewport()
        # Only auto-select first item if query exists
        if query.strip() != "" and self.viewport.get_children():
            self.update_selection(0)
        return False

    def add_next_clipboard_entry(self, entries_iter: Iterator[(str, str)]):
        if not (entry := next(entries_iter, None)):
            return False
        self.viewport.add(self.bake_clipboard_entry_slot(entry))
        return True

    def resize_viewport(self):
        self.scrolled_window.set_min_content_width(
            self.viewport.get_allocation().width  # type: ignore
        )
        return False

    def bake_clipboard_entry_slot(self, entry: tuple[str, str], **kwargs) -> Button:
        button = Button(
            name="clipboard-entry-slot-button",
            child=Box(
                name="clipboard-entry-slot-box",
                orientation="h",
                spacing=10,
                children=[
                    Label(
                        name="clipboard-entry-label",
                        label=entry[1] or "Unknown",
                        ellipsization="end",
                        v_align="center",
                        h_align="center",
                    ),
                ],
            ),
            on_clicked=lambda *_: self.copy_or_rightclick(entry, None, None),
            **kwargs,
        )
        button.connect(
            "button-press-event",
            lambda button, event: self.copy_or_rightclick(entry, button, event)
        )
        return button

    def copy_or_rightclick(self, entry, button, event):
        if event == None or event.button == Gdk.BUTTON_PRIMARY:
            self.copy_text_to_clipboard(entry[1])
            self.close_clipboard()
            # self.update_db_order(entry.name)
        elif event.button == Gdk.BUTTON_SECONDARY:
            self.delete_from_history(entry[0])

    def update_selection(self, new_index: int):
        # Unselect current
        if self.selected_index != -1 and self.selected_index < len(self.viewport.get_children()):
            current_button = self.viewport.get_children()[self.selected_index]
            current_button.get_style_context().remove_class("selected")
        # Select new
        if new_index != -1 and new_index < len(self.viewport.get_children()):
            new_button = self.viewport.get_children()[new_index]
            new_button.get_style_context().add_class("selected")
            self.selected_index = new_index
            self.scroll_to_selected(new_button)
        else:
            self.selected_index = -1

    def scroll_to_selected(self, button):
        def scroll():
            adj = self.scrolled_window.get_vadjustment()
            alloc = button.get_allocation()
            if alloc.height == 0:
                return False  # Retry if allocation isn't ready

            y = alloc.y
            height = alloc.height
            page_size = adj.get_page_size()
            current_value = adj.get_value()

            # Calculate visible boundaries
            visible_top = current_value
            visible_bottom = current_value + page_size

            if y < visible_top:
                # Item above viewport - align to top
                adj.set_value(y)
            elif y + height > visible_bottom:
                # Item below viewport - align to bottom
                new_value = y + height - page_size
                adj.set_value(new_value)
            # No action if already fully visible
            return False
        GLib.idle_add(scroll)

    def on_search_entry_activate(self, text):
        children = self.viewport.get_children()
        if children:
            # Only activate if we have selection or non-empty query
            if text.strip() == "" and self.selected_index == -1:
                return  # Prevent accidental activation when empty
            selected_index = self.selected_index if self.selected_index != -1 else 0
            if 0 <= selected_index < len(children):
                children[selected_index].clicked()

    def delete_selected_from_history(self):
        selected_entry_id = self._sorted_filtered_clipboard_entries[self.selected_index][0]
        self.delete_from_history(selected_entry_id)

    def on_search_entry_key_press(self, widget, event):
        if self.selected_index != -1: # only if something is selected can we copy/delete it
            # if key is shift+delete, then delete entry from db
            if event.keyval == Gdk.KEY_Delete and (event.state & Gdk.ModifierType.SHIFT_MASK):
                self.delete_selected_from_history()
                return True

        # navigation
        if event.keyval == Gdk.KEY_Down:
            self.move_selection(1)
            return True
        elif event.keyval == Gdk.KEY_Up:
            self.move_selection(-1)
            return True
        elif event.keyval == Gdk.KEY_Escape:
            self.close_clipboard()
            return True
        return False

    def move_selection(self, delta: int):
        children = self.viewport.get_children()
        if not children:
            return
        # Allow starting selection from nothing when empty
        if self.selected_index == -1 and delta == 1:
            new_index = 0
        else:
            new_index = self.selected_index + delta
        new_index = max(0, min(new_index, len(children) - 1))
        self.update_selection(new_index)

    def copy_text_to_clipboard(self, text: str):
        try:
            subprocess.run(["wl-copy"], input=text.encode(), check=True)
        except subprocess.CalledProcessError as e:
            print(f"Clipboard copy failed: {e}")

    def create_db_if_not_exists(self, db_path):
        if not os.path.exists(db_path):
            subprocess.call(['touch', db_path])
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute('''CREATE TABLE IF NOT EXISTS c
                (id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT, contents text)''')
            conn.commit()
            conn.close()

    def delete_from_history(self, entry_id):
        conn = sqlite3.connect(CLIPBOARD_FILE)
        cursor = conn.cursor()

        cursor.execute('''DELETE FROM c WHERE id = ?''', (entry_id,))

        conn.commit()
        conn.close()

        self.arrange_viewport(self.search_entry.get_text())

    def clear_clipboard_database(self):
        conn = sqlite3.connect(CLIPBOARD_FILE)
        cursor = conn.cursor()

        cursor.execute('''DELETE FROM c''')

        conn.commit()
        conn.close()

        self.arrange_viewport(self.search_entry.get_text())
