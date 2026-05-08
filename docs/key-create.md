# Creation des cles de securite

L'ancien dossier `app/Backend/Key/key-create/` ne contient actuellement pas de
code actif. La creation effective
des cles Security Hub est implementee dans :

- `app/Backend/Key/KeyListingWin.py`
- `app/Backend/Key/KeyListingLinux.py`

## Flux actuel

1. Le frontend appelle `api.init_usb(device, password)`.
2. L'API selectionne le support USB.
3. `initialize_security_key(...)` derive une cle depuis le mot de passe maitre.
4. `make_master_file(...)` cree `USBSecurity/USBKey.rin`.
5. `make_passwordManager_file(...)` cree
   `USBSecurity/PasswordManager.Archer`.

Le code actuel ne clone pas de cle et ne formate pas le support USB.
