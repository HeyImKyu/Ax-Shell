## A ʜᴀᴄᴋᴀʙʟᴇ sʜᴇʟʟ ꜰᴏʀ Hʏᴘʀʟᴀɴᴅ, ᴘᴏᴡᴇʀᴇᴅ ʙʏ [Fᴀʙʀɪᴄ](https://github.com/Fabric-Development/fabric/).

<table align="center">
  <tr>
    <td colspan="4"><img src="https://github.com/user-attachments/assets/f52da9e7-31dd-4e7f-b0bb-f859816cde27"></td>
  </tr>
  <tr>
    <td colspan="1"><img src="https://github.com/user-attachments/assets/4754afe9-b474-4f42-b79c-c2a1b9b6be4f"></td>
    <td colspan="1"><img src="https://github.com/user-attachments/assets/e8e77b94-6aee-4086-b4b7-aab1878e0a4d"></td>
    <td colspan="1"><img src="https://github.com/user-attachments/assets/6aec1a96-2325-4c1d-a569-2f88896b04ff"></td>
    <td colspan="1" align="center"><img src="https://github.com/user-attachments/assets/26f72534-1911-4263-9e72-b7b90f0c36af"></td>
  </tr>
</table>

This is my own Fork of [Axenide's Ax-Shell](https://github.com/Axenide/Ax-Shell)

**There's a lot of stuff in here that probably wont work out of the box for anyone trying to use this.**

If you want to just run a script and have it work, take a look at the original Ax-Shell instead.

## Stuff i've changed from Axenide's implementations

- Notch opens and closes on hover (without click)
  - Exceptions:
    - When playing music; to still be able to use the player controls
    - When looking at kanban; to be able to drag Tasks better
- Implemented a sidebar:
  - Contains workspace switcher now
  - Has a download buttons that's implemented with aria2 to show progress and open ariang
  - Includes a VPN button to easily switch connected VPNs
- Notifications are on the top level (above fullscreen applications) and located in the top right
- The network button opens a new terminal with nmtui
- Workspaces button opens hyprexpo
- Own Clipboard-History implementation with a lot of nice features
- Added matugen vesktop integration, so my discord theme changes as well
- Wallpaper picker changes wallpapers on a single click
- Ability to download wallpapers right from the wallpaper picker
- Added battery gauge to the notch (Thank you [nova](https://github.com/nova-r/)<3)
- New battery icons
- Changed scroll direction in small circular sliders for volume etc
- Margin and gap changes
- Increased max volume to 200
- Changed paths for files to make them work for myself
- Changed screen corners a bit
- Removed pins tab cause it doesnt work for me
- Removed the coming soon tab
- Removed example images to make the clone on nixos rebuild more slim

### Dependencies
- [Fabric](https://github.com/Fabric-Development/fabric)
- [fabric-cli](https://github.com/Fabric-Development/fabric-cli)
- [Gray](https://github.com/Fabric-Development/gray)
- [Matugen](https://github.com/InioX/matugen)
- `brightnessctl`
- `cava`
- `gnome-bluetooth-3.0`
- `gobject-introspection`
- `gpu-screen-recorder`
- `grimblast`
- `hypridle`
- `hyprlock`
- `hyprpicker`
- `hyprsunset`
- `imagemagick`
- `libnotify`
- `noto-fonts-emoji`
- `playerctl`
- `swappy`
- `swww`
- `tesseract`
- `uwsm`
- `wl-clipboard`
- `wlinhibit`
- `foot`
- Python dependencies:
    - ijson
    - pillow
    - psutil
    - requests
    - setproctitle
    - toml
    - watchdog
    - thefuzz
- Fonts:
    - Zed Mono
    - Tabler Icons (included in [assests](https://github.com/HeyImKyu/Ax-Shell/tree/main/assets/fonts/tabler-icons))
