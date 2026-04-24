# cette classe est le controller des fonctionnalités liées au gestionnaire de mots de passe

class Pswctrl():
    def __init__(self, webview_api):
        self.secret = None
    def set_secret(self, value):
        self.secret = value