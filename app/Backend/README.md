# Backend

Le backend contient le point d'entree Python et les services exposes au frontend `pywebview`.

## Composants principaux

- `OSManagement.py` : detection de l'OS via `os.name`
- `WebviewAPI.py` : API appelee depuis le JavaScript
- `Cryptography/PasswordManager.py` : derivation Argon2id et HKDF
- `Cryptography/SecretManager.py` : generation et stockage en memoire de secrets runtime
- `Key/KeyListingWin.py` : detection, creation et login Windows
- `Key/KeyListingLinux.py` : detection et creation POSIX avec montage temporaire

## Etat courant

- `Api.self.usb` represente le chemin du dossier `USBSecurity` ou `None`
- `Api.secret_manager` conserve les secrets de session en memoire pour l'instance `Api`
- l'initialisation cree deux fichiers :
  - `USBSecurity/USBKey.rin` : fichier maitre derive du mot de passe
  - `USBSecurity/PasswordManager.Archer` : conteneur chiffre des mots de passe
- le login Windows est branche au frontend et extrait `PasswordManagerKey` depuis `USBKey.rin`
- le frontend attend un booleen de `Api.login(...)` pour naviguer vers `Dashboard.html`
- le login POSIX n'est pas implemente dans le depot
