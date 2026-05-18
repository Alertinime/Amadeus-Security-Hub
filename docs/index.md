# Amadeus Security Hub - Documentation technique

Etat documente le 18 mai 2026.

Cette documentation decrit l'etat du code present dans le depot. Elle ne
decrit pas un etat runtime externe, ni des fichiers generes sur une cle USB.

## Documents principaux

- [Rapport d'architecture](architecture.md)
- [Rapport d'avancement](avancement.md)
- [Backend](backend.md)
- [Frontend](frontend.md)
- [Runtime Python](runtime.md)
- [Gestion des cles USB](key-management.md)
- [Creation des cles](key-create.md)
- [Lecture / ecriture legacy](key-read-write-legacy.md)

## Vue d'ensemble

Amadeus Security Hub est une application desktop locale construite avec
Python, `pywebview` et un frontend statique HTML/CSS/JavaScript.

Le principe general est le suivant :

1. `app/main.py` detecte le systeme d'exploitation.
2. Le backend liste les supports USB disponibles.
3. L'application cherche un dossier `USBSecurity` contenant `USBKey.rin`.
4. Selon l'etat detecte, `pywebview` ouvre l'une des pages suivantes :
   - `Nokey.html` si aucun support USB n'est detecte.
   - `CreateKey.html` si un support USB existe mais aucune cle Security Hub
     n'est trouvee.
   - `Login.html` si une cle Security Hub existe.
5. Apres login, le frontend ouvre `Dashboard.html`.
6. Le dashboard lit et met a jour `PasswordManager.Archer`, le conteneur
   chiffre des couples site / mot de passe.

## Structure du depot

```text
app/
  main.py
  Backend/
    OSManagement.py
    WebviewAPI.py
    WebviewAPIWindows.py
    WebviewAPILinux.py
    Controller/
      AMHSPswdCtrl.py
    Cryptography/
      PasswordManager.py
      SecretManager.py
    Key/
      KeyListingWin.py
      KeyListingLinux.py
      key-create/
      key-read&write/
  Frontend/
    Html/
      Nokey.html
      CreateKey.html
      Login.html
      Dashboard.html
      Settings.html
      securityhub.css
      JS/
        common.js
        create_key.js
        login.js
        dashboard.js
runtime/
  requirements.txt
docs/
  index.md
  architecture.md
  avancement.md
  backend.md
  frontend.md
  runtime.md
  key-management.md
  key-create.md
  key-read-write-legacy.md
```

## Contrats applicatifs

### Etat backend partage

- `Api.usb` contient `None` ou le chemin absolu du dossier `USBSecurity`.
- `Api.pswctrl` est une instance de `Pswctrl`.
- Apres login, `Pswctrl.secret` contient la `PasswordManagerKey` encodee en
  base64.

### Fichiers attendus sur la cle

```text
<mount-or-drive>/USBSecurity/
  USBKey.rin
  PasswordManager.Archer
```

`USBKey.rin` contient un package JSON chiffre avec une cle derivee du mot de
passe maitre. Son payload contient `PasswordManagerKey`.

`PasswordManager.Archer` contient un package JSON chiffre avec
`PasswordManagerKey`. Son payload clair attendu est :

```json
{
  "sites": [
    {
      "domaine": "exemple.com",
      "password": "secret"
    }
  ]
}
```

### API exposee au frontend

Les classes `WebviewAPIWindows.Api` et `WebviewAPILinux.Api` exposent
actuellement :

- `login(value)` : verifie le mot de passe maitre et charge
  `PasswordManagerKey` en memoire.
- `reload_usb_check()` : relance la detection USB et retourne une page cible.
- `usb_list()` : retourne les supports USB affichables.
- `init_usb(device, password)` : initialise une cle Security Hub.
- `get_pswtable_data()` : retourne la liste `sites` du conteneur chiffre.
- `update_password_data(data)` : ajoute des entrees et reecrit le conteneur
  chiffre.

### Extension navigateur

L'extension Chromium communique avec l'application locale via Native Messaging.
Sous Windows, le host natif relaie les messages vers le serveur named pipe
`\\.\pipe\amadeus-security-hub`.

Flux :

```text
content.js
  -> background.js
  -> NativesPipeline.py
  -> WinNamedPipes.py
  -> WinNamedPipesHandler.py
  -> Pswctrl
```

Messages principaux :

- `Ask` : recupere le mot de passe associe a un domaine via
  `Pswctrl.getpsswd(path, domaine)`.
- `AddEntry` : ajoute ou remplace l'entree d'un domaine via
  `Pswctrl.addentry(path, domaine, password)`.

## Etat fonctionnel court

Fonctionnel ou branche :

- detection USB Windows et Linux/POSIX ;
- creation de `USBKey.rin` ;
- creation de `PasswordManager.Archer` ;
- login Windows ;
- login Linux/POSIX ;
- lecture du tableau de mots de passe apres login ;
- ajout de nouvelles entrees depuis le dashboard.
- recuperation et ajout de mots de passe depuis l'extension Chromium sous
  Windows.

Incomplet ou a consolider :

- edition d'une ligne existante dans le dashboard non persistante ;
- page `Nokey.html` reference `JS/nokey.js`, absent du depot ;
- `reload_usb_check()` retourne une page mais le frontend ne navigue pas encore
  avec ce retour ;
- `CreateKey.html` annonce un effacement total de la cle, mais le backend cree
  seulement le dossier et les fichiers Security Hub ;
- logs de debug sensibles presents dans les flux de login ;
- absence de tests automatises.

## Dependances

`runtime/requirements.txt` :

- `argon2-cffi`
- `cryptography`
- `wmi`
- `pywebview`

Dependances systeme implicites :

- Windows : WMI disponible.
- Linux/POSIX : `/sys/bus/usb/devices`, `/proc/mounts`, `udisksctl` pour les
  montages non deja disponibles.
