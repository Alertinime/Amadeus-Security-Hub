# Rapport d'avancement

Etat documente le 28 avril 2026.

Depot Git : https://github.com/Alertinime/Amadeus-Security-Hub

## 1. Resume executif

Le socle applicatif est en place : demarrage desktop, detection USB, creation de
cle, login, lecture du conteneur de mots de passe et ajout d'entrees depuis le
dashboard. L'application est deja structuree autour d'un backend separe
Windows/Linux et d'un frontend statique pilote par `pywebview`.

Le prochain palier n'est pas de recreer l'architecture, mais de stabiliser les
flux existants : navigation apres detection, persistance de l'edition,
nettoyage des logs sensibles, tests automatises et clarification UX autour de
l'initialisation USB.

## 2. Conception hors architecture

Cette section documente les choix de conception et de technologie sans reprendre
le detail de l'architecture, qui est decrit dans `architecture.md`.

### 2.1 Choix du type d'application

Le projet est concu comme une application desktop locale plutot qu'une
application web hebergee.

Raisons principales :

- garder les secrets sur la machine de l'utilisateur ;
- eviter l'envoi du mot de passe maitre ou des donnees sensibles vers un
  serveur distant ;
- permettre l'acces direct aux supports USB ;
- conserver une interface simple avec des pages HTML locales.

### 2.2 Choix des technologies

- Python : coeur applicatif, detection USB, logique de chiffrement et operations
  fichier.
- `pywebview` : fenetre desktop et bridge entre JavaScript et Python.
- HTML/CSS/JavaScript statique : interface legere, sans bundler ni serveur web
  frontend.
- WMI : detection des supports USB sous Windows.
- `/sys`, `/proc/mounts` et `udisksctl` : detection et montage des supports
  USB sous Linux/POSIX.
- `cryptography` : AES-GCM, HKDF et primitives cryptographiques.
- Argon2id : derivation de cle a partir du mot de passe maitre.

### 2.3 Choix de securite

- Le mot de passe maitre n'est pas stocke.
- La cle de chiffrement du gestionnaire de mots de passe est stockee chiffree
  dans `USBKey.rin`.
- Les entrees du gestionnaire de mots de passe sont stockees chiffrees dans
  `PasswordManager.Archer`.
- Le chiffrement utilise AES-GCM avec nonce et AAD.
- La cle de session `PasswordManagerKey` n'est disponible en memoire qu'apres
  login reussi.
- Le support USB est utilise comme support physique de stockage des secrets
  applicatifs.

### 2.4 Choix d'interface

- Une page est dediee a chaque etat principal :
  - absence de cle ;
  - creation de cle ;
  - login ;
  - dashboard ;
  - parametres.
- Le dashboard privilegie une table simple `url/password`.
- L'ajout manuel passe par une modale.
- La page `Settings.html` est gardee comme point d'entree futur pour la
  configuration.

### 2.5 Choix pour l'extension web

L'extension navigateur prevue ne doit pas acceder directement aux fichiers de la
cle USB. Elle devra communiquer avec un serveur local AMHS, qui transmettra les
operations autorisees au controleur `AMHSPswdCtrl.py`.

Ce choix permet :

- de garder la logique de chiffrement dans le backend Python ;
- de centraliser les operations sur `PasswordManager.Archer` dans `Pswctrl` ;
- de limiter l'exposition des fichiers sensibles au navigateur ;
- de controler les requetes de l'extension via une couche locale dediee.

## 3. Fonctionnalites terminees ou branchees

- Demarrage via `app/main.py`.
- Detection de l'OS via `OSManagement.py`.
- Selection d'une API backend Windows ou Linux.
- Detection des supports USB Windows avec WMI.
- Detection des supports USB Linux/POSIX via `/sys`, `/proc/mounts` et
  `udisksctl`.
- Choix de la page initiale selon l'etat USB.
- Creation du dossier `USBSecurity`.
- Creation de `USBKey.rin`.
- Creation de `PasswordManager.Archer`.
- Derivation de cle via Argon2id et HKDF.
- Chiffrement AES-GCM des fichiers applicatifs.
- Login Windows.
- Login Linux/POSIX.
- Stockage en memoire de `PasswordManagerKey` dans `Pswctrl`.
- Lecture des entrees `sites` depuis le dashboard.
- Ajout d'une nouvelle entree depuis le dashboard et reecriture du fichier
  chiffre.
- Page `Settings.html` accessible depuis le dashboard.

## 4. Fonctionnalites partielles

- `reload_usb_check()` retourne bien une page cible, mais le frontend ne
  l'utilise pas encore pour naviguer.
- Les lignes du dashboard peuvent etre modifiees visuellement, mais la
  validation ne persiste pas encore les changements.
- `Settings.html` existe, mais reste une page placeholder.
- `Nokey.html` affiche un bouton de nouvelle detection, mais son script
  `JS/nokey.js` est absent.
- La documentation etait partiellement a jour ; elle est maintenant regroupee
  dans le dossier `docs/`.

## 5. Ecarts et risques

### Critiques

- Des logs de debug exposent des donnees sensibles dans les flux de login
  Windows et Linux. Ils doivent etre supprimes avant une utilisation reelle.
- Aucune suite de tests automatises ne couvre les formats de fichiers, les
  erreurs de dechiffrement ou les contrats d'API.

### Importants

- L'interface annonce dans `CreateKey.html` que toutes les donnees seront
  effacees, mais le backend ne formate pas la cle et n'efface pas le support.
  Le texte UX et le comportement doivent etre alignes.
- Le dashboard depend d'une session backend en memoire. Une ouverture directe de
  `Dashboard.html` sans login ne peut pas fonctionner correctement.
- Le module legacy `key-read&write/USB.py` n'est pas compatible avec le format
  moderne et peut preter a confusion.
- Les erreurs sont principalement journalisees avec `print`, sans canal
  utilisateur uniforme.

### Moyens

- Certains fichiers contiennent des caracteres accentues mal encodes.
- `PasswordManager` declare `_init_` au lieu de `__init__`, meme si cela ne
  bloque pas l'usage actuel.
- `SecretManager.secrets_dict` n'est plus le mecanisme principal de session.
- Les dependances Linux systeme ne sont pas explicitees dans
  `requirements.txt`, car elles ne sont pas des paquets Python.

## 6. Roadmap conseillee

### Priorite 1 - Stabilisation securite et flux

- Supprimer les logs sensibles de `KeyListingWin.py`, `KeyListingLinux.py` et
  des API webview.
- Ajouter `JS/nokey.js` pour rendre le bouton de detection fonctionnel.
- Utiliser la valeur retour de `reload_usb_check()` pour naviguer vers la bonne
  page.
- Aligner le message d'initialisation USB avec le comportement reel.

### Priorite 2 - Gestion des mots de passe

- Ajouter une API backend pour remplacer la liste complete ou mettre a jour une
  entree existante.
- Faire persister le bouton `Valider` du dashboard.
- Ajouter une action de suppression.
- Ajouter une validation minimale des donnees `url/password` cote backend.

### Priorite 3 - Tests

- Tester la creation de package `USBKey.rin`.
- Tester la creation et le dechiffrement de `PasswordManager.Archer`.
- Tester `Pswctrl.update_file_with_new_data`.
- Tester les erreurs : mauvais mot de passe, fichier absent, JSON invalide,
  cle invalide.
- Isoler les appels WMI, `/sys` et `udisksctl` derriere des mocks.

### Priorite 4 - Nettoyage technique

- Retirer ou archiver le module legacy `key-read&write/USB.py`.
- Normaliser l'encodage UTF-8 des fichiers HTML/JS.
- Harmoniser les noms de classes et methodes (`key_listening_linux`,
  `key_listing_win`, `Pswctrl`).
- Remplacer les `print` par un logging controle.
- Ajouter une commande de lancement documentee.

## 7. Definition de pret pour une version demo

Une version demo raisonnable devrait au minimum avoir :

- detection USB fonctionnelle sur l'OS cible ;
- creation de cle ;
- login ;
- lecture du dashboard ;
- ajout persistant ;
- edition persistante ou edition desactivee ;
- aucun log de cle, sel, nonce, AAD ou payload sensible ;
- documentation de lancement ;
- un jeu de tests unitaires sur la crypto applicative et le controleur de
  fichier.
- une extension web permettant d'interagire avec depuis navigateur chrominium
## 8. Etat des documents

Mis a jour dans cette passe :

- `docs/index.md`
- `docs/architecture.md`
- `docs/avancement.md`
- `docs/backend.md`
- `docs/frontend.md`
- `docs/runtime.md`
- `docs/key-management.md`
- `docs/key-create.md`
- `docs/key-read-write-legacy.md`
