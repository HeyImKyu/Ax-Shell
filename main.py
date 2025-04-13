from modules.notifications import NotificationBox
import setproctitle
import os
from fabric import Application
from fabric.utils import get_relative_path, exec_shell_command_async
from modules.bar import Bar
from modules.sidebar import SideBar
from modules.notch import Notch
from modules.dock import Dock
from modules.corners import Corners
from modules.notification_window import NotificationWindow

# Direct import of data module to avoid possible circular imports
from config.data import APP_NAME, CACHE_DIR, CONFIG_FILE, CURRENT_WIDTH, CURRENT_HEIGHT, APP_NAME_CAP

fonts_updated_file = f"{CACHE_DIR}/fonts_updated"

if __name__ == "__main__":
    setproctitle.setproctitle(APP_NAME)

    current_wallpaper = os.path.expanduser("~/.current.wall")
    if not os.path.exists(current_wallpaper):
        example_wallpaper = os.path.expanduser(f"~/.wallpapers/example-1.jpg")
        os.symlink(example_wallpaper, current_wallpaper)

    corners = Corners()
    bar = Bar()
    sidebar = SideBar(main_bar=bar)
    notification = NotificationWindow()
    notch = Notch(notif_win=notification)
    dock = Dock() 
    bar.notch = notch
    notch.bar = bar
    app = Application(f"{APP_NAME}", bar, notch, dock, notification)

    def set_css():
        app.set_stylesheet_from_file(
            get_relative_path("main.css"),
            exposed_functions={
                "overview_width": lambda: f"min-width: {CURRENT_WIDTH * 0.1 * 5 + 92}px;",
                "overview_height": lambda: f"min-height: {CURRENT_HEIGHT * 0.1 * 2 + 32 + 56}px;",
            },
        )

    app.set_css = set_css

    app.set_css()

    app.run()
