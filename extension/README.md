# Extension Chromium

Extension navigateur pour Amadeus Security Hub.

Cette extension est prevue pour fonctionner avec les navigateurs Chromium, comme Google Chrome, Microsoft Edge, Brave ou Chromium.

## Objectif

L'objectif est de fournir une extension capable d'interagir avec le gestionnaire
de mots de passe local Amadeus Security Hub.

L'extension ne lit jamais directement les fichiers de la cle USB. Elle passe par
Native Messaging, puis par le serveur IPC local de l'application desktop.

Elle couvre les usages suivants :

- detecter les champs de mot de passe dans une page web ;
- demander au backend si un mot de passe existe pour le domaine courant ;
- proposer `Remplir` quand un mot de passe est trouve ;
- generer un mot de passe localement avec `Generer` ;
- memoriser le dernier mot de passe genere pour permettre `Confirmer` dans un
  champ de confirmation ;
- proposer l'enregistrement du mot de passe genere dans le coffre local.

## Etat actuel

Version actuelle : `0.1.0`

Fonctionnalites disponibles :

- Detection des champs `<input type="password">`.
- Detection via `click`, `focusin` et `event.composedPath()`, utile sur les
  composants web qui encapsulent les inputs.
- Affichage d'un panneau flottant au focus ou au clic sur un champ mot de passe.
- Generation locale d'un mot de passe de 20 caracteres.
- Utilisation de `crypto.getRandomValues` pour l'aleatoire.
- Bouton `Remplir` affiche seulement si le coffre renvoie un mot de passe pour
  le domaine courant.
- Bouton `Generer` qui remplit uniquement le champ actif.
- Bouton `Confirmer` qui remplit le champ actif avec le dernier mot de passe
  genere sur la page.
- Enregistrement optionnel du mot de passe genere via Native Messaging et IPC.
- Emission des evenements `input` et `change` pour que les sites web detectent la modification.
- Repositionnement du panneau au scroll et au resize.

## Structure des fichiers

```text
extension/
  manifest.json
  README.md
  test-page.html
  NativesMessages/
    NativesPipeline.py
    run-native-host.cmd
    run-native-host.sh
  src/
    content.css
    content.js
    background.js
```

### `manifest.json`

Declare l'extension Chromium en Manifest V3.

Points importants :

- `manifest_version: 3` : format actuel des extensions Chromium.
- `matches: ["<all_urls>"]` : le content script peut s'injecter sur toutes les pages visitees.
- `js: ["src/content.js"]` : script qui detecte les champs et gere la generation.
- `css: ["src/content.css"]` : style du bouton injecte.
- `permissions: ["nativeMessaging"]` : permet au service worker de communiquer avec le host natif.
- `background.service_worker` : declare le service worker qui sert de pont entre le content script et Native Messaging.

### `src/content.js`

Script injecte dans les pages web.

Responsabilites :

- ecouter les evenements `focusin` et `click` ;
- verifier si l'element cible est un `HTMLInputElement` de type `password` ;
- creer un panneau flottant si necessaire ;
- placer le panneau sous le champ actif ;
- demander le mot de passe du domaine courant au backend ;
- afficher `Remplir` seulement si une entree existe dans le coffre ;
- generer un mot de passe ;
- remplir uniquement le champ actif ;
- conserver le dernier mot de passe genere pour le bouton `Confirmer` ;
- envoyer au backend le mot de passe genere si l'utilisateur accepte
  l'enregistrement ;
- declencher les evenements attendus par les frameworks frontend.

Le mot de passe genere contient actuellement :

- lettres minuscules ;
- lettres majuscules ;
- chiffres ;
- symboles.

La longueur actuelle est de 20 caracteres.

### `src/content.css`

Style du panneau flottant et des boutons `Generer`, `Remplir` et `Confirmer`.

Le panneau est positionne en `absolute` avec un `z-index` tres eleve pour rester
visible au-dessus de la page.

### `src/background.js`

Service worker Manifest V3.

Responsabilites :

- recevoir les messages envoyes par le content script ;
- router `native_ask` vers le message natif `Ask` ;
- router `native_add` vers le message natif `AddEntry` ;
- appeler le host Native Messaging `com.amadeus.security_hub` ;
- renvoyer la reponse au content script.

### `NativesMessages`

Contient le host natif de test et les lanceurs systeme.

Ces fichiers ne sont pas des installateurs. Les installateurs centraux sont documentes dans `docs/installateurs.md`.

Flux Windows actuel :

```text
content.js
  -> background.js
  -> Native Messaging host NativesPipeline.py
  -> extension/NativesMessages/IPC/WinNamedPipes.py
  -> app/Backend/IPC/WinNamedPipesHandler.py
  -> Pswctrl.getpsswd(path, domaine)
  -> Pswctrl.addentry(path, domaine, password)
```

### `test-page.html`

Page locale simple pour tester l'extension avec un champ email et un champ mot de passe.

Cette page sert uniquement au developpement local.

## Installation en local sur Edge

1. Ouvrir Microsoft Edge.
2. Aller sur `edge://extensions`.
3. Activer le `Mode developpeur`.
4. Cliquer sur `Charger l'extension decompressee`.
5. Selectionner le dossier `extension`.
6. Ouvrir une page avec un champ mot de passe.

Quand l'utilisateur clique dans un champ mot de passe, le panneau doit apparaitre.

## Installation en local sur Chrome

1. Ouvrir Google Chrome.
2. Aller sur `chrome://extensions`.
3. Activer le `Mode developpeur`.
4. Cliquer sur `Charger l'extension non empaquetee`.
5. Selectionner le dossier `extension`.
6. Tester sur une page contenant un champ `<input type="password">`.

## Test rapide

Apres avoir charge l'extension dans Edge ou Chrome :

1. Ouvrir le fichier `extension/test-page.html` dans le navigateur.
2. Cliquer dans le champ `Mot de passe`.
3. Verifier que le bouton `Generer` apparait.
4. Cliquer sur `Generer`.
5. Verifier que le champ mot de passe est rempli.
6. Cliquer dans un autre champ mot de passe.
7. Verifier que `Confirmer` permet de remettre le meme mot de passe genere.

Pour tester `Remplir`, il faut que l'application desktop soit lancee, que
l'utilisateur soit connecte a sa cle, et qu'une entree existe pour le domaine
courant dans `PasswordManager.Archer`.

Exemple de mot de passe possible :

```text
hO2WrtK]d*t0dau{;?F8
```

Le resultat change a chaque generation.

## Limites actuelles

Cette version est volontairement minimale.

Limites connues :

- pas encore de popup d'extension ;
- pas encore de choix de longueur ;
- pas encore de choix des caracteres autorises ;
- pas encore de copie dans le presse-papiers ;
- pas encore de gestion des iframes complexes ;
- support limite aux shadow roots ouverts ; les shadow roots fermes restent
  inaccessibles au content script ;
- l'extension ne tente pas de deviner automatiquement les champs
  ancien/nouveau/confirmation : l'utilisateur choisit explicitement `Remplir`,
  `Generer` ou `Confirmer` sur le champ actif.

## Pistes pour la suite

Prochaines evolutions possibles :

- ajouter une popup d'extension ;
- ajouter une page d'options ;
- permettre de choisir la longueur du mot de passe ;
- permettre d'exclure certains symboles ;
- ajouter un bouton pour copier le mot de passe ;
- detecter les formulaires d'inscription ;
- ajouter un panneau d'options ;
- ajouter une UI plus riche pour afficher l'etat d'enregistrement ;
- etendre le support Linux du serveur IPC extension si necessaire ;
- ajouter des tests automatises.

## Notes de securite

Le mot de passe genere est cree localement dans le navigateur avec
`crypto.getRandomValues`.

Quand l'utilisateur accepte l'enregistrement, le mot de passe est transmis au
host Native Messaging local, puis au serveur IPC local de l'application desktop.
Il n'est pas envoye a un serveur distant.

Le stockage reste gere par `Pswctrl` et `PasswordManager.Archer`, chiffre sur la
cle USB. L'extension ne conserve pas le mot de passe au-dela de la page active,
sauf en memoire JS pour permettre le bouton `Confirmer`.
