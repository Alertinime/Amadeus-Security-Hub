from Backend.OSManagement import OSspliter

current_os = OSspliter().get_current_os()

if current_os == "nt":
  from Backend.WebviewAPIWindows import Api
elif current_os == "posix":
  from Backend.WebviewAPILinux import Api
else:
  raise RuntimeError(f"Unsupported OS: {current_os}")
