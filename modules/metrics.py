import psutil
import subprocess
import re
from gi.repository import GLib, Gdk

from fabric.widgets.label import Label
from fabric.widgets.box import Box
from fabric.widgets.scale import Scale
from fabric.widgets.eventbox import EventBox
from fabric.widgets.button import Button
from fabric.widgets.circularprogressbar import CircularProgressBar
from fabric.widgets.overlay import Overlay
from fabric.widgets.revealer import Revealer
from fabric.core.fabricator import Fabricator
from fabric.utils.helpers import exec_shell_command_async

import modules.icons as icons

class MetricsProvider:
    """
    Class responsible for obtaining centralized CPU, memory, and disk usage metrics.
    It updates periodically so that all widgets querying it display the same values.
    """
    def __init__(self):
        self.cpu = 0.0
        self.mem = 0.0
        self.disk = 0.0
        # Updates every 1 second
        GLib.timeout_add_seconds(1, self._update)

    def _update(self):
        # Get non-blocking usage percentages (interval=0)
        # The first call may return 0, but subsequent calls will provide consistent values.
        self.cpu = psutil.cpu_percent(interval=0)
        self.mem = psutil.virtual_memory().percent
        self.disk = psutil.disk_usage("/").percent
        return True

    def get_metrics(self):
        return (self.cpu, self.mem, self.disk)

# Global instance to share data between both widgets.
shared_provider = MetricsProvider()

class BatteryProvider:
    """
    Class responsible for obtaining centralized battery metrics.
    It updates periodically so that all widgets querying it display the same values.
    """
    def __init__(self):
        self.percent = 0.0
        self.charging = None
        self.icon = icons.battery

        # Updates every 1 second
        GLib.timeout_add_seconds(1, self._update)

    def _update(self):
        # The first call may return None, but subsequent calls will provide consistent values.
        battery = psutil.sensors_battery()
        if battery is None:
            self.percent = 0.0
            self.charging = None
            self.icon = icons.battery
        else:
            self.percent = battery.percent
            self.charging = battery.power_plugged

            if self.charging == True:
                self.icon = icons.battery_charging
            elif self.percent >= 90:
                self.icon = icons.battery_4
            elif self.percent >= 50:
                self.icon = icons.battery_3
            elif self.percent >= 30:
                self.icon = icons.battery_2
            elif self.percent >= 10:
                self.icon = icons.battery_1
            elif self.percent < 10:
                self.icon = icons.battery_warning
            else:
                # charging can be None, so this is the fallback
                self.icon = icons.battery_0

        return True

    def get_battery(self):
        return (self.percent, self.charging, self.icon)

# Global instance to share data between both widgets.
shared_battery_provider = BatteryProvider()

class Metrics(Box):
    def __init__(self, **kwargs):
        super().__init__(
            name="metrics",
            spacing=8,
            h_align="center",
            v_align="fill",
            visible=True,
            all_visible=True,
        )

        self.cpu_usage = Scale(
            name="cpu-usage",
            value=0.25,
            orientation='v',
            inverted=True,
            v_align='fill',
            v_expand=True,
        )

        self.cpu_label = Label(
            name="cpu-label",
            markup=icons.cpu,
        )

        self.cpu = Box(
            name="cpu-box",
            orientation='v',
            spacing=8,
            children=[
                self.cpu_usage,
                self.cpu_label,
            ]
        )

        self.ram_usage = Scale(
            name="ram-usage",
            value=0.5,
            orientation='v',
            inverted=True,
            v_align='fill',
            v_expand=True,
        )

        self.ram_label = Label(
            name="ram-label",
            markup=icons.memory,
        )

        self.ram = Box(
            name="ram-box",
            orientation='v',
            spacing=8,
            children=[
                self.ram_usage,
                self.ram_label,
            ]
        )

        self.disk_usage = Scale(
            name="disk-usage",
            value=0.75,
            orientation='v',
            inverted=True,
            v_align='fill',
            v_expand=True,
        )

        self.disk_label = Label(
            name="disk-label",
            markup=icons.disk,
        )

        self.disk = Box(
            name="disk-box",
            orientation='v',
            spacing=8,
            children=[
                self.disk_usage,
                self.disk_label,
            ]
        )

        self.battery_usage = Scale(
            name="battery-usage",
            value=0.75,
            orientation='v',
            inverted=True,
            v_align='fill',
            v_expand=True,
        )

        self.battery_label = Label(
            name="battery-label",
            markup=icons.battery,
        )

        self.battery = Box(
            name="battery-box",
            orientation='v',
            spacing=8,
            children=[
                self.battery_usage,
                self.battery_label,
            ]
        )

        self.scales = [
            self.battery,
            self.disk,
            self.ram,
            self.cpu,
        ]

        self.cpu_usage.set_sensitive(False)
        self.ram_usage.set_sensitive(False)
        self.disk_usage.set_sensitive(False)
        self.battery_usage.set_sensitive(False)

        for x in self.scales:
            self.add(x)

        # Update the widget every second
        GLib.timeout_add_seconds(1, self.update_status)

    def update_status(self):
        # Retrieve centralized data
        cpu, mem, disk = shared_provider.get_metrics()

        # Normalize to 0.0 - 1.0
        self.cpu_usage.value = cpu / 100.0
        self.ram_usage.value = mem / 100.0
        self.disk_usage.value = disk / 100.0

        self.update_battery(None, shared_battery_provider.get_battery())

        return True  # Continue calling this function

    def update_battery(self, sender, battery_data):
        value, charging, icon = battery_data
        if value == 0:
            self.set_visible(False)
        else:
            self.set_visible(True)
            self.battery_usage.value = value / 100.0

        percentage = int(value * 100)
        self.battery_label.set_markup(icon)

        if percentage <= 15:
            self.battery_label.add_style_class("alert")
        else:
            self.battery_label.remove_style_class("alert")

class MetricsSmall(Overlay):
    def __init__(self, **kwargs):
        # Creamos el contenedor principal para los widgets métricos
        main_box = Box(
            name="metrics-small",
            spacing=0,
            orientation="h",
            visible=True,
            all_visible=True,
        )

        # ------------------ CPU ------------------
        self.cpu_icon = Label(name="metrics-icon", markup=icons.cpu)
        self.cpu_circle = CircularProgressBar(
            name="metrics-circle",
            value=0,
            size=28,
            line_width=2,
            start_angle=150,
            end_angle=390,
            style_classes="cpu",
            child=self.cpu_icon,
        )
        self.cpu_level = Label(name="metrics-level", style_classes="cpu", label="0%")
        self.cpu_revealer = Revealer(
            name="metrics-cpu-revealer",
            transition_duration=250,
            transition_type="slide-left",
            child=self.cpu_level,
            child_revealed=False,
        )
        self.cpu_box = Box(
            name="metrics-cpu-box",
            orientation="h",
            spacing=0,
            children=[self.cpu_circle, self.cpu_revealer],
        )
        self.cpu_event_box = EventBox(
            events=["button-press", "enter-notify-event", "leave-notify-event"],
            name="metrics-cpu-button",
            orientation="h",
            spacing=0,
            child=self.cpu_box,
            v_expand=True,
            h_expand=True
        )
        self.cpu_event_box.connect("enter-notify-event", self.on_button_enter)
        self.cpu_event_box.connect("leave-notify-event", self.on_button_leave)
        self.cpu_event_box.connect("button-press-event", lambda *_: print('henlo'))

        # ------------------ RAM ------------------
        self.ram_icon = Label(name="metrics-icon", markup=icons.memory)
        self.ram_circle = CircularProgressBar(
            name="metrics-circle",
            value=0,
            size=28,
            line_width=2,
            start_angle=150,
            end_angle=390,
            style_classes="ram",
            child=self.ram_icon,
        )
        self.ram_level = Label(name="metrics-level", style_classes="ram", label="0%")
        self.ram_revealer = Revealer(
            name="metrics-ram-revealer",
            transition_duration=250,
            transition_type="slide-left",
            child=self.ram_level,
            child_revealed=False,
        )
        self.ram_box = Box(
            name="metrics-ram-box",
            orientation="h",
            spacing=0,
            children=[self.ram_circle, self.ram_revealer],
        )

        # ------------------ Disk ------------------
        self.disk_icon = Label(name="metrics-icon", markup=icons.disk)
        self.disk_circle = CircularProgressBar(
            name="metrics-circle",
            value=0,
            size=28,
            line_width=2,
            start_angle=150,
            end_angle=390,
            style_classes="disk",
            child=self.disk_icon,
        )
        self.disk_level = Label(name="metrics-level", style_classes="disk", label="0%")
        self.disk_revealer = Revealer(
            name="metrics-disk-revealer",
            transition_duration=250,
            transition_type="slide-left",
            child=self.disk_level,
            child_revealed=False,
        )
        self.disk_box = Box(
            name="metrics-disk-box",
            orientation="h",
            spacing=0,
            children=[self.disk_circle, self.disk_revealer],
        )

        # Agregamos cada widget métrico al contenedor principal
        main_box.add(self.disk_box)
        main_box.add(Box(name="metrics-sep"))
        main_box.add(self.ram_box)
        main_box.add(Box(name="metrics-sep"))
        main_box.add(self.cpu_event_box)

        # Se crea un único EventBox que envuelve todo el contenedor, para que
        # los eventos de hover se capturen de forma central y siempre queden por encima
        # de los widgets internos.
        event_box = EventBox(events=["enter-notify-event", "leave-notify-event"])
        event_box.connect("enter-notify-event", self.on_mouse_enter)
        event_box.connect("leave-notify-event", self.on_mouse_leave)

        # Inicializamos MetricsSmall como un Overlay cuyo "child" es el EventBox
        super().__init__(
            name="metrics-small",
            child=main_box,
            visible=True,
            all_visible=True,
            overlays=[event_box]
        )

        # Actualización de métricas cada segundo
        GLib.timeout_add_seconds(1, self.update_metrics)

        # Estado inicial de los revealers y variables para la gestión del hover
        self.hide_timer = None
        self.hover_counter = 0

    def on_button_enter(self, widget, event):
        window = widget.get_window()
        if window:
            window.set_cursor(Gdk.Cursor(Gdk.CursorType.HAND2))

    def on_button_leave(self, widget, event):
        window = widget.get_window()
        if window:
            window.set_cursor(None)

    def _format_percentage(self, value: int) -> str:
        """Formato natural del porcentaje sin forzar ancho fijo."""
        return f"{value}%"

    def on_mouse_enter(self, widget, event):
        self.hover_counter += 1
        if self.hide_timer is not None:
            GLib.source_remove(self.hide_timer)
            self.hide_timer = None
        # Revelar niveles en hover para todas las métricas
        self.cpu_revealer.set_reveal_child(True)
        self.ram_revealer.set_reveal_child(True)
        self.disk_revealer.set_reveal_child(True)
        return False

    def on_mouse_leave(self, widget, event):
        if self.hover_counter > 0:
            self.hover_counter -= 1
        if self.hover_counter == 0:
            if self.hide_timer is not None:
                GLib.source_remove(self.hide_timer)
            self.hide_timer = GLib.timeout_add(500, self.hide_revealer)
        return False

    def hide_revealer(self):
        self.cpu_revealer.set_reveal_child(False)
        self.ram_revealer.set_reveal_child(False)
        self.disk_revealer.set_reveal_child(False)
        self.hide_timer = None
        return False

    def update_metrics(self):
        # Recuperar datos centralizados
        cpu, mem, disk = shared_provider.get_metrics()
        self.cpu_circle.set_value(cpu / 100.0)
        self.ram_circle.set_value(mem / 100.0)
        self.disk_circle.set_value(disk / 100.0)
        # Actualizar etiquetas con el porcentaje formateado
        self.cpu_level.set_label(self._format_percentage(int(cpu)))
        self.ram_level.set_label(self._format_percentage(int(mem)))
        self.disk_level.set_label(self._format_percentage(int(disk)))
        return True


class Battery(Overlay):
    def __init__(self, **kwargs):
        # Creamos el contenedor principal para los widgets métricos
        main_box = Box(
            name="metrics-small",
            spacing=0,
            orientation="h",
            visible=True,
            all_visible=True,
        )

        # ------------------ Battery ------------------
        self.bat_icon = Label(name="metrics-icon", markup=icons.battery)
        self.bat_circle = CircularProgressBar(
            name="metrics-circle",
            value=0,
            size=28,
            line_width=2,
            start_angle=150,
            end_angle=390,
            style_classes="bat",
            child=self.bat_icon,
        )
        self.bat_level = Label(name="metrics-level", style_classes="bat", label="100%")
        self.bat_revealer = Revealer(
            name="metrics-bat-revealer",
            transition_duration=250,
            transition_type="slide-left",
            child=self.bat_level,
            child_revealed=False,
        )
        self.bat_box = Box(
            name="metrics-bat-box",
            orientation="h",
            spacing=0,
            children=[self.bat_circle, self.bat_revealer],
        )

        # Agregamos cada widget métrico al contenedor principal
        main_box.add(self.bat_box)

        # Se crea un único EventBox que envuelve todo el contenedor, para que
        # los eventos de hover se capturen de forma central y siempre queden por encima
        # de los widgets internos.
        event_box = EventBox(events=["enter-notify-event", "leave-notify-event"])
        event_box.connect("enter-notify-event", self.on_mouse_enter)
        event_box.connect("leave-notify-event", self.on_mouse_leave)

        # Inicializamos MetricsSmall como un Overlay cuyo "child" es el EventBox
        super().__init__(
            name="metrics-small",
            child=main_box,
            visible=True,
            all_visible=True,
            overlays=[event_box]
        )

        # Actualización de la batería cada segundo
        self.batt_fabricator = Fabricator(lambda *args, **kwargs: shared_battery_provider.get_battery(), interval=1000, stream=False, default_value=0)
        self.batt_fabricator.changed.connect(self.update_battery)
        GLib.idle_add(self.update_battery, None, shared_battery_provider.get_battery())

        # Estado inicial de los revealers y variables para la gestión del hover
        self.hide_timer = None
        self.hover_counter = 0

    def _format_percentage(self, value: int) -> str:
        """Formato natural del porcentaje sin forzar ancho fijo."""
        return f"{value}%"

    def on_mouse_enter(self, widget, event):
        self.hover_counter += 1
        if self.hide_timer is not None:
            GLib.source_remove(self.hide_timer)
            self.hide_timer = None
        # Revelar niveles en hover para todas las métricas
        self.bat_revealer.set_reveal_child(True)
        return False

    def on_mouse_leave(self, widget, event):
        if self.hover_counter > 0:
            self.hover_counter -= 1
        if self.hover_counter == 0:
            if self.hide_timer is not None:
                GLib.source_remove(self.hide_timer)
            self.hide_timer = GLib.timeout_add(500, self.hide_revealer)
        return False

    def hide_revealer(self):
        self.bat_revealer.set_reveal_child(False)
        self.hide_timer = None
        return False

    def update_battery(self, sender, battery_data):
        value, charging, icon = battery_data
        if value == 0:
            self.set_visible(False)
        else:
            self.set_visible(True)
            self.bat_circle.set_value(value / 100)
        percentage = int(value)
        self.bat_level.set_label(self._format_percentage(percentage))
        self.bat_icon.set_markup(icon)
        if percentage <= 15:
            self.bat_icon.add_style_class("alert")
            self.bat_circle.add_style_class("alert")
        else:
            self.bat_icon.remove_style_class("alert")
            self.bat_circle.remove_style_class("alert")
