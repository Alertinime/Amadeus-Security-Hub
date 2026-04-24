# Documentation technique du depot

Cette documentation decrit l'etat sauvegarde du depot.
Elle ne decrit pas des modifications non enregistrees dans l'IDE ni l'etat runtime en memoire.

## 1. Vue d'ensemble

Le projet est une application desktop Python basee sur `pywebview`.

Au demarrage, le backend choisit une page HTML parmi :

- `Nokey.html` si aucun support USB n'est detecte
- `CreateKey.html` si un support USB existe mais qu'aucune cle Security Hub n'est trouvee
- `Login.html` si un fichier `USBSecurity/USBKey.rin` est detecte

Apres authentification reussie, le frontend redirige vers `Dashboard.html`.

Invariant important observe dans le code courant :

- `Api.self.usb` contient soit `None`, soit le chemin absolu du dossier `USBSecurity`
- `Api.secret_manager` conserve en memoire les secrets de session pour l'instance `Api`

## 2. Structure utile du depot

### Backend Python

- `app/main.py`
- `app/Backend/OSManagement.py`
- `app/Backend/WebviewAPI.py`
- `app/Backend/Cryptography/PasswordManager.py`
- `app/Backend/Cryptography/SecretManager.py`
- `app/Backend/Key/KeyListingWin.py`
- `app/Backend/Key/KeyListingLinux.py`
- `app/Backend/Key/key-read&write/USB.py`

### Frontend charge par pywebview

- `app/Frontend/Html/Nokey.html`
- `app/Frontend/Html/CreateKey.html`
- `app/Frontend/Html/Login.html`
- `app/Frontend/Html/Dashboard.html`
- `app/Frontend/Html/Settings.html`
- `app/Frontend/Html/securityhub.css`
- `app/Frontend/Html/JS/common.js`
- `app/Frontend/Html/JS/create_key.js`
- `app/Frontend/Html/JS/login.js`
- `app/Frontend/Html/JS/dashboard.js`

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

### Login frontend

- `Login.html` charge `login.js`
- `login.js` appelle `api.login(...)`
- si le backend renvoie `true`, le frontend navigue vers `Dashboard.html`
- sinon un message d'erreur est affiche dans la page de login

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
- conserver en memoire certains secrets de session via `SecretManager`

Etat interne :

- `self.usb` vaut `None` au depart
- `self.secret_manager` est une instance de `SecretManager`
- quand une cle est confirmee, `self.usb` vaut le chemin du dossier `USBSecurity`

Methodes exposees :

- `login(value)`
  - sous Windows, appelle `key_listing_win.login_usb(self.usb, value)`
  - en cas de succes, recupere `PasswordManagerKey` depuis `USBKey.rin`
  - stocke cette valeur dans `self.secret_manager` sous la cle `PasswordManagerKey`
  - retourne un booleen exploitable par le frontend
  - sous POSIX, le flux est prepare pour un `login_usb(...)`, mais `KeyListingLinux.py` n'expose pas encore cette methode

- `check_os()`
  - retourne `os.name`

- `set_window(window)`
  - stocke la fenetre, mais cette reference n'est pas exploitee ailleurs

- `reload_usb_check()`
  - remet `self.usb = None` au debut
  - refait une detection USB complete
  - si une cle est trouvee, stocke le chemin de `USBSecurity` dans `self.usb`
  - retourne `Nokey.html`, `CreateKey.html` ou `Login.html`
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

- le login complet n'existe actuellement que cote Windows
- `SecretManager` stocke les secrets en memoire mais n'expose pas encore de getter/clear explicite

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

### `app/Backend/Cryptography/SecretManager.py`

Role :

- generer des secrets aleatoires
- stocker des secrets en memoire pour la session courante

Methodes :

- `generate_random_key()`
  - retourne `os.urandom(32)` soit 32 octets / 256 bits

- `store_secret(key, secret)`
  - enregistre la valeur dans `self.secrets_dict`

- `generate_aad()`
  - retourne 16 octets aleatoires

### `app/Backend/Key/KeyListingWin.py`

Role :

- detecter les lecteurs USB Windows
- trouver `USBSecurity/USBKey.rin`
- initialiser une cle Security Hub
- creer un conteneur chiffre `PasswordManager.Archer`
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
  - genere une `PasswordManagerKey` aleatoire de 32 octets
  - chiffre un payload JSON contenant `PasswordManagerKey` avec `AESGCM`
  - utilise le serial USB comme AAD
  - ecrit un JSON dans `USBKey.rin`
  - cree aussi `PasswordManager.Archer`

- `_normalize_password_entries(passwords)`
  - valide et normalise une liste d'entrees `{url, password}`

- `make_passwordManager_file(usb, password_manager_key, passwords=None)`
  - ecrit `USBSecurity/PasswordManager.Archer`
  - chiffre un payload JSON du type `{"sites": [{"url": "...", "password": "..."}]}`
  - utilise `password_manager_key` comme cle AES-GCM
  - utilise le serial USB comme AAD

- `get_usb_from_security_dir(security_dir)`
  - convertit un chemin `E:\USBSecurity` vers l'objet `Win32_LogicalDisk` associe

- `login_usb(usb, password)`
  - attend en entree un chemin de dossier `USBSecurity`
  - relit `USBKey.rin`
  - rederive la cle de decryption a partir du mot de passe et du serial USB
  - dechiffre le payload JSON
  - extrait `PasswordManagerKey`
  - retourne `PasswordManagerKey` encodee en base64 ou `False`

### `app/Backend/Key/KeyListingLinux.py`

Role :

- enumerer les supports USB sous POSIX
- monter temporairement les partitions non montees pour inspection
- detecter `USBSecurity/USBKey.rin`
- initialiser une cle Security Hub
- creer un conteneur chiffre `PasswordManager.Archer`

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

- `make_master_file(...)`
  - ecrit `USBKey.rin`
  - y stocke `PasswordManagerKey` de facon chiffree
  - cree aussi `PasswordManager.Archer`

- `_normalize_password_entries(passwords)`
  - valide et normalise une liste d'entrees `{url, password}`

- `make_passwordManager_file(...)`
  - ecrit `PasswordManager.Archer`
  - chiffre un payload JSON de type `{"sites": [...]}`

Point de vigilance visible :

- il n'existe toujours pas de methode `login_usb()` sous Linux

### `app/Backend/Key/key-read&write/USB.py`

Ce module legacy n'est pas branche au flux principal.

Il contient :

- une logique Windows historique de creation et lecture de `USBKey.rin`
- une saisie du mot de passe via Tkinter
- des hypotheses specifiques a Windows (`Caption`, `VolumeSerialNumber`, `ctypes.windll`)

## 5. Frontend

### `app/Frontend/Html/JS/common.js`

Role :

- fournir un acces commun a l'API `pywebview`
- fournir un helper de navigation simple entre pages HTML

Fonctions :

- `getApi()`
  - retourne `window.pywebview.api`
  - sinon `window.api`
  - sinon `null`

- `callApi(method, ...args)`
  - verifie l'existence de la methode
  - appelle la methode de facon asynchrone
  - journalise et relance les erreurs

- `goToPage(page)`
  - change `window.location.href`

### `app/Frontend/Html/JS/login.js`

Role :

- intercepter le submit du formulaire de login
- envoyer le mot de passe a `api.login(...)`
- rediriger vers le dashboard en cas de succes

Comportement :

- ecoute `DOMContentLoaded`
- recupere `#master-password`
- appelle `callApi('login', value)` ou `api.login(value)`
- si le backend renvoie `true`, navigue vers `Dashboard.html`
- sinon affiche un message d'erreur dans la page

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

### `app/Frontend/Html/JS/dashboard.js`

Role :

- afficher la liste des sites et mots de passe dans le dashboard
- charger les sites via `get_the_sites()` si la methode existe
- permettre un ajout local manuel
- permettre l'edition locale d'une ligne

Comportement principal :

- `loadSites()` appelle `api.get_the_sites()` si la methode existe
- sinon le tableau reste dans un etat vide explicite
- `handleAddSite()` ajoute une entree locale `{url, password}`
- `settings-button` ouvre `Settings.html`

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
- afficher l'erreur de login en ligne

Remarque :

- le formulaire declare `action="/unlock"`, mais aucun backend HTTP n'existe
- le submit est intercepte par `login.js`

### `app/Frontend/Html/Dashboard.html`

Role :

- afficher le tableau principal apres login
- presenter les actions `Parametres` et `Ajouter un site`

Etat courant :

- le tableau est structure en trois colonnes : URL, mot de passe, edition
- le chargement reel depend d'une future methode backend `get_the_sites()`
- les ajouts/editions actuels restent locaux au frontend

## 6. Dependances observees

`runtime/requirements.txt` contient :

- `argon2-cffi`
- `cryptography`
- `wmi`
- `pywebview`

Dependances visibles dans le code :

- `pywebview` pour la fenetre desktop et le bridge JS/Python
- `cryptography` pour Argon2id, HKDF et AES-GCM
- `wmi` pour la detection Windows
- `tkinter` dans le module legacy `USB.py`

## 7. Resume d'etat

Ce qui est raccorde dans le depot :

- detection Windows et POSIX des supports USB
- choix initial de la page affichee
- creation de `USBKey.rin` sous Windows et POSIX
- creation de `PasswordManager.Archer` sous Windows et POSIX
- stockage de `Api.self.usb` comme chemin du dossier `USBSecurity`
- login Windows branche au frontend
- recuperation de `PasswordManagerKey` depuis `USBKey.rin` sous Windows
- stockage en memoire de `PasswordManagerKey` dans `Api.secret_manager`
- redirection frontend vers `Dashboard.html` si `Api.login(...)` renvoie `true`

Ce qui reste incomplet ou partiellement branche :

- le login POSIX n'est pas implemente
- `reload_usb_check()` renvoie un nom de page mais le frontend ne navigue pas encore a partir de ce retour
- `Nokey.html` reference un script absent
- `get_the_sites()` n'existe pas encore cote backend
- le module legacy `USB.py` n'est pas integre au flux principal
