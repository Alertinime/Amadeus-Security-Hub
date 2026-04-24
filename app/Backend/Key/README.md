# Gestion des cles USB

Ce dossier regroupe la detection USB, la creation des fichiers de securite lies a la cle,
et les helpers associes au support physique.

## Windows

`KeyListingWin.py` :

- detecte les lecteurs USB via `Win32_LogicalDisk`
- considere une cle Security Hub valide si `USBSecurity/USBKey.rin` existe
- derive et ecrit `USBKey.rin`
- cree aussi `USBSecurity/PasswordManager.Archer`
- extrait `PasswordManagerKey` depuis `USBKey.rin` pendant le login
- expose aussi des helpers pour remonter du dossier `USBSecurity` vers l'objet WMI

## POSIX

`KeyListingLinux.py` :

- liste les supports USB avec peripherique bloc
- reutilise les montages existants
- monte temporairement les partitions non montees si necessaire
- cherche `USBSecurity/USBKey.rin`
- cree aussi `USBSecurity/PasswordManager.Archer` a l'initialisation
- demonte les partitions montees uniquement pour l'inspection si aucune cle n'est trouvee
- garde en memoire les montages realises par l'application pour les nettoyer a la fermeture

## Contrat utile pour le reste du projet

- quand une cle est confirmee, `WebviewAPI.Api.self.usb` pointe vers le dossier `USBSecurity`
- les fichiers attendus dans ce dossier sont :
  - `USBKey.rin`
  - `PasswordManager.Archer`

## Fichiers ecrits sur la cle

- `USBKey.rin`
  - contient un package JSON avec `header` et `payload`
  - le `payload` chiffre contient actuellement `PasswordManagerKey` encodee en base64
  - la cle de dechiffrement est rederivee depuis le mot de passe maitre

- `PasswordManager.Archer`
  - contient un package JSON avec `header` et `payload`
  - le `payload` chiffre contient une structure du type :
    - `{"sites": [{"url": "...", "password": "..."}]}`
  - ce conteneur est chiffre avec `PasswordManagerKey`
