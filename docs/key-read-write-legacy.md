# Lecture / ecriture legacy

L'ancien dossier `app/Backend/Key/key-read&write/` contient un module
historique (`USB.py`) non branche au flux principal de l'application.

## Statut

- Non utilise par `app/main.py`.
- Non utilise par `WebviewAPIWindows.py`.
- Non utilise par `WebviewAPILinux.py`.
- Non compatible avec le format moderne complet documente dans
  `key-management.md`.

## Remarques

Le module utilise Tkinter pour demander un mot de passe, des appels Windows via
`ctypes` et des attributs WMI. Il peut servir d'archive de prototype, mais les
nouveaux developpements doivent cibler `KeyListingWin.py`,
`KeyListingLinux.py` et `Controller/AMHSPswdCtrl.py`.
