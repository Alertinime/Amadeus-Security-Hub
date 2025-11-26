import webview
from Backend.OSManagement import OSspliter
from Backend.Key.KeyListingWin import key_listing_win
from Backend.WebviewAPI import Api
os_spliter = OSspliter()
if os_spliter.get_current_os() == "nt":
    key_win = key_listing_win()
    key = key_win.check_for_key()
    if key != False:
      usb = key_win.check_for_security_key(key)

if key == False:
  window = webview.create_window('Amadeus Sécurity Hub', 'Frontend/Html/Nokey.html', js_api=Api())
elif usb == False:
  window = webview.create_window('Amadeus Sécurity Hub', 'Frontend/Html/CreateKey.html', js_api=Api())
else:
  window = webview.create_window('Amadeus Sécurity Hub', 'Frontend/Html/Login.html', js_api=Api())
webview.start()