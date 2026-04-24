import webview

from Backend.OSManagement import OSspliter

os_spliter = OSspliter()
current_os = os_spliter.get_current_os()

if current_os == "nt":
  from Backend.WebviewAPIWindows import Api
  from Backend.Key.KeyListingWin import key_listing_win
elif current_os == "posix":
  from Backend.WebviewAPILinux import Api
  from Backend.Key.KeyListingLinux import key_listening_linux
else:
  raise RuntimeError(f"Unsupported OS: {current_os}")

api = Api()
key = False
usb = False

if current_os == "nt":
  key_win = key_listing_win()
  key = key_win.check_for_key()
  if key != False:
    usb = key_win.check_for_security_key(key)
    if usb != False:
      api.usb = key_win.get_security_dir(usb) or None

if current_os == "posix":
  key_linux = key_listening_linux()
  usb_devices = key_linux.list_usb()
  if len(usb_devices) != 0:
    key = True
    print("USB devices found:", [usb["product"] for usb in usb_devices])
    usb = key_linux.check_for_security_key(usb_devices)
    if usb != False:
      api.usb = key_linux.get_security_dir(usb) or None
  else:
    key = False
    usb = False

if key == False:
  window = webview.create_window('Amadeus Security Hub', 'Frontend/Html/Nokey.html', js_api=api)
elif usb == False:
  window = webview.create_window('Amadeus Security Hub', 'Frontend/Html/CreateKey.html', js_api=api)
else:
  print("Security key found:", usb)
  window = webview.create_window('Amadeus Security Hub', 'Frontend/Html/Login.html', js_api=api)

try:
  webview.start(debug=False)
finally:
  if current_os == "posix":
    key_listening_linux().cleanup_managed_mounts()
