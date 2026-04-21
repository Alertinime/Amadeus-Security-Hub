# Documentation technique du code

Cette documentation décrit uniquement le comportement observable dans le dépôt au moment de l'analyse.  
Elle couvre l'ensemble du code Python et JavaScript présent, ainsi que les vues HTML/CSS nécessaires pour comprendre les flux.

## 1. Vue d'ensemble

Le projet est une application desktop Python basée sur `pywebview`.

Le point d'entrée Python choisit un écran HTML en fonction de l'état des périphériques USB :

- `Nokey.html` si aucune clé USB n'est détectée.
- `CreateKey.html` si une clé USB est détectée mais ne contient pas encore `USBSecurity/USBKey.rin` ou `USBSecurity/USBKey.json`.
- `Login.html` si une clé USB contenant `USBSecurity/USBKey.rin` ou `USBSecurity/USBKey.json` est détectée.

Le front JavaScript appelle des méthodes Python via l'API exposée par `pywebview`.

## 2. Fichiers source réellement présents

### Python

- `app/main.py`
- `app/Backend/OSManagement.py`
- `app/Backend/WebviewAPI.py`
- `app/Backend/Cryptography/PasswordManager.py`
- `app/Backend/Key/KeyListingLinux.py`
- `app/Backend/Key/KeyListingWin.py`
- `app/Backend/Key/key-read&write/USB.py`
- `app/test.py`

### JavaScript

- `app/Frontend/Html/JS/common.js`
- `app/Frontend/Html/JS/login.js`
- `app/Frontend/Html/JS/create_key.js`

### HTML/CSS utilisés par ces scripts

- `app/Frontend/Html/Login.html`
- `app/Frontend/Html/CreateKey.html`
- `app/Frontend/Html/Nokey.html`
- `app/Frontend/Html/securityhub.css`

## 3. Flux global d'exécution

### Démarrage

Le fichier `app/main.py` :

- importe `webview`, `OSspliter` et `Api`.
- détecte l'OS via `os.name`.
- sur Windows (`"nt"`), charge `key_listing_win`, liste les clés USB, puis cherche `USBSecurity/USBKey.rin` ou `USBSecurity/USBKey.json`.
- sur Linux / POSIX (`"posix"`), charge `key_listening_linux`, liste les périphériques USB, monte temporairement les partitions non montées si nécessaire, puis cherche `USBSecurity/USBKey.rin` ou `USBSecurity/USBKey.json`.
- crée ensuite une fenêtre `pywebview` pointant vers l'un des trois fichiers HTML.
- injecte l'objet `Api` dans la fenêtre via `js_api=api`.
- lance l'application avec `webview.start(debug=False)`.
- à la fermeture sous POSIX, démonte les partitions que l'application a montées elle-même pendant la détection.

### Décision d'écran

Le code suit cette logique :

- aucune clé USB détectée : `Frontend/Html/Nokey.html`
- au moins une clé détectée, mais aucune clé "Security Hub" trouvée : `Frontend/Html/CreateKey.html`
- une clé "Security Hub" trouvée : `Frontend/Html/Login.html`

## 4. Backend Python

### `app/main.py`

Rôle :

- point d'entrée de l'application.
- orchestration initiale entre détection USB, choix de l'écran et démarrage de `pywebview`.

Comportement notable :

- la variable `api` est créée une seule fois.
- `api.set_window(window)` stocke la fenêtre dans l'objet API, mais aucun autre code du dépôt n'utilise ensuite `self.window`.
- le code sépare explicitement Windows et POSIX.

### `app/Backend/OSManagement.py`

Rôle :

- encapsuler la détection de l'OS.

Contenu réel :

- la classe `OSspliter` expose uniquement `get_current_os()`.
- cette méthode retourne directement `os.name`.

Valeurs attendues dans le code :

- `"nt"` pour Windows
- `"posix"` pour Linux / environnements POSIX

### `app/Backend/WebviewAPI.py`

Rôle :

- exposer au JavaScript les méthodes Python appelables via `pywebview`.

Chargement :

- le module importe `key_listing_win` si l'OS courant vaut `"nt"`.
- il importe `key_listening_linux` si l'OS courant vaut `"posix"`.

Méthodes exposées :

- `log(value)` : affiche simplement `value` dans la sortie standard.
- `check_os()` : retourne `os.name`.
- `set_window(window)` : stocke la référence de la fenêtre.
- `reload_usb_check()` : refait une détection USB et retourne uniquement une chaîne parmi `Nokey.html`, `CreateKey.html` ou `Login.html`.
- `usb_list()` :
  - sous Windows, retourne `[usb.Caption for usb in key]`
  - sous POSIX, retourne `[usb["product"] for usb in usb_devices]`
- `init_usb(device, password)` :
  - reliste les périphériques USB
  - sous POSIX, trouve celui dont `usb["product"] == device`
  - sous Windows, trouve celui dont `usb.Caption == device`
  - appelle `initialize_security_key(...)` sur le support trouvé

Limites visibles :

- `reload_usb_check()` retourne un nom de page mais ne change pas elle-même la fenêtre.
- aucune méthode `go_back()` n'existe dans ce fichier.
- aucune méthode d'authentification ou de déchiffrement n'est exposée pour l'écran de login.

### `app/Backend/Cryptography/PasswordManager.py`

Rôle :

- dériver une clé depuis un mot de passe et générer un sel.

Méthodes :

- `kdf(mdp, salt)` :
  - utilise `cryptography.hazmat.primitives.kdf.argon2.Argon2id`
  - longueur de sortie : 32 octets
  - `iterations=1`
  - `memory_cost=2_097_152`
  - `lanes=8`
  - retourne `kdf.derive(mdp.encode())`
- `create_salt()` :
  - retourne `os.urandom(16)`

Remarque factuelle :

- la classe déclare `_init_` au lieu de `__init__`. Cela n'empêche pas l'instanciation, mais ce n'est pas un constructeur Python standard.

### `app/Backend/Key/KeyListingLinux.py`

Rôle :

- détecter les périphériques USB sous Linux/POSIX.
- localiser une clé déjà initialisée.
- commencer un flux d'initialisation d'une clé.
- gérer sous POSIX les montages temporaires nécessaires à la détection.

Méthodes :

- `list_with_lsusb()` :
  - appelle `lsusb`
  - retourne la liste des lignes non vides
  - en cas d'erreur, retourne `[]`
  - cette méthode n'est pas utilisée ailleurs dans le dépôt

- `_find_block_devices(devpath)` :
  - parcourt récursivement un sous-arbre de `/sys/bus/usb/devices`
  - collecte les noms de périphériques bloc trouvés dans les dossiers `block`
  - retourne la liste triée

- `_mounted_points_for(block_names)` :
  - lit `/proc/mounts`
  - associe les noms de périphériques bloc à leurs points de montage
  - retourne la liste des points de montage correspondants

- `_mount_block_device(block_name)` :
  - appelle `udisksctl mount -b /dev/<partition>`
  - retourne `True` si le montage réussit

- `_unmount_block_device(block_name)` :
  - appelle `udisksctl unmount -b /dev/<partition>`
  - retourne `True` si le démontage réussit

- `_ensure_mounts(usb)` :
  - réutilise les points de montage existants si le support est déjà monté
  - sinon tente de monter ses partitions
  - mémorise les partitions montées par l'application dans `mounted_by_app`

- `_release_usb_mounts(usb)` :
  - démonte uniquement les partitions montées par l'application pour ce support

- `cleanup_managed_mounts()` :
  - démonte à la fermeture de l'application les partitions que le backend POSIX a gardées montées

- `list_usb()` :
  - parcourt `/sys/bus/usb/devices`
  - ignore les entrées sans `idVendor`
  - lit les métadonnées suivantes si elles existent :
    - `idVendor`
    - `idProduct`
    - `manufacturer`
    - `product`
    - `serial`
  - ajoute aussi :
    - `sysname`
    - `blocks`
    - `mounts`
  - exclut les périphériques sans périphérique bloc
  - retourne une liste de dictionnaires décrivant les supports USB montables

- `check_for_security_key(usbl)` :
  - parcourt les supports USB détectés
  - monte temporairement un support si nécessaire pour pouvoir l'inspecter
  - cherche `USBSecurity/USBKey.rin` puis `USBSecurity/USBKey.json`
  - si le fichier existe :
    - ajoute `security_mount`
    - ajoute `security_key_path`
    - affiche le chemin trouvé
    - retourne le dictionnaire USB concerné
  - si aucun fichier n'est trouvé sur un support monté par l'application, ce support est redémonté immédiatement
  - sinon retourne `False`

- `initialize_security_key(usb, password)` :
  - s'assure d'abord que le support dispose d'un point de montage utilisable
  - instancie `PasswordManager`
  - génère un sel
  - dérive une clé à partir du mot de passe
  - dérive ensuite une clé HKDF liée au support USB
  - écrit un fichier `USBSecurity/USBKey.rin`

Constat important :

- la détection POSIX ne dépend plus du fait qu'un volume soit déjà monté avant le démarrage de l'application.

### `app/Backend/Key/KeyListingWin.py`

Rôle :

- détecter les lecteurs USB sous Windows.
- vérifier si un lecteur contient déjà la structure `USBSecurity/USBKey.rin` ou `USBSecurity/USBKey.json`.

Méthodes :

- `check_for_key()` :
  - utilise `wmi.WMI()`
  - parcourt `Win32_LogicalDisk()`
  - conserve les volumes dont `DriveType == 2`
  - retourne la liste des lecteurs trouvés ou `False`

- `check_for_security_key(usbl)` :
  - teste pour chaque lecteur l'existence de `usb.Caption/USBSecurity/USBKey.rin` puis `usb.Caption/USBSecurity/USBKey.json`
  - retourne le premier lecteur correspondant ou `False`

## 3.1 Flux de détection Linux / POSIX

Au démarrage, le backend POSIX applique le flux suivant :

1. lister les périphériques USB avec un périphérique bloc associé
2. pour chaque support, réutiliser ses points de montage s'ils existent déjà
3. si le support n'est pas monté, tenter un montage via `udisksctl`
4. chercher `USBSecurity/USBKey.rin`, puis `USBSecurity/USBKey.json`
5. si une clé est trouvée, conserver le montage pour le reste de la session afin de permettre le login
6. si aucune clé n'est trouvée sur un support monté par l'application, démonter ce support immédiatement
7. à la fermeture de l'application, démonter les partitions que l'application a montées elle-même

Ce flux évite deux erreurs :

- ouvrir `CreateKey.html` alors qu'une clé de sécurité existe mais que son volume n'était pas monté
- démonter un volume déjà monté par l'utilisateur ou par le système avant le lancement de l'application

### `app/Backend/Key/key-read&write/USB.py`

Rôle :

- implémenter une logique de création et de lecture d'un fichier `USBKey.json` chiffré sur une clé USB, avec interface Tkinter pour la saisie du mot de passe.

État d'intégration :

- aucun autre fichier du dépôt n'importe cette classe.
- ce module n'est pas utilisé par `main.py` ni par `WebviewAPI.py`.

Fonctionnement interne :

- `__init__(usb_path)` :
  - stocke l'objet USB dans `self.usb`

- `is_usb()` :
  - vérifie l'existence de `self.usb.caption`
  - retourne `False` si le chemin n'existe pas
  - sinon retourne `True`

- `charging()` :
  - appelle `is_usb()`
  - ne fait rien d'autre

- `doK()` :
  - crée un sel depuis `sha256(self.usb.VolumeSerialNumber.encode())[:16]`
  - récupère un mot de passe transformé via `get_processed()`
  - applique ensuite `HKDF(SHA256, length=32, salt=salt, info=b"fixed-app-context")`
  - retourne la clé dérivée finale

- `run_create()` :
  - vérifie la clé USB
  - dérive la clé
  - prépare un paquet chiffré
  - tente de le sauvegarder sur le support

- `run_decrypt()` :
  - vérifie la clé USB
  - dérive la clé
  - lit et déchiffre `USBKey.json`
  - retourne les données JSON déchiffrées

- `get_data(potato)` :
  - lit `USBSecurity/USBKey.json`
  - décode `iv` et `data` en base64
  - déchiffre avec `AESGCM`
  - retourne l'objet JSON obtenu

- `save(data)` :
  - crée `USBSecurity` si le dossier n'existe pas
  - écrit `USBKey.json`
  - tente de cacher le dossier avec les attributs Windows via `ctypes.windll.kernel32`
  - retourne `True` si le dossier a été créé, sinon `False`

- `prepare_data(potato)` :
  - génère une clé aléatoire de 32 octets
  - construit un JSON contenant :
    - un `UUID`
    - une clé encodée en base64
  - chiffre ce JSON avec `AESGCM`
  - retourne un dictionnaire `{ "iv": ..., "data": ... }`

- `get_processed()` :
  - ouvre une fenêtre Tkinter
  - récupère le mot de passe saisi
  - applique `argon2.low_level.hash_secret_raw(...)`
  - stocke le résultat dans `self.result`
  - ferme la fenêtre
  - retourne `self.result`

Remarques factuelles sur ce module :

- `is_usb()` utilise `self.usb.caption` en minuscule, alors que le reste du fichier utilise `self.usb.Caption`.
- `default_backend` est importé mais n'est jamais utilisé.
- ce module vise clairement un flux Windows, notamment à cause de `VolumeSerialNumber`, `Caption` et `ctypes.windll`.

### `app/test.py`

Rôle actuel :

- fichier vide.

## 5. Frontend JavaScript

### `app/Frontend/Html/JS/common.js`

Rôle :

- fournir un accès commun à l'API Python exposée par `pywebview`.

Fonctions :

- `getApi()` :
  - retourne `window.pywebview.api` si disponible
  - sinon `window.api` si disponible
  - sinon `null`

- `callApi(method, ...args)` :
  - récupère l'API
  - vérifie que la méthode demandée existe
  - appelle la méthode de façon asynchrone
  - journalise les erreurs et les relance

Effet :

- ces deux fonctions sont exportées sur `window`.

### `app/Frontend/Html/JS/login.js`

Rôle :

- gérer l'envoi du mot de passe saisi dans l'écran de connexion.

Fonctionnement :

- écoute `DOMContentLoaded`
- récupère le formulaire `.form-block`
- intercepte le `submit`
- lit `#master-password`
- récupère l'API Python
- appelle `log(value)` côté Python

Constat important :

- l'écran de login n'effectue actuellement ni validation d'accès, ni déchiffrement, ni comparaison de secret.
- le mot de passe saisi est seulement envoyé à `Api.log()`, qui l'affiche sur la sortie standard.

### `app/Frontend/Html/JS/create_key.js`

Rôle :

- gérer l'écran de sélection de support USB et la saisie du mot de passe maître lors de l'initialisation d'une clé.

État interne :

- `selectedDevice` mémorise le nom du support choisi.
- `PASSWORD_REGEX` impose :
  - au moins 12 caractères
  - une minuscule
  - une majuscule
  - un chiffre
  - un symbole

Fonctions principales :

- `openPasswordModal(deviceName)` :
  - mémorise le support sélectionné
  - met à jour le libellé de la popup
  - vide les champs et erreurs
  - affiche la popup

- `closePasswordModal()` :
  - masque la popup
  - réinitialise `selectedDevice`

- `validatePassword(password, confirmPassword)` :
  - vérifie la regex
  - vérifie l'égalité des deux champs
  - retourne une liste d'erreurs

- `handlePasswordSubmit(event)` :
  - empêche le submit HTML normal
  - lit les deux champs mot de passe
  - affiche les erreurs de validation éventuelles
  - appelle `api.init_usb(selectedDevice, password)` si disponible
  - ferme la popup en cas de succès technique de l'appel

- `setupPasswordModal()` :
  - branche le `submit` du formulaire de popup
  - branche le bouton d'annulation
  - ferme la popup au clic sur le fond
  - ferme la popup avec `Escape`

- `createUsbButton(name)` :
  - crée dynamiquement un bouton pour un support USB
  - ouvre la popup au clic

- `loadUsbList()` :
  - vide `.menu-list`
  - attend que l'API `pywebview` soit disponible
  - appelle `usb_list()`
  - crée un bouton par support détecté
  - affiche un message si aucun support n'est trouvé ou si l'API est absente

- `setupBackButton()` :
  - branche le bouton `.btn-back`
  - appelle `reload_usb_check()` si disponible
  - sinon appelle `go_back()` si disponible

- `start()` :
  - initialise les handlers
  - charge la liste USB

Déclenchement :

- `start()` est lancé sur l'événement `pywebviewready`.
- en fallback, `start()` est aussi lancé au `DOMContentLoaded` si l'API est déjà prête.

Constats importants :

- le code attend un retour de `reload_usb_check()` ou `go_back()`, mais n'utilise pas la valeur renvoyée pour naviguer vers une autre page.
- aucun `go_back()` n'existe côté Python.
- si `init_usb()` retourne `None`, le code ferme quand même la popup après l'appel réussi.

## 6. Vues HTML et feuille de style

### `app/Frontend/Html/Login.html`

Rôle :

- afficher le formulaire de mot de passe maître.

Structure :

- une carte centrale
- un champ `#master-password`
- un bouton de soumission
- chargement de `JS/common.js` puis `JS/login.js`

Point important :

- le formulaire possède `method="post"` et `action="/unlock"`, mais ce submit est intercepté par `login.js`. Aucun backend HTTP n'est présent dans le dépôt.

### `app/Frontend/Html/CreateKey.html`

Rôle :

- afficher les supports USB détectés et la popup de saisie du mot de passe maître.

Structure :

- un conteneur `.menu-list` rempli dynamiquement par `create_key.js`
- un bouton `Retour`
- une popup contenant :
  - le nom du support sélectionné
  - deux champs mot de passe
  - une zone d'erreur
  - un bouton d'annulation
  - un bouton d'initialisation

### `app/Frontend/Html/Nokey.html`

Rôle :

- afficher l'absence de clé USB détectée.

Structure :

- message principal
- message secondaire
- bouton `Réessayer la détection`
- bouton `Quitter`
- chargement de `JS/common.js`
- chargement de `JS/nokey.js`

Constat important :

- `JS/nokey.js` n'existe pas dans le dépôt.
- aucun comportement JavaScript n'est donc défini ici pour les boutons de cet écran.

### `app/Frontend/Html/securityhub.css`

Rôle :

- fournir le style des trois écrans HTML.

Le fichier :

- définit les variables CSS globales
- stylise les cartes, boutons, champs mot de passe, messages d'état et popup de mot de passe
- ne contient aucune logique métier

## 7. Dépendances visibles

Le fichier `runtime/requirements.txt` contient :

- `argon2-cffi`
- `cryptography`
- `wmi`
- `pywebview`

Dépendances effectivement visibles dans le code :

- `pywebview` pour la fenêtre desktop et le bridge JS/Python
- `cryptography` pour Argon2id, HKDF et AESGCM
- `argon2-cffi` pour `hash_secret_raw`
- `wmi` pour la détection Windows
- `tkinter` pour la saisie de mot de passe dans `USB.py`

## 8. État réel du projet d'après le code

### Ce qui fonctionne conceptuellement dans le dépôt

- détection initiale de l'OS
- détection de périphériques USB Windows et Linux
- choix initial de l'écran affiché
- bridge JavaScript vers Python via `pywebview`
- affichage dynamique de la liste des supports USB dans `CreateKey.html`
- validation front d'un mot de passe maître dans `create_key.js`

### Ce qui est présent mais incomplet ou non raccordé

- `KeyListingLinux.initialize_security_key()` ne termine pas l'initialisation d'une clé.
- `login.js` n'implémente pas un déverrouillage réel.
- `USB.py` contient une logique de création/lecture chiffrée, mais elle n'est pas branchée au flux principal.
- `Nokey.html` référence un script absent.
- `reload_usb_check()` renvoie un nom de page, mais rien dans le front ne recharge la vue à partir de cette valeur.
- `app/test.py` ne contient aucun test.

### Écarts entre l'interface et le code observé

- `CreateKey.html` annonce que toutes les données seront effacées, mais aucun code d'effacement ou de formatage n'apparaît dans les sources lues.
- `Login.html` annonce un déchiffrement local, mais le code actuel ne fait qu'imprimer le mot de passe saisi.
- `Nokey.html` annonce une détection automatique et propose des boutons d'action, mais aucun script correspondant n'est présent.

## 9. Résumé final

Le dépôt contient une base d'application desktop `pywebview` organisée autour de trois écrans : absence de clé, création de clé, connexion.

Le flux actuellement le plus abouti est :

- détection d'une clé USB
- affichage de la liste des supports
- saisie d'un mot de passe côté front
- appel de l'API Python correspondante

En revanche, le flux complet de création réelle d'une clé Security Hub et le flux complet de déverrouillage ne sont pas finis dans l'état actuel du code.
