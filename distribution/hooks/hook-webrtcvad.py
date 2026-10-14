# The installed wheel is webrtcvad-wheels, not the legacy webrtcvad distribution.
from PyInstaller.utils.hooks import copy_metadata
datas = copy_metadata("webrtcvad-wheels")
hiddenimports = ["_webrtcvad"]
