# Rapport d'architecture

Etat documente le 18 mai 2026.

## 1. Synthese

Amadeus Security Hub est une application desktop locale. Le backend Python
controle la detection USB, la creation de fichiers chiffres, le login et les
operations sur le gestionnaire de mots de passe. Le frontend est un ensemble de
pages HTML statiques chargees dans une fenetre `pywebview`.

L'architecture est simple et directe :

```text
Utilisateur
  -> Pages HTML/JS
  -> pywebview bridge
  -> Api Windows ou Api Linux
  -> Services USB / crypto / controleur password manager
  -> Fichiers chiffres sur cle USB
```

Une brique extension web existe en complement du frontend desktop :

```text
Extension navigateur
  -> Native Messaging
  -> serveur IPC local
  -> AMHSPswdCtrl / Pswctrl
  -> PasswordManager.Archer
```

Dans ce modele, l'extension ne dialogue pas directement avec les fichiers de la
cle USB. Elle passe par le host Native Messaging puis par le serveur named pipe
Windows de l'application, qui delegue les operations de lecture, ajout et mise
a jour au controleur `AMHSPswdCtrl.py`.

Diagramme global :

```text
                         +----------------------+
                         | Utilisateur desktop  |
                         +----------+-----------+
                                    |
                                    v
                         +----------------------+
                         | Pages HTML / JS      |
                         +----------+-----------+
                                    |
                                    v
                         +----------------------+
                         | Bridge pywebview     |
                         +----------+-----------+
                                    |
                                    v
                         +----------------------+
                         | API Python selon OS  |
                         +----------+-----------+
                                    |
                 +------------------+------------------+
                 |                                     |
                 v                                     v
      +-----------------------+             +----------------------+
      | WebviewAPIWindows.Api |             | WebviewAPILinux.Api  |
      +-----------+-----------+             +----------+-----------+
                  |                                    |
                  v                                    v
      +-----------------------+             +----------------------+
      | KeyListingWin         |             | KeyListingLinux      |
      +-----------+-----------+             +----------+-----------+
                  |                                    |
                  +------------------+-----------------+
                                     |
                                     v
                         +----------------------+
                         | Crypto               |
                         | PasswordManager      |
                         | SecretManager        |
                         +----------+-----------+
                                    |
                                    v
                         +----------------------+
                         | Cle USB              |
                         | USBSecurity/         |
                         +----------+-----------+
                                    |
                 +------------------+------------------+
                 |                                     |
                 v                                     v
      +-----------------------+             +----------------------+
      | USBKey.rin            |             | PasswordManager.     |
      |                       |             | Archer               |
      +-----------------------+             +----------+-----------+
                                                        ^
                                                        |
                         +----------------------+       |
                         | AMHSPswdCtrl.py      |-------+
                         | Pswctrl              |
                         +----------+-----------+
                                    ^
                                    |
                 +------------------+------------------+
                 |                                     |
                 v                                     v
      +-----------------------+             +----------------------+
      | Dashboard desktop     |             | Serveur IPC Windows  |
      | via API pywebview     |             +----------+-----------+
      +-----------------------+                        ^
                                                       |
                                            +----------+-----------+
                                            | Extension navigateur |
                                            +----------------------+
```

## 2. Point d'entree

Le point d'entree est `app/main.py`.

Responsabilites :

- detecter l'OS via `OSspliter().get_current_os()`;
- importer l'implementation backend adaptee :
  - `WebviewAPIWindows.Api` et `KeyListingWin.key_listing_win` sous Windows ;
  - `WebviewAPILinux.Api` et `KeyListingLinux.key_listening_linux` sous POSIX ;
- chercher les supports USB ;
- chercher une cle Security Hub deja initialisee ;
- renseigner `api.usb` avec le chemin du dossier `USBSecurity` quand une cle
  est trouvee ;
- ouvrir la page initiale avec `webview.create_window(...)`;
- nettoyer les montages geres par l'application a la fermeture sous POSIX.

Decision de page :

```text
aucun support USB     -> Frontend/Html/Nokey.html
support sans cle      -> Frontend/Html/CreateKey.html
cle Security Hub      -> Frontend/Html/Login.html
login reussi          -> Frontend/Html/Dashboard.html
```

## 3. Backend

### 3.1 Selection d'API

`app/Backend/WebviewAPI.py` est une facade d'import. Elle expose `Api` depuis
l'implementation specifique a l'OS courant.

Les vraies implementations sont :

- `app/Backend/WebviewAPIWindows.py`
- `app/Backend/WebviewAPILinux.py`

Elles ont un contrat similaire pour le frontend.

### 3.2 API pywebview

Etat interne commun :

- `self.usb` : chemin du dossier `USBSecurity` ou `None`.
- `self.window` : reference optionnelle a la fenetre.
- `self.pswctrl` : instance de `Pswctrl`, utilisee apres login.

Methodes exposees :

- `login(value)`
  - derive et verifie la cle maitre depuis `USBKey.rin`;
  - recupere `PasswordManagerKey`;
  - stocke cette cle dans `Pswctrl.secret`;
  - retourne `True` ou `False`.

- `reload_usb_check()`
  - relance la detection USB ;
  - met a jour `self.usb` ;
  - retourne `Nokey.html`, `CreateKey.html` ou `Login.html`.

- `usb_list()`
  - retourne une liste de supports affichables par `CreateKey.html`.

- `init_usb(device, password)`
  - initialise le support selectionne ;
  - cree `USBSecurity/USBKey.rin` ;
  - cree `USBSecurity/PasswordManager.Archer` ;
  - met a jour `self.usb` si la creation est confirmee.

- `get_pswtable_data()`
  - dechiffre `PasswordManager.Archer` via `Pswctrl` ;
  - retourne la liste `sites`.

- `update_password_data(data)`
  - dechiffre le conteneur existant ;
  - ajoute `data["sites"]` a la liste existante ;
  - rechiffre le fichier ;
  - retourne la liste complete mise a jour.

### 3.3 Detection et gestion USB Windows

Fichier : `app/Backend/Key/KeyListingWin.py`

Responsabilites :

- enumerer les volumes amovibles via WMI `Win32_LogicalDisk`;
- retrouver des informations de nommage via associations WMI ;
- construire les chemins `USBSecurity`, `USBKey.rin` et
  `PasswordManager.Archer`;
- initialiser une cle ;
- executer le login ;
- mapper un dossier `USBSecurity` vers son objet WMI.

Contrat de listing frontend :

```json
[
  {
    "id": "E:",
    "name": "Nom du support"
  }
]
```

### 3.4 Detection et gestion USB Linux/POSIX

Fichier : `app/Backend/Key/KeyListingLinux.py`

Responsabilites :

- enumerer les peripheriques USB depuis `/sys/bus/usb/devices`;
- detecter les blocs et partitions associes ;
- lire les montages depuis `/proc/mounts`;
- monter temporairement avec `udisksctl` si necessaire ;
- chercher `USBSecurity/USBKey.rin`;
- initialiser la cle ;
- executer le login ;
- nettoyer les montages que l'application a elle-meme crees.

Contrat de listing frontend :

```json
[
  {
    "id": "serial-ou-sysname",
    "name": "Nom du support"
  }
]
```

### 3.5 Crypto

Fichiers :

- `app/Backend/Cryptography/PasswordManager.py`
- `app/Backend/Cryptography/SecretManager.py`

`PasswordManager` :

- derive une cle de 32 octets avec `Argon2id`;
- derive une cle applicative avec `HKDF(SHA256)`;
- genere un sel aleatoire de 16 octets.

Parametres Argon2id observes :

- `length=32`
- `iterations=1`
- `memory_cost=2_097_152`
- `lanes=8`

`SecretManager` :

- genere des cles aleatoires de 32 octets ;
- genere des sels de 32 octets ;
- genere des AAD de 16 octets ;
- contient encore un dictionnaire de secrets generique, peu utilise par le flux
  principal actuel.

### 3.6 Controleur du gestionnaire de mots de passe

Fichier : `app/Backend/Controller/AMHSPswdCtrl.py`

`Pswctrl` gere `PasswordManager.Archer`.

Responsabilites :

- stocker en memoire la `PasswordManagerKey` base64 apres login ;
- lire le package JSON ;
- recuperer l'AAD depuis le header ;
- dechiffrer avec `AESGCM(base64.b64decode(self.secret))` ;
- ajouter de nouvelles entrees `sites` ;
- rechiffrer le fichier avec un nouveau nonce ;
- retourner les donnees dechiffrees au frontend.

Format attendu :

```json
{
  "header": {
    "version": 1,
    "type": "security-hub-password-manager",
    "cipher": "AES-256-GCM",
    "key_source": "PasswordManagerKey",
    "payload_format": "site-password-list",
    "nonce": "...",
    "aad": "..."
  },
  "payload": "..."
}
```

## 4. Frontend

Le frontend n'utilise ni bundler ni serveur Node. Les pages sont chargees
directement par `pywebview`.

### 4.1 Pages

- `Nokey.html` : absence de support USB.
- `CreateKey.html` : choix d'un support et saisie du mot de passe maitre.
- `Login.html` : deblocage de la cle.
- `Dashboard.html` : consultation et ajout d'entrees.
- `Settings.html` : page placeholder de configuration.

### 4.2 Scripts

`common.js` :

- expose `getApi()`;
- expose `callApi(method, ...args)`;
- expose `goToPage(page)`.

`create_key.js` :

- charge `usb_list()`;
- valide un mot de passe maitre avec une regex locale ;
- appelle `init_usb(device, password)`;
- ferme la popup si l'initialisation reussit.

`login.js` :

- intercepte le submit ;
- appelle `login(value)`;
- ouvre `Dashboard.html` si le backend retourne `true`.

`dashboard.js` :

- charge les sites via `get_pswtable_data()`;
- affiche la liste ;
- ouvre une modale d'ajout ;
- appelle `update_password_data({ sites: [...] })`;
- met a jour le tableau avec la reponse backend.

### 4.3 Extension web

L'architecture integre une extension navigateur pour interagir avec le
gestionnaire de mots de passe depuis le web.

Flux de responsabilite :

```text
Extension web
  -> content script
  -> background service worker
  -> Native Messaging host
  -> serveur named pipe Windows
  -> appel a AMHSPswdCtrl / Pswctrl
  -> lecture ou modification de PasswordManager.Archer
  -> reponse au navigateur
```

Le host Native Messaging et le serveur IPC servent de couche d'isolation entre
le navigateur et le backend interne. Le named pipe n'est demarre qu'apres login
sur Windows, quand `Pswctrl.secret` est disponible en memoire.

`Pswctrl` reste le point d'acces metier au fichier chiffre :

- lecture des donnees via `get_file_data(...)` ;
- ajout de nouvelles donnees via `update_file_with_new_data(...)` ;
- lecture extension via `getpsswd(path, domaine)` ;
- ajout/remplacement extension via `addentry(path, domaine, password)` ;
- chiffrement et dechiffrement de `PasswordManager.Archer`.

## 5. Flux principaux

### 5.1 Creation de cle

```text
CreateKey.html
  -> create_key.js
  -> api.usb_list()
  -> utilisateur selectionne un support
  -> api.init_usb(device, password)
  -> KeyListing*.initialize_security_key(...)
  -> PasswordManager.kdf(...)
  -> PasswordManager.HKDF(...)
  -> creation USBKey.rin
  -> creation PasswordManager.Archer
```

### 5.2 Login

```text
Login.html
  -> login.js
  -> api.login(password)
  -> KeyListing*.login_usb(api.usb, password)
  -> lecture USBKey.rin
  -> derivation Argon2id + HKDF
  -> dechiffrement AES-GCM
  -> extraction PasswordManagerKey
  -> Pswctrl.set_secret(...)
  -> Dashboard.html
```

### 5.3 Lecture du dashboard

```text
Dashboard.html
  -> dashboard.js
  -> api.get_pswtable_data()
  -> Pswctrl.get_file_data(api.usb)
  -> lecture PasswordManager.Archer
  -> dechiffrement AES-GCM avec PasswordManagerKey
  -> retour sites[]
```

### 5.4 Ajout d'une entree

```text
Dashboard.html
  -> dashboard.js
  -> api.update_password_data({ sites: [...] })
  -> Pswctrl.concatenate_file_and_new_data(...)
  -> Pswctrl.encrypt_file(...)
  -> retour sites[] mis a jour
```

### 5.5 Extension web et IPC local

```text
Extension navigateur
  -> Native Messaging
  -> WinNamedPipes.py
  -> WinNamedPipesHandler.py
  -> Pswctrl.getpsswd(...) ou Pswctrl.addentry(...)
  -> PasswordManager.Archer
  -> reponse a l'extension
```

Ce flux est une extension de l'architecture desktop. La couche IPC ne duplique
pas la logique de chiffrement : elle reutilise `Pswctrl`, qui conserve la
responsabilite de lire, dechiffrer, modifier et rechiffrer le conteneur de mots
de passe.

## 6. Points d'attention architecturaux

- Le frontend peut ouvrir `Dashboard.html` directement, mais sans login
  `Pswctrl.secret` reste vide et le dechiffrement echoue.
- Les editions de lignes dans `dashboard.js` modifient l'etat local, mais ne
  rappellent pas encore le backend pour persister.
- `Nokey.html` charge `JS/nokey.js`, absent du depot.
- Le bouton retour de `CreateKey.html` appelle `reload_usb_check()` mais ignore
  le nom de page retourne.
- Des logs affichent des donnees sensibles pendant le login, dont des elements
  de derivation et parfois la cle dechiffree.
- Le module `Key/key-read&write/USB.py` est legacy : il utilise une ancienne
  structure de fichier et Tkinter, et n'est pas branche au flux principal.
- Le code contient plusieurs noms et commentaires avec encodage altere dans
  certains fichiers frontend historiques.

## 7. Frontieres techniques

Le flux desktop actuel n'est pas une application web client/serveur. La
communication desktop se fait via le bridge `pywebview` entre JS et objets
Python.

Pour l'extension web, la frontiere supplementaire est Native Messaging puis IPC
local. Sous Windows, le serveur named pipe `\\.\pipe\amadeus-security-hub`
sert d'interface entre l'extension navigateur et `AMHSPswdCtrl.py`. Cette
couche reste fine et delegue les operations sensibles au controleur existant.

Le stockage persistant applicatif principal est la cle USB, via deux fichiers
JSON chiffres. La memoire Python contient la cle de session seulement apres un
login reussi.
