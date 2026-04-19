from Backend.OSManagement import OSspliter
if OSspliter().get_current_os() == "nt":
  from Backend.Key.KeyListingWin import key_listing_win
elif OSspliter().get_current_os() == "posix":
  from Backend.Key.KeyListingLinux import key_listening_linux
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
    elif self.check_os() == "posix":
        key_linux = key_listening_linux()
        key = key_linux.list_usb()
        usb = key_linux.check_for_security_key(key)
        if len(key) == 0:
          return "Nokey.html"
        elif usb == False:
          return "CreateKey.html"
        else:
          return "Login.html"
  def usb_list(self):
    if self.check_os() == "nt":
        key_win = key_listing_win()
        return key_win.list_usb_for_frontend()
    elif self.check_os() == "posix":
        key_linux = key_listening_linux()
        usb_devices = key_linux.list_usb()
        return [usb["product"] for usb in usb_devices]
  
  def init_usb(self, device, password):
    print("Initializing USB:", device, "with password:", password)
    if self.check_os() == "posix":
        key_linux = key_listening_linux()
        usb_devices = key_linux.list_usb()
        for usb in usb_devices:
          if usb["product"] == device:
            result = key_linux.initialize_security_key(usb, password)
            return result
    elif self.check_os() == "nt":
        key_win = key_listing_win()
        usb_devices = key_win.check_for_key() or []
        for usb in usb_devices:
          if getattr(usb, "Caption", None) == device:
            result = key_win.initialize_security_key(usb, password)
            return result
        return False
