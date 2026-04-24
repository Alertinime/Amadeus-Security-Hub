import base64
import os

from Backend.Controller.AMHSPswdCtrl import Pswctrl
from Backend.Key.KeyListingWin import key_listing_win


class Api():
  def __init__(self,):
    self.usb = None
    self.window = None
    self.pswctrl = Pswctrl(self)

  def login(self, value):
    response = False
    result = None

    try:
      key_win = key_listing_win()
      result = key_win.login_usb(self.usb, value)
      if result:
        self.pswctrl.set_secret(result)
        print("Login result:", base64.b64decode(result) if result else "No result")
        response = True
    except Exception as exc:
      print("Login failed:", exc)
      response = False

    return response

  def set_window(self, window):
    self.window = window

  def reload_usb_check(self):
    self.usb = None
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

  def usb_list(self):
    key_win = key_listing_win()
    return key_win.list_usb_for_frontend()

  def init_usb(self, device, password):
    print("Initializing USB:", device, "with password:", password)
    self.usb = None
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
