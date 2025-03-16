from typing import Any, List, Literal
from fabric.widgets.label import Label
from fabric.widgets.button import Button
from fabric.widgets.centerbox import CenterBox
from fabric.widgets.scrolledwindow import ScrolledWindow
from fabric.widgets.box import Box
import modules.icons as icons

import gi
from fabric.core.service import Property, Service, Signal
from fabric.utils import bulk_connect, exec_shell_command_async
from gi.repository import Gio
from loguru import logger

try:
    gi.require_version("NM", "1.0")
    from gi.repository import NM
except ValueError:
    logger.error("Failed to start network manager")


class Wifi(Service):
    """A service to manage the wifi connection."""

    @Signal
    def changed(self) -> None: ...

    @Signal
    def enabled(self) -> bool: ...

    def __init__(self, client: NM.Client, device: NM.DeviceWifi, **kwargs):
        self._client: NM.Client = client
        self._device: NM.DeviceWifi = device
        self._ap: NM.AccessPoint | None = None
        self._ap_signal: int | None = None
        super().__init__(**kwargs)

        self._client.connect(
            "notify::wireless-enabled",
            lambda *args: self.notifier("enabled", args),
        )
        if self._device:
            bulk_connect(
                self._device,
                {
                    "notify::active-access-point": lambda *args: self._activate_ap(),
                    "access-point-added": lambda *args: self.emit("changed"),
                    "access-point-removed": lambda *args: self.emit("changed"),
                    "state-changed": lambda *args: self.ap_update(),
                },
            )
            self._activate_ap()

    def ap_update(self):
        self.emit("changed")
        for sn in [
            "enabled",
            "internet",
            "strength",
            "frequency",
            "access-points",
            "ssid",
            "state",
            "icon-name",
        ]:
            self.notify(sn)

    def _activate_ap(self):
        if self._ap:
            self._ap.disconnect(self._ap_signal)
        self._ap = self._device.get_active_access_point()
        if not self._ap:
            return

        self._ap_signal = self._ap.connect(
            "notify::strength", lambda *args: self.ap_update()
        )  # type: ignore

    def toggle_wifi(self):
        self._client.wireless_set_enabled(not self._client.wireless_get_enabled())

    # def set_active_ap(self, ap):
    #     self._device.access

    def scan(self):
        self._device.request_scan_async(
            None,
            lambda device, result: [
                device.request_scan_finish(result),
                self.emit("changed"),
            ],
        )

    def notifier(self, name: str, *args):
        self.notify(name)
        self.emit("changed")
        return

    @Property(bool, "read-write", default_value=False)
    def enabled(self) -> bool:  # type: ignore
        return bool(self._client.wireless_get_enabled())

    @enabled.setter
    def enabled(self, value: bool):
        self._client.wireless_set_enabled(value)

    @Property(int, "readable")
    def strength(self):
        return self._ap.get_strength() if self._ap else -1

    @Property(str, "readable")
    def icon_name(self):
        if not self._ap:
            return "network-wireless-disabled-symbolic"

        if self.internet == "activated":
            return {
                80: "network-wireless-signal-excellent-symbolic",
                60: "network-wireless-signal-good-symbolic",
                40: "network-wireless-signal-ok-symbolic",
                20: "network-wireless-signal-weak-symbolic",
                00: "network-wireless-signal-none-symbolic",
            }.get(
                min(80, 20 * round(self._ap.get_strength() / 20)),
                "network-wireless-no-route-symbolic",
            )
        if self.internet == "activating":
            return "network-wireless-acquiring-symbolic"

        return "network-wireless-offline-symbolic"

    @Property(int, "readable")
    def frequency(self):
        return self._ap.get_frequency() if self._ap else -1

    @Property(int, "readable")
    def internet(self):
        return {
            NM.ActiveConnectionState.ACTIVATED: "activated",
            NM.ActiveConnectionState.ACTIVATING: "activating",
            NM.ActiveConnectionState.DEACTIVATING: "deactivating",
            NM.ActiveConnectionState.DEACTIVATED: "deactivated",
        }.get(
            self._device.get_active_connection().get_state(),
            "unknown",
        )

    @Property(object, "readable")
    def access_points(self) -> List[object]:
        points: list[NM.AccessPoint] = self._device.get_access_points()

        def make_ap_dict(ap: NM.AccessPoint):
            return {
                "bssid": ap.get_bssid(),
                # "address": ap.get_
                "last_seen": ap.get_last_seen(),
                "ssid": NM.utils_ssid_to_utf8(ap.get_ssid().get_data())
                if ap.get_ssid()
                else "Unknown",
                "active-ap": self._ap,
                "strength": ap.get_strength(),
                "frequency": ap.get_frequency(),
                "icon-name": {
                    80: "network-wireless-signal-excellent-symbolic",
                    60: "network-wireless-signal-good-symbolic",
                    40: "network-wireless-signal-ok-symbolic",
                    20: "network-wireless-signal-weak-symbolic",
                    00: "network-wireless-signal-none-symbolic",
                }.get(
                    min(80, 20 * round(ap.get_strength() / 20)),
                    "network-wireless-no-route-symbolic",
                ),
            }

        return list(map(make_ap_dict, points))

    @Property(str, "readable")
    def ssid(self):
        if not self._ap:
            return "Disconnected"
        ssid = self._ap.get_ssid().get_data()
        return NM.utils_ssid_to_utf8(ssid) if ssid else "Unknown"

    @Property(int, "readable")
    def state(self):
        return {
            NM.DeviceState.UNMANAGED: "unmanaged",
            NM.DeviceState.UNAVAILABLE: "unavailable",
            NM.DeviceState.DISCONNECTED: "disconnected",
            NM.DeviceState.PREPARE: "prepare",
            NM.DeviceState.CONFIG: "config",
            NM.DeviceState.NEED_AUTH: "need_auth",
            NM.DeviceState.IP_CONFIG: "ip_config",
            NM.DeviceState.IP_CHECK: "ip_check",
            NM.DeviceState.SECONDARIES: "secondaries",
            NM.DeviceState.ACTIVATED: "activated",
            NM.DeviceState.DEACTIVATING: "deactivating",
            NM.DeviceState.FAILED: "failed",
        }.get(self._device.get_state(), "unknown")


class Ethernet(Service):
    """A service to manage the ethernet connection."""

    @Signal
    def changed(self) -> None: ...

    @Signal
    def enabled(self) -> bool: ...

    @Property(int, "readable")
    def speed(self) -> int:
        return self._device.get_speed()

    @Property(str, "readable")
    def internet(self) -> str:
        return {
            NM.ActiveConnectionState.ACTIVATED: "activated",
            NM.ActiveConnectionState.ACTIVATING: "activating",
            NM.ActiveConnectionState.DEACTIVATING: "deactivating",
            NM.ActiveConnectionState.DEACTIVATED: "deactivated",
        }.get(
            self._device.get_active_connection().get_state(),
            "disconnected",
        )

    @Property(str, "readable")
    def icon_name(self) -> str:
        network = self.internet
        if network == "activated":
            return "network-wired-symbolic"

        elif network == "activating":
            return "network-wired-acquiring-symbolic"

        elif self._device.get_connectivity != NM.ConnectivityState.FULL:
            return "network-wired-no-route-symbolic"

        return "network-wired-disconnected-symbolic"

    def __init__(self, client: NM.Client, device: NM.DeviceEthernet, **kwargs) -> None:
        super().__init__(**kwargs)
        self._client: NM.Client = client
        self._device: NM.DeviceEthernet = device

        for pn in (
            "active-connection",
            "icon-name",
            "internet",
            "speed",
            "state",
        ):
            self._device.connect(f"notify::{pn}", lambda *_: self.notifier(pn))

        self._device.connect("notify::speed", lambda *_: print(_))

    def notifier(self, pn):
        self.notify(pn)
        self.emit("changed")


class NetworkClient(Service):
    """A service to manage the network connections."""

    @Signal
    def device_ready(self) -> None: ...

    def __init__(self, **kwargs):
        self._client: NM.Client | None = None
        self.wifi_device: Wifi | None = None
        self.ethernet_device: Ethernet | None = None
        super().__init__(**kwargs)
        NM.Client.new_async(
            cancellable=None,
            callback=self._init_network_client,
            **kwargs,
        )

    def _init_network_client(self, client: NM.Client, task: Gio.Task, **kwargs):
        self._client = client
        wifi_device: NM.DeviceWifi | None = self._get_device(NM.DeviceType.WIFI)  # type: ignore
        ethernet_device: NM.DeviceEthernet | None = self._get_device(
            NM.DeviceType.ETHERNET
        )

        if wifi_device:
            self.wifi_device = Wifi(self._client, wifi_device)
            self.emit("device-ready")

        if ethernet_device:
            self.ethernet_device = Ethernet(client=self._client, device=ethernet_device)
            self.emit("device-ready")

        self.notify("primary-device")

    def _get_device(self, device_type) -> Any:
        devices: List[NM.Device] = self._client.get_devices()  # type: ignore
        return next(
            (
                x
                for x in devices
                if x.get_device_type() == device_type
                and x.get_active_connection() is not None
            ),
            None,
        )

    def _get_primary_device(self) -> Literal["wifi", "wired"] | None:
        if not self._client:
            return None
        return (
            "wifi"
            if "wireless"
            in str(self._client.get_primary_connection().get_connection_type())
            else "wired"
            if "ethernet"
            in str(self._client.get_primary_connection().get_connection_type())
            else None
        )

    def connect_wifi_bssid(self, bssid):
        # We are using nmcli here, idk im lazy
        exec_shell_command_async(
            f"nmcli device wifi connect {bssid}", lambda *args: print(args)
        )

    @Property(str, "readable")
    def primary_device(self) -> Literal["wifi", "wired"] | None:
        return self._get_primary_device()

class NetworkConnections(Box):
    def __init__(self, **kwargs):
        super().__init__(
            name="network",
            spacing=4,
            orientation="vertical",
            **kwargs,
        )

        self.widgets = kwargs["widgets"]

        self.buttons = self.widgets.buttons.network_button
        self.net_status_text = self.buttons.network_status_text
        self.net_status_button = self.buttons.network_status_button
        self.net_icon = self.buttons.network_icon
        self.net_label = self.buttons.network_label
        self.net_menu_button = self.buttons.network_menu_button
        self.net_menu_label = self.buttons.network_menu_label

        # self.client = NetworkClient(on_device_added=self.on_device_added)
        self.scan_label = Label(name="bluetooth-scan-label", markup=icons.radar)
        self.scan_button = Button(
            name="bluetooth-scan",
            child=self.scan_label,
            tooltip_text="Scan for Bluetooth devices",
            # on_clicked=lambda *_: self.client.toggle_scan()
        )
        self.back_button = Button(
            name="bluetooth-back",
            child=Label(name="bluetooth-back-label", markup=icons.chevron_left),
            on_clicked=lambda *_: self.widgets.show_notif()
        )

        # self.client.connect("notify::enabled", lambda *_: self.status_label())
        # self.client.connect(
        #     "notify::scanning",
        #     lambda *_: self.update_scan_label()
        # )

        self.paired_box = Box(spacing=2, orientation="vertical")
        self.available_box = Box(spacing=2, orientation="vertical")

        # Create a single content container with the required structure:
        # [Paired label] [Paired devices list] [Available label] [Available devices list]
        content_box = Box(spacing=4, orientation="vertical")
        content_box.add(self.paired_box)
        content_box.add(Label(name="bluetooth-section", label="Available"))
        content_box.add(self.available_box)

        self.children = [
            CenterBox(
                name="bluetooth-header",
                start_children=self.back_button,
                center_children=Label(name="bluetooth-text", label="Bluetooth Devices"),
                end_children=self.scan_button
            ),
            ScrolledWindow(
                name="bluetooth-devices",
                min_content_size=(-1, -1),
                child=content_box,
                v_expand=True
            ),
        ]

        # Trigger initial notifications to update status without delay.
        # self.client.notify("scanning")
        # self.client.notify("enabled")

    def status_label(self):
        # # print(self.client.enabled)
        # if self.client.enabled:
        #     self.bt_status_text.set_label("Enabled")
        #     for i in [self.bt_status_button, self.bt_status_text, self.bt_icon, self.bt_label, self.bt_menu_button, self.bt_menu_label]:
        #         i.remove_style_class("disabled")
        #     self.bt_icon.set_markup(icons.bluetooth)
        # else:
            self.bt_status_text.set_label("Disabled")
            for i in [self.bt_status_button, self.bt_status_text, self.bt_icon, self.bt_label, self.bt_menu_button, self.bt_menu_label]:
                i.add_style_class("disabled")
            self.bt_icon.set_markup(icons.bluetooth_off)

    # def on_device_added(self, client: BluetoothClient, address: str):
    #     if not (device := client.get_device(address)):
    #         return
    #     # slot = BluetoothDeviceSlot(device)

    #     if device.paired:
    #         return self.paired_box.add(slot)
    #     return self.available_box.add(slot)

    def update_scan_label(self):
        # if self.client.scanning:
        #     self.scan_label.add_style_class("scanning")
        #     self.scan_button.add_style_class("scanning")
        #     self.scan_button.set_tooltip_text("Stop scanning for Bluetooth devices")
        # else:
            self.scan_label.remove_style_class("scanning")
            self.scan_button.remove_style_class("scanning")
            self.scan_button.set_tooltip_text("Scan for Bluetooth devices")
