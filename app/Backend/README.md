# Backend

Le backend contient le point d'entree Python et les services exposes au frontend `pywebview`.

## Composants principaux

- `OSManagement.py` : detection de l'OS via `os.name`
- `WebviewAPI.py` : API appelee depuis le JavaScript
- `Cryptography/PasswordManager.py` : derivation Argon2id et HKDF
- `Key/KeyListingWin.py` : detection, creation et login Windows
- `Key/KeyListingLinux.py` : detection et creation POSIX avec montage temporaire

## Etat courant

- `Api.self.usb` represente le chemin du dossier `USBSecurity` ou `None`
- le login Windows est branche au frontend
- le login POSIX n'est pas implemente dans le depot
