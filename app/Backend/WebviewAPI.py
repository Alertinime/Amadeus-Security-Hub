import os
from Backend.OSManagement import OSspliter
if OSspliter().get_current_os() == "nt":
  from Backend.Key.KeyListingWin import key_listing_win
elif OSspliter().get_current_os() == "posix":
  from Backend.Key.KeyListingLinux import key_listening_linux
import base64
from Backend.Cryptography.PasswordManager import PasswordManager
from Backend.Cryptography.SecretManager import SecretManager
class Api():
  def __init__(self,): 
    self.usb = None
    self.secret_manager = SecretManager()
    pass
  def login(self, value):
    response = False
    result = None
    try:
      if self.check_os() == "nt":
          key_win = key_listing_win()
          result = key_win.login_usb(self.usb, value)
          if result:
            self.secret_manager.store_secret("PasswordManagerKey", result)
            print("Login result:", base64.b64decode(result) if result else "No result" )
            response = True
      elif self.check_os() == "posix":
          key_linux = key_listening_linux()
          if hasattr(key_linux, "login_usb"):
            result = key_linux.login_usb(self.usb, value)
            if result:
              self.secret_manager.store_secret("PasswordManagerKey", result)
              print("Login result:", base64.b64decode(result) if result else "No result" )
              response = True
          else:
            print("Login is not implemented on this platform yet.")
            result = False
          print("Login result:", result)
    except Exception as exc:
      print("Login failed:", exc)
      response = False

    return response
  def check_os(self):
    os_spliter = OSspliter()
    return os_spliter.get_current_os()

  def set_window(self, window):
    self.window = window

  def reload_usb_check(self):
    self.usb = None
    if self.check_os() == "nt": 
        key_win = key_listing_win()
        key = key_win.check_for_key()
        if key != False:
          usb = key_win.check_for_security_key(key)
        if key == False:
          self.usb = None
          return "Nokey.html"
        elif usb == False:
          self.usb = None
          return "CreateKey.html"
        else:
          self.usb = key_win.get_security_dir(usb) or None
          return "Login.html"
    elif self.check_os() == "posix":
        key_linux = key_listening_linux()
        key = key_linux.list_usb()
        usb = key_linux.check_for_security_key(key)
        if len(key) == 0:
          self.usb = None
          return "Nokey.html"
        elif usb == False:
          self.usb = None
          return "CreateKey.html"
        else:
          self.usb = key_linux.get_security_dir(usb) or None
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
    self.usb = None
    if self.check_os() == "posix":
        key_linux = key_listening_linux()
        usb_devices = key_linux.list_usb()
        for usb in usb_devices:
          if usb["product"] == device:
            result = key_linux.initialize_security_key(usb, password)
            if not result:
              return False

            security_dir = key_linux.get_security_dir(usb)
            key_path = os.path.join(security_dir, "USBKey.rin") if security_dir else ""
            if key_path and os.path.exists(key_path):
              self.usb = security_dir
              return True
            return False
        return False
    elif self.check_os() == "nt":
        key_win = key_listing_win()
        usb_devices = key_win.check_for_key() or []
        for usb in usb_devices:
          if getattr(usb, "Caption", None) == device:
            result = key_win.initialize_security_key(usb, password)
            if not result:
              return False

            security_dir = key_win.get_security_dir(usb)
            key_path = os.path.join(security_dir, "USBKey.rin") if security_dir else ""
            if key_path and os.path.exists(key_path):
              self.usb = security_dir
              return True
            return False
        return False
