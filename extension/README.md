# Extension Chromium

Extension navigateur pour Amadeus Security Hub.

Cette extension est prevue pour fonctionner avec les navigateurs Chromium, comme Google Chrome, Microsoft Edge, Brave ou Chromium.

## Objectif

L'objectif est de construire la base d'une extension capable de travailler avec un futur gestionnaire de mots de passe.

Pour le moment, l'extension ne gere pas encore de coffre, de compte utilisateur, de synchronisation ou de sauvegarde. Elle fait uniquement la premiere brique fonctionnelle :

- detecter les champs de mot de passe dans une page web ;
- afficher un bouton de generation quand l'utilisateur clique dans un champ ;
- generer un mot de passe localement ;
- remplir le champ selectionne avec le mot de passe genere.

## Etat actuel

Version actuelle : `0.1.0`

Fonctionnalites disponibles :

- Detection des champs `<input type="password">`.
- Affichage d'un bouton `Generer` au focus ou au clic sur un champ mot de passe.
- Generation locale d'un mot de passe de 20 caracteres.
- Utilisation de `crypto.getRandomValues` pour l'aleatoire.
- Insertion du mot de passe dans le champ actif.
- Emission des evenements `input` et `change` pour que les sites web detectent la modification.
- Repositionnement du bouton au scroll et au resize.

## Structure des fichiers

```text
extension/
  manifest.json
  README.md
  test-page.html
  src/
    content.css
    content.js
```

### `manifest.json`

Declare l'extension Chromium en Manifest V3.

Points importants :

- `manifest_version: 3` : format actuel des extensions Chromium.
- `matches: ["<all_urls>"]` : le content script peut s'injecter sur toutes les pages visitees.
- `js: ["src/content.js"]` : script qui detecte les champs et gere la generation.
- `css: ["src/content.css"]` : style du bouton injecte.
- `permissions: []` : aucune permission specifique n'est demandee pour l'instant.

### `src/content.js`

Script injecte dans les pages web.

Responsabilites :

- ecouter les evenements `focusin` et `click` ;
- verifier si l'element cible est un `HTMLInputElement` de type `password` ;
- creer un bouton flottant si necessaire ;
- placer le bouton a cote du champ actif ;
- generer un mot de passe ;
- remplir le champ actif ;
- declencher les evenements attendus par les frameworks frontend.

Le mot de passe genere contient actuellement :

- lettres minuscules ;
- lettres majuscules ;
- chiffres ;
- symboles.

La longueur actuelle est de 20 caracteres.

### `src/content.css`

Style du bouton `Generer`.

Le bouton est positionne en `absolute` avec un `z-index` tres eleve pour rester visible au-dessus de la page.

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

Quand l'utilisateur clique dans un champ mot de passe, le bouton `Generer` doit apparaitre.

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

Exemple de mot de passe possible :

```text
hO2WrtK]d*t0dau{;?F8
```

Le resultat change a chaque generation.

## Limites actuelles

Cette version est volontairement minimale.

Limites connues :

- pas encore de popup d'extension ;
- pas encore de stockage de mots de passe ;
- pas encore de connexion avec le reste de l'application Amadeus Security Hub ;
- pas encore de detection avancee des formulaires ;
- pas encore de choix de longueur ;
- pas encore de choix des caracteres autorises ;
- pas encore de copie dans le presse-papiers ;
- pas encore de gestion des iframes complexes ;
- pas encore de support specifique pour les champs caches ou les composants custom.

## Pistes pour la suite

Prochaines evolutions possibles :

- ajouter une popup d'extension ;
- ajouter une page d'options ;
- permettre de choisir la longueur du mot de passe ;
- permettre d'exclure certains symboles ;
- ajouter un bouton pour copier le mot de passe ;
- detecter les formulaires d'inscription ;
- proposer l'enregistrement du mot de passe genere ;
- connecter l'extension au futur coffre de mots de passe ;
- ajouter un background service worker ;
- ajouter des tests automatises.

## Notes de securite

Le mot de passe est genere localement dans le navigateur.

La version actuelle ne transmet aucune donnee a un serveur et ne demande aucune permission specifique en dehors de l'injection du content script sur les pages correspondant au filtre `matches`.

Le stockage et la synchronisation devront etre concus separement avec attention, car ils impliqueront des choix de chiffrement, d'authentification et de gestion des secrets.
