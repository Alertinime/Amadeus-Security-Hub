import base64
import os

from Backend.Controller.AMHSPswdCtrl import Pswctrl
from Backend.Key.KeyListingLinux import key_listening_linux


class Api():
  def __init__(self,):
    self.usb = None
    self.window = None
    self.pswctrl = Pswctrl()
    self.key_listener = key_listening_linux()

  def login(self, value):
    response = False
    result = None

    try:
      key_linux = self.key_listener
      if hasattr(key_linux, "login_usb"):
        result = key_linux.login_usb(self.usb, value)
        if result:
          self.pswctrl.set_secret(result)
          print("Login result:", base64.b64decode(result) if result else "No result")
          response = True
      else:
        print("Login is not implemented on this platform yet.")
        result = False
      print("Login result:", result)
    except Exception as exc:
      print("Login failed:", exc)
      response = False

    return response

  def set_window(self, window):
    self.window = window

  def reload_usb_check(self):
    self.usb = None
    key_linux = self.key_listener
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
    key_linux = self.key_listener
    return key_linux.list_usb_for_frontend()

  def init_usb(self, device, password):
    print("Initializing USB:", device, "with password:", password)
    self.usb = None
    key_linux = self.key_listener
    usb_devices = key_linux.list_usb()
    for usb in usb_devices:
      device_ids = (
        key_linux.get_usb_id(usb),
        key_linux.get_usb_name(usb),
        usb.get("product", ""),
        usb.get("sysname", ""),
      )
      if device in device_ids:
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

  def _get_usb_aad(self):
    if not self.usb:
      print("No USB security directory is selected.")
      return None

    key_linux = self.key_listener
    usb = key_linux.get_usb_from_security_dir(self.usb)
    if not usb:
      print("Unable to resolve USB device from security directory:", self.usb)
      return None

    return key_linux.get_usb_serial(usb).encode("utf-8")

  def update_password_data(self,data):
    aad = self._get_usb_aad()
    if aad is None:
      return False

    result = self.pswctrl.update_file_with_new_data(self.usb, aad, data)
    if not result:
        return False
    return self.get_data_list_from_pswctrl(self.usb, aad)

  def get_data_list_from_pswctrl(self, path, aad):
        response = self.pswctrl.get_file_data(path, aad)
        if not response:
            print("Failed to get data list from password controller:", path)
            return False
        return response.get("sites", [])

  def get_pswtable_data(self):
    aad = self._get_usb_aad()
    if aad is None:
      return False
    return self.get_data_list_from_pswctrl(self.usb, aad)
