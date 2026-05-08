# Backend

Le backend contient le point d'entree Python, les APIs exposees au frontend
`pywebview`, la detection USB, la crypto et le controleur du gestionnaire de
mots de passe.

## Composants

- `OSManagement.py` : retourne `os.name`.
- `WebviewAPI.py` : facade qui expose l'API adaptee a l'OS courant.
- `WebviewAPIWindows.py` : API `pywebview` pour Windows.
- `WebviewAPILinux.py` : API `pywebview` pour Linux/POSIX.
- `Controller/AMHSPswdCtrl.py` : lecture, ajout et reecriture du fichier
  `PasswordManager.Archer`.
- `Cryptography/PasswordManager.py` : Argon2id, HKDF et generation du sel de
  mot de passe.
- `Cryptography/SecretManager.py` : generation de cles, sels et AAD aleatoires.
- `Key/KeyListingWin.py` : detection USB, creation et login Windows.
- `Key/KeyListingLinux.py` : detection USB, montage temporaire, creation et
  login Linux/POSIX.

## Contrat avec le frontend

Les classes `Api` Windows et Linux exposent :

- `login(value)`
- `reload_usb_check()`
- `usb_list()`
- `init_usb(device, password)`
- `get_pswtable_data()`
- `update_password_data(data)`

`Api.usb` vaut `None` ou le chemin du dossier `USBSecurity`.

Apres un login reussi, `Api.pswctrl.secret` contient la
`PasswordManagerKey` encodee en base64. Cette cle sert a dechiffrer et
rechiffrer `PasswordManager.Archer`.

## Fichiers sur la cle USB

Le backend attend ou cree :

```text
USBSecurity/
  USBKey.rin
  PasswordManager.Archer
```

`USBKey.rin` stocke un payload chiffre contenant `PasswordManagerKey`.

`PasswordManager.Archer` stocke un payload chiffre de forme :

```json
{
  "sites": [
    {
      "url": "https://exemple.com",
      "password": "secret"
    }
  ]
}
```

## Etat courant

Branche :

- detection USB Windows et Linux/POSIX ;
- creation des deux fichiers applicatifs ;
- login Windows et Linux/POSIX ;
- lecture du tableau des mots de passe ;
- ajout persistant d'entrees.

A consolider :

- suppression des logs sensibles ;
- tests automatises ;
- edition persistante d'une entree existante ;
- remplacement des `print` par un logging controle ;
- nettoyage du module legacy `Key/key-read&write/USB.py`.
