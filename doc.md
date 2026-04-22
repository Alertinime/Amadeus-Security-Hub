# Documentation technique du depot

Cette documentation decrit l'etat des fichiers presents dans le depot au moment de l'analyse.
Elle ne decrit pas d'eventuelles modifications non sauvegardees dans l'IDE ni des changements
runtime non persistants.

## 1. Vue d'ensemble

Le projet est une application desktop Python basee sur `pywebview`.

Le backend choisit au demarrage une page HTML parmi :

- `Nokey.html` si aucun support USB n'est detecte
- `CreateKey.html` si un support USB existe mais qu'aucune cle Security Hub n'est trouvee
- `Login.html` si un fichier `USBSecurity/USBKey.rin` est detecte

Le frontend est un ensemble de fichiers HTML, CSS et JavaScript statiques charges dans
la fenetre `pywebview`. Le JavaScript appelle les methodes Python exposees par `js_api`.

Invariant important observe dans le code courant :

- `Api.self.usb` contient soit `None`, soit le chemin absolu du dossier `USBSecurity`
- `Api.self.usb` ne represente plus l'objet USB brut

## 2. Structure utile du depot

### Backend Python

- `app/main.py`
- `app/Backend/OSManagement.py`
- `app/Backend/WebviewAPI.py`
- `app/Backend/Cryptography/PasswordManager.py`
- `app/Backend/Key/KeyListingWin.py`
- `app/Backend/Key/KeyListingLinux.py`
- `app/Backend/Key/key-read&write/USB.py`

### Frontend charge par pywebview

- `app/Frontend/Html/Nokey.html`
- `app/Frontend/Html/CreateKey.html`
- `app/Frontend/Html/Login.html`
- `app/Frontend/Html/securityhub.css`
- `app/Frontend/Html/JS/common.js`
- `app/Frontend/Html/JS/create_key.js`
- `app/Frontend/Html/JS/login.js`

### Runtime

- `runtime/requirements.txt`

## 3. Flux global d'execution

### Demarrage

`app/main.py` :

- instancie une seule fois `Api()`
- detecte l'OS via `OSspliter().get_current_os()`
- sous Windows :
  - instancie `key_listing_win`
  - appelle `check_for_key()`
  - si des lecteurs USB existent, appelle `check_for_security_key(...)`
  - si une cle est trouvee, renseigne `api.usb` avec le dossier `USBSecurity`
- sous POSIX :
  - instancie `key_listening_linux`
  - appelle `list_usb()`
  - si des supports existent, appelle `check_for_security_key(...)`
  - si une cle est trouvee, renseigne `api.usb` avec le dossier `USBSecurity`
- ouvre ensuite la fenetre `pywebview` sur `Nokey.html`, `CreateKey.html` ou `Login.html`
- sous POSIX, appelle `cleanup_managed_mounts()` a la fermeture

### Choix d'ecran

- `key == False` : `Frontend/Html/Nokey.html`
- `usb == False` : `Frontend/Html/CreateKey.html`
- sinon : `Frontend/Html/Login.html`

## 4. Backend Python

### `app/Backend/OSManagement.py`

La classe `OSspliter` expose une seule methode :

- `get_current_os()` retourne `os.name`

Valeurs attendues dans le depot :

- `nt` pour Windows
- `posix` pour Linux / POSIX

### `app/Backend/WebviewAPI.py`

Role :

- exposer les fonctions Python appelees depuis le frontend
- centraliser l'etat `self.usb`

Etat interne :

- `self.usb` vaut `None` au depart
- quand une cle est confirmee, `self.usb` vaut le chemin du dossier `USBSecurity`

Methodes exposees :

- `login(value)`
  - sous Windows, appelle `key_listing_win.login_usb(self.usb, value)`
  - affiche `Login result: ...`
  - ne retourne pas explicitement le resultat au frontend
  - sous POSIX, le code appelle `key.login_usb(value)` alors que `key` n'est pas defini
  - il n'existe pas de methode de login dans `KeyListingLinux.py`

- `check_os()`
  - retourne `os.name`

- `set_window(window)`
  - stocke la fenetre, mais cette reference n'est pas exploitee ailleurs

- `reload_usb_check()`
  - remet `self.usb = None` au debut
  - refait une detection USB complete
  - si une cle est trouvee, stocke le chemin de `USBSecurity` dans `self.usb`
  - retourne seulement `Nokey.html`, `CreateKey.html` ou `Login.html`
  - ne change pas elle-meme la page affichee

- `usb_list()`
  - sous Windows, retourne une liste d'objets `{id, name}`
  - sous POSIX, retourne une liste de valeurs `usb["product"]`

- `init_usb(device, password)`
  - remet `self.usb = None` au debut
  - reliste les supports USB
  - initialise le support selectionne
  - verifie ensuite l'existence de `USBKey.rin`
  - si la creation est confirmee, stocke le dossier `USBSecurity` dans `self.usb`
  - sinon retourne `False`

Points de vigilance visibles :

- `login()` n'est complet que cote Windows
- la navigation frontend n'est pas pilotee a partir des valeurs renvoyees par `reload_usb_check()`

### `app/Backend/Cryptography/PasswordManager.py`

Role :

- deriver des cles depuis le mot de passe utilisateur
- generer un sel aleatoire

Methodes :

- `kdf(mdp, salt)`
  - utilise `Argon2id`
  - derive 32 octets
  - `iterations=1`
  - `memory_cost=2_097_152`
  - `lanes=8`

- `HKDF(key_material, salt, info, length)`
  - derive une nouvelle cle avec `HKDF(SHA256)`
  - le `salt` de HKDF est `sha256(salt.encode()).digest()`

- `create_salt()`
  - retourne `os.urandom(16)`

Remarque :

- la classe declare `_init_` au lieu de `__init__`

### `app/Backend/Key/KeyListingWin.py`

Role :

- detecter les lecteurs USB Windows
- trouver `USBSecurity/USBKey.rin`
- initialiser une cle Security Hub
- tenter une authentification de login Windows

Methodes importantes :

- `check_for_key()`
  - parcourt `Win32_LogicalDisk()`
  - conserve les volumes avec `DriveType == 2`

- `_get_disk_drive(usb)`
  - remonte de `Win32_LogicalDisk` vers `Win32_DiskDrive`

- `_get_usb_root(usb)`
  - derive la racine montee du lecteur, par exemple `E:\`

- `get_security_dir(usb)`
  - retourne le dossier `E:\USBSecurity`

- `_security_key_path(usb)`
  - retourne `E:\USBSecurity\USBKey.rin`

- `list_usb_for_frontend()`
  - retourne une liste de dictionnaires `{id, name}`

- `check_for_security_key(usbl)`
  - teste l'existence de `USBKey.rin`
  - retourne le premier objet WMI correspondant ou `False`

- `initialize_security_key(usb, password)`
  - derive une cle Argon2id depuis le mot de passe et un sel aleatoire
  - derive ensuite une cle HKDF liee au serial USB
  - appelle `make_master_file(...)`

- `make_master_file(usb, master_key, saltpasw)`
  - cree `USBSecurity`
  - chiffre un payload vide `{}` avec `AESGCM`
  - utilise le serial USB comme AAD
  - ecrit un JSON dans `USBKey.rin`

- `get_usb_from_security_dir(security_dir)`
  - convertit un chemin `E:\USBSecurity` vers l'objet `Win32_LogicalDisk` associe

- `login_usb(usb, password)`
  - attend en entree un chemin de dossier `USBSecurity`
  - convertit ce chemin en objet WMI avec `get_usb_from_security_dir(...)`
  - relit `USBKey.rin`
  - rederive la cle de decryption a partir du mot de passe et du serial USB
  - tente `aesgcm.decrypt(...)`

Point important visible dans le code enregistre :

- `login_usb()` reutilise ensuite la variable `usb` comme si c'etait encore un chemin
  lorsqu'il construit `os.path.join(usb, "USBKey.rin")`
- le flux voulu est identifiable, mais l'implementation melange dans la meme variable
  un chemin de dossier et un objet WMI

### `app/Backend/Key/KeyListingLinux.py`

Role :

- enumerer les supports USB sous POSIX
- monter temporairement les partitions non montees pour inspection
- detecter `USBSecurity/USBKey.rin`
- initialiser une cle Security Hub

Methodes importantes :

- `list_with_lsusb()`
  - execute `lsusb`
  - n'est pas utilisee ailleurs

- `_find_block_devices(devpath)`
  - collecte les peripheriques bloc associes a une entree `/sys/bus/usb/devices`

- `_mounted_points_for(block_names)`
  - relit `/proc/mounts`
  - retourne les points de montage correspondants

- `_find_partitions(block_names)`
  - determine les partitions reelles a partir des blocs trouves

- `_mount_block_device(block_name)`
  - utilise `udisksctl mount`

- `_unmount_block_device(block_name)`
  - utilise `udisksctl unmount`

- `_security_key_path(mount_point)`
  - construit `<mount>/USBSecurity/USBKey.rin`

- `get_security_dir(usb)`
  - retourne le dossier `USBSecurity` a partir de `security_key_path`, `security_mount`
    ou du premier point de montage connu

- `_ensure_mounts(usb)`
  - reutilise les montages existants
  - sinon tente de monter les partitions
  - memorise les montages realises par l'application dans `mounted_by_app`

- `_release_usb_mounts(usb)`
  - demonte uniquement les partitions montees par l'application pour ce support

- `cleanup_managed_mounts()`
  - demonte a la fermeture les partitions que l'application a elle-meme laissees montees

- `list_usb()`
  - parcourt `/sys/bus/usb/devices`
  - lit `idVendor`, `idProduct`, `manufacturer`, `product`, `serial`
  - ajoute `sysname`, `blocks`, `partitions`, `mounts`
  - ignore les entrees sans peripherique bloc

- `check_for_security_key(usbl)`
  - monte les supports si necessaire
  - cherche `USBKey.rin`
  - si trouve :
    - renseigne `security_mount`
    - renseigne `security_key_path`
    - retourne le dictionnaire USB
  - si rien n'est trouve sur un support monte par l'application :
    - le support est redemonte

- `initialize_security_key(usb, password)`
  - assure un montage exploitable
  - derive une cle avec `PasswordManager`
  - appelle `make_master_file(...)`
  - retourne ensuite `bool(usbs_dir and salt and key)`

- `make_master_file(...)`
  - ecrit le JSON `USBKey.rin` dans `USBSecurity`

Points de vigilance visibles :

- il n'existe pas de methode `login_usb()` sous Linux
- `initialize_security_key()` ne retourne pas directement le resultat de `make_master_file(...)`

### `app/Backend/Key/key-read&write/USB.py`

Ce module legacy n'est pas branche au flux principal.

Il contient :

- une logique Windows historique de creation et lecture de `USBKey.rin`
- une saisie du mot de passe via Tkinter
- des hypotheses specifiques a Windows (`Caption`, `VolumeSerialNumber`, `ctypes.windll`)

Remarques visibles :

- `is_usb()` utilise `self.usb.caption` alors que le reste du fichier utilise plutot `Caption`
- `default_backend` est importe mais non utilise

### `app/test.py`

Le fichier est vide.

## 5. Frontend

### `app/Frontend/Html/JS/common.js`

Role :

- fournir un acces commun a l'API `pywebview`

Fonctions :

- `getApi()`
  - retourne `window.pywebview.api`
  - sinon `window.api`
  - sinon `null`

- `callApi(method, ...args)`
  - verifie l'existence de la methode
  - appelle la methode de facon asynchrone
  - journalise et relance les erreurs

### `app/Frontend/Html/JS/login.js`

Role :

- intercepter le submit du formulaire de login
- envoyer le mot de passe a `api.login(...)`

Comportement :

- ecoute `DOMContentLoaded`
- recupere `#master-password`
- appelle `callApi('login', value)` ou `api.login(value)`
- ne pilote pas la navigation apres succes ou echec

### `app/Frontend/Html/JS/create_key.js`

Role :

- lister les supports USB
- ouvrir une popup de saisie du mot de passe maitre
- lancer `init_usb(device, password)`

Comportement principal :

- impose une regex de mot de passe :
  - minimum 12 caracteres
  - une minuscule
  - une majuscule
  - un chiffre
  - un symbole
- `usb_list()` alimente dynamiquement la liste des supports
- `init_usb()` est appelee avec l'identifiant du support selectionne
- en cas de succes, la popup se ferme
- en cas d'echec, un message d'erreur est affiche

Limite visible :

- le bouton `Retour` appelle `reload_usb_check()` ou `go_back()`, mais la valeur renvoyee
  n'est pas utilisee pour changer de page

### `app/Frontend/Html/Nokey.html`

Role :

- afficher l'absence de support USB detecte

Limite visible :

- la page charge `JS/nokey.js`
- ce fichier n'existe pas dans le depot

### `app/Frontend/Html/CreateKey.html`

Role :

- afficher la liste des supports USB detectes
- afficher la popup d'initialisation du mot de passe maitre

Remarque :

- le texte annonce que toutes les donnees seront effacees, mais aucun code de formatage
  ou d'effacement complet n'apparait dans le depot

### `app/Frontend/Html/Login.html`

Role :

- afficher le formulaire de mot de passe maitre

Remarque :

- le formulaire declare `action="/unlock"`, mais aucun backend HTTP n'existe
- le submit est intercepte par `login.js`

## 6. Dependances observees

`runtime/requirements.txt` contient :

- `argon2-cffi`
- `cryptography`
- `wmi`
- `pywebview`

Dependances visibles dans le code :

- `pywebview` pour la fenetre desktop et le bridge JS/Python
- `cryptography` pour Argon2id, HKDF et AES-GCM
- `argon2-cffi` via `argon2.low_level` dans le module legacy `USB.py`
- `wmi` pour la detection Windows
- `tkinter` dans le module legacy `USB.py`

## 7. Resume d'etat

Ce qui est raccorde dans le depot :

- detection Windows et POSIX des supports USB
- choix initial de la page affichee
- creation de `USBKey.rin` sous Windows et POSIX
- stockage de `Api.self.usb` comme chemin du dossier `USBSecurity`
- envoi du mot de passe de login au backend via `pywebview`

Ce qui reste incomplet ou incoherent dans l'etat enregistre :

- le login POSIX n'est pas implemente
- le login Windows melange actuellement chemin `USBSecurity` et objet WMI dans `login_usb()`
- `reload_usb_check()` renvoie un nom de page mais le frontend ne navigue pas a partir de ce retour
- `Nokey.html` reference un script absent
- le module legacy `USB.py` n'est pas integre au flux principal
