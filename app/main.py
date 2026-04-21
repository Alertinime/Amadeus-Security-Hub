import webview
from Backend.OSManagement import OSspliter
from Backend.WebviewAPI import Api
os_spliter = OSspliter()
if os_spliter.get_current_os() == "nt":
    from Backend.Key.KeyListingWin import key_listing_win
    key_win = key_listing_win()
    key = key_win.check_for_key()
    if key != False:
      usb = key_win.check_for_security_key(key)
api = Api()
if os_spliter.get_current_os() == "posix":
    from Backend.Key.KeyListingLinux import key_listening_linux
    key_linux = key_listening_linux()
    usb_devices = key_linux.list_usb()
    if len(usb_devices) != 0:
      key = True
      print("USB devices found:", [usb["product"] for usb in usb_devices])
      usb = key_linux.check_for_security_key(usb_devices)
    else:
      key = False
      usb = False
if key == False:
  window = webview.create_window('Amadeus Sécurity Hub', 'Frontend/Html/Nokey.html', js_api=api)
elif usb == False:
  window = webview.create_window('Amadeus Sécurity Hub', 'Frontend/Html/CreateKey.html', js_api=api)
else:
  print("Security key found:", usb)
  window = webview.create_window('Amadeus Sécurity Hub', 'Frontend/Html/Login.html', js_api=api)
#api.set_window(window) je test pour voir si ça résout de lag au demarage sur windows
try:
  webview.start(debug=False)
finally:
  if os_spliter.get_current_os() == "posix":
    key_listening_linux().cleanup_managed_mounts()
