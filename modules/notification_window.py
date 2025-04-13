from os import truncate
from fabric.widgets.eventbox import EventBox
from fabric.widgets.box import Box
from fabric.widgets.label import Label
from fabric.widgets.centerbox import CenterBox
from fabric.widgets.button import Button
from fabric.widgets.stack import Stack
from fabric.widgets.overlay import Overlay
from fabric.widgets.revealer import Revealer
from fabric.widgets.wayland import WaylandWindow as Window
from fabric.hyprland.widgets import ActiveWindow
from fabric.utils.helpers import FormattedString, truncate
from gi.repository import GLib, Gdk, Gtk, Pango
from modules.launcher import AppLauncher
from modules.dashboard import Dashboard
from modules.notifications import NotificationContainer
from modules.power import PowerMenu
from modules.overview import Overview
from modules.emoji import EmojiPicker
from modules.clipboard import Clipboard
from modules.corners import MyCorner
import modules.icons as icons
import config.data as data
from modules.player import PlayerSmall
from modules.tools import Toolbox


class NotificationWindow(Window):
    def __init__(self, **kwargs):
        super().__init__(
            name="notch",
            layer="overlay",
            anchor="top right",
            keyboard_mode="none",
            exclusivity="normal",
            visible=True,
            all_visible=True,
        )

        # Primero inicializamos NotificationContainer
        self.notification = NotificationContainer(notif_win=self)
        self.notification_history = self.notification.history

        self.notification_revealer = Revealer(
            name="notification-revealer",
            transition_type="slide-down",
            transition_duration=250,
            child_revealed=False,
        )

        self.boxed_notification_revealer = Box(
            name="boxed-notification-revealer",
            orientation="v",
            children=[
                self.notification_revealer,
            ]
        )

        self.add(self.boxed_notification_revealer)
        self.show_all()
