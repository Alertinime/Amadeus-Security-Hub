# Gestion des cles USB

Ce document decrit la detection des supports USB, la creation des fichiers de
securite et les helpers lies au support physique.

## Windows

`KeyListingWin.py` :

- detecte les lecteurs amovibles via `Win32_LogicalDisk`;
- considere une cle Security Hub valide si `USBSecurity/USBKey.rin` existe ;
- cree `USBSecurity/USBKey.rin` ;
- cree `USBSecurity/PasswordManager.Archer` ;
- extrait `PasswordManagerKey` pendant le login ;
- remonte d'un dossier `USBSecurity` vers l'objet WMI correspondant.

## Linux / POSIX

`KeyListingLinux.py` :

- liste les supports USB avec peripherique bloc ;
- lit les montages depuis `/proc/mounts` ;
- monte temporairement les partitions non montees via `udisksctl` ;
- cherche `USBSecurity/USBKey.rin` ;
- cree `USBSecurity/USBKey.rin` ;
- cree `USBSecurity/PasswordManager.Archer` ;
- extrait `PasswordManagerKey` pendant le login ;
- demonte uniquement les partitions montees par l'application.

## Contrat avec le reste du backend

Quand une cle est confirmee, `Api.usb` pointe vers le dossier `USBSecurity`.

Fichiers attendus :

```text
USBSecurity/
  USBKey.rin
  PasswordManager.Archer
```

## Formats ecrits

`USBKey.rin` :

- JSON avec `header` et `payload` ;
- payload chiffre en AES-GCM ;
- payload clair contenant `PasswordManagerKey` encodee en base64 ;
- cle de dechiffrement derivee du mot de passe maitre via Argon2id puis HKDF.

`PasswordManager.Archer` :

- JSON avec `header` et `payload` ;
- payload chiffre en AES-GCM ;
- payload clair attendu :

```json
{
  "sites": [
    {
      "url": "...",
      "password": "..."
    }
  ]
}
```

## Module legacy

`key-read&write/USB.py` est un module historique non branche au flux principal.
Il utilise Tkinter, des hypotheses Windows et un ancien format de fichier. Il
ne doit pas servir de reference pour les nouveaux flux.
