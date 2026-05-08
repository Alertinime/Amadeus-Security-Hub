# Runtime Python

Ce document decrit le runtime Python necessaire a l'application desktop.

## Point d'entree

Le point d'entree applicatif est :

```powershell
python app\main.py
```

La commande doit etre lancee depuis la racine du depot pour que les chemins
relatifs vers `Frontend/Html/...` restent valides.

## Dependances Python

`requirements.txt` contient :

- `argon2-cffi`
- `cryptography`
- `wmi`
- `pywebview`

Installation typique :

```powershell
pip install -r runtime\requirements.txt
```

## Dependances systeme

Windows :

- WMI accessible par Python ;
- support USB vu comme `Win32_LogicalDisk` avec `DriveType == 2`.

Linux/POSIX :

- acces a `/sys/bus/usb/devices` ;
- acces a `/proc/mounts` ;
- `udisksctl` disponible si l'application doit monter une partition non
  montee.

## Role runtime

- lancer `pywebview` ;
- exposer les methodes Python au JavaScript ;
- charger les pages HTML locales ;
- laisser le backend lire et ecrire les fichiers chiffres sur le support USB.
