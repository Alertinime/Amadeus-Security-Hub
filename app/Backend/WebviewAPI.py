from Backend.OSManagement import OSspliter
from Backend.Key.KeyListingWin import key_listing_win
class Api():
  def __init__(self,): 
    pass
  def log(self, value):
    print(value)
  def check_os(self):
    os_spliter = OSspliter()
    return os_spliter.get_current_os()

  def set_window(self, window):
    self.window = window

  def reload_usb_check(self):
    if self.check_os() == "nt":
        key_win = key_listing_win()
        key = key_win.check_for_key()
        if key != False:
          usb = key_win.check_for_security_key(key)
        if key == False:
          return "Nokey.html"
        elif usb == False:
          return "CreateKey.html"
        else:
          return "Login.html"