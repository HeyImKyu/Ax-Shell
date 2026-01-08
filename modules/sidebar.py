from fabric.core.fabricator import Fabricator
from fabric.widgets.box import Box
from fabric.widgets.label import Label
from fabric.widgets.datetime import DateTime
from fabric.widgets.centerbox import CenterBox
from fabric.widgets.button import Button
from fabric.widgets.scale import Scale
from fabric.widgets.circularprogressbar import CircularProgressBar
from fabric.widgets.revealer import Revealer
from fabric.widgets.wayland import WaylandWindow as Window
from fabric.hyprland.widgets import Workspaces, WorkspaceButton
from fabric.utils.helpers import exec_shell_command_async
from gi.repository import Gdk, GLib
from modules.systemtray import SystemTray
import modules.icons as icons
from services.download import AriaProvider

class SideBar(Window):
    def __init__(self, **kwargs):
        super().__init__(
            name="bar",
            layer="top",
            anchor="top left bottom",
            margin="6px -24px -8px -8px",
            exclusivity="auto",
            visible=True,
            all_visible=True,
        )
        self.main_bar = kwargs.get("main_bar", None)

        # self.aria_provider = AriaProvider()

        self.workspaces = Workspaces(
            name="workspaces",
            invert_scroll=True,
            empty_scroll=True,
            v_align="fill",
            orientation="v",
            spacing=10,
            buttons=[WorkspaceButton(id=i, label="") for i in range(1, 11)],
        )

        self.vpn_button = Button(
            name="vpn-button",
            style_classes=["button-sidebar"],
            on_clicked=lambda *_: self.switch_vpn(),
            child=Label(
                name="vpn-button-label",
                style_classes=["button-sidebar-label"],
                markup=icons.vpn
            )
        )
        self.vpn_button.connect("enter_notify_event", self.on_button_enter)
        self.vpn_button.connect("leave_notify_event", self.on_button_leave)

        self.downloads_label = Label(
            name="downloads-button-label",
            style_classes=["button-sidebar-label"],
            markup=icons.downloads,
        )

        self.downloads_circle = CircularProgressBar(
            name="downloads-circle",
            value=0.0,
            size=28,
            line_width=2,
            start_angle=150,
            end_angle=390,
            child=self.downloads_label
        )

        # i honestly have no idea what these all do
        # if someone stumbles across this and can tell me which ones i can leave out, please do
        # self.downloads_fabricator = Fabricator(
        #     poll_from=lambda v: self.aria_provider.fetch_from_aria(),
        #     on_changed=lambda f, v: self.update_downloads_circle,
        #     interval=3000,
        #     stream=False,
        #     default_value=0
        # )
        # self.downloads_fabricator.changed.connect(self.update_downloads_circle)
        # GLib.idle_add(self.update_downloads_circle, None, self.aria_provider.progress)


        self.downloads_button = Button(
            name="downloads-button",
            style_classes=["button-sidebar"],
            on_clicked=lambda *_: self.open_aria(),
            child=self.downloads_circle
        )
        
        self.downloads_button.connect("enter_notify_event", self.on_button_enter)
        self.downloads_button.connect("leave_notify_event", self.on_button_leave)

        self.bar_inner = CenterBox(
            name="sidebar-inner",
            orientation="v",
            h_align="center",
            v_align="fill",
            start_children=Box(
                name="start-container",
                spacing=4,
                orientation="v",
                children=[
                    Box(name="workspaces-container", children=[self.workspaces]),
                ]
            ),
            center_childern=Box(
                name="center-container",
                spacing=4,
                orientation="v",
            ),
            end_children=Box(
                name="end-container",
                spacing=4,
                orientation="v",
                children=[
                    self.vpn_button,
                    self.downloads_button,
                ],
            ),
        )

        self.children = self.bar_inner

        self.hidden = False

    def on_button_enter(self, widget, event):
        window = widget.get_window()
        if window:
            window.set_cursor(Gdk.Cursor(Gdk.CursorType.HAND2))

    def on_button_leave(self, widget, event):
        window = widget.get_window()
        if window:
            window.set_cursor(None)

    def tools_menu(self):
        self.notch.open_notch("tools")

    def toggle_hidden(self):
        self.hidden = not self.hidden
        if self.hidden:
            self.bar_inner.add_style_class("hidden")
        else:
            self.bar_inner.remove_style_class("hidden")

    def switch_vpn(self):
        # should still be converted to python code
        self.main_bar.vpn_status.vpn_provider.cycle_wireguard_vpn()
        self.main_bar.vpn_status.update_button()
        

    def open_aria(self):
        exec_shell_command_async("xdg-open http://localhost:6801/")


    def update_downloads_circle(self, sender, data):
        if (data == 0):
            self.downloads_circle.add_style_class("hidden")
        else:
            self.downloads_circle.remove_style_class("hidden")
            
        self.downloads_circle.set_value(data/100.0)
