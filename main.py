import setproctitle
import os
import shutil
from fabric import Application
from fabric.utils import get_relative_path, exec_shell_command_async
from modules.bar import Bar
from modules.sidebar import SideBar
from modules.notch import Notch
from modules.dock import Dock
from modules.corners import Corners
import config.data as data

fonts_updated_file = f"{data.CACHE_DIR}/fonts_updated"

if __name__ == "__main__":
    setproctitle.setproctitle(data.APP_NAME)

    if not os.path.isfile(data.CONFIG_FILE):
        exec_shell_command_async(f"python {os.path.expanduser(f"~/.config/Ax-Shell/config/config.py")}")

    current_wall = os.path.expanduser("~/.current.wall")
    if not os.path.exists(current_wall):
        shutil.copyfile(os.path.expanduser(f"~/.config/{data.APP_NAME_CAP}/assets/wallpapers_example/example-1.jpg"), os.path.expanduser(f"~/.current.wall"))

    corners = Corners()
    bar = Bar()
    sidebar = SideBar(main_bar=bar)
    notch = Notch()
    dock = Dock() 
    bar.notch = notch
    notch.bar = bar
    app = Application(f"{data.APP_NAME}", bar, notch, dock)

    def set_css():
        app.set_stylesheet_from_file(
            get_relative_path("main.css"),
            exposed_functions={
                "overview_width": lambda: f"min-width: {data.CURRENT_WIDTH * 0.1 * 5 + 92}px;",
                "overview_height": lambda: f"min-height: {data.CURRENT_HEIGHT * 0.1 * 2 + 32 + 56}px;",
            },
        )

    app.set_css = set_css

    app.set_css()

    app.run()
