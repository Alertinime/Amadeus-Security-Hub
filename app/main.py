import webview
from Backend.OSManagement import OSspliter
class Api():
  def log(self, value):
    print(value)
os_spliter = OSspliter()
print(f"Current OS: {os_spliter.get_current_os()}")

window = webview.create_window('Woah dude!', 'Frontend/Html/Login.html', js_api=Api())
webview.start()