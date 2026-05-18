# Frontend

Le frontend n'est pas une SPA et n'utilise pas de projet Node. Il s'agit de
pages statiques chargees par `pywebview`.

## Pages

- `Html/Nokey.html` : aucun support USB detecte.
- `Html/CreateKey.html` : choix du support USB et creation de cle.
- `Html/Login.html` : saisie du mot de passe maitre.
- `Html/Dashboard.html` : lecture et ajout d'entrees du gestionnaire de mots de
  passe.
- `Html/Settings.html` : page placeholder de configuration.
- `Html/securityhub.css` : styles communs.

## Scripts

- `Html/JS/common.js`
  - `getApi()`
  - `callApi(method, ...args)`
  - `goToPage(page)`

- `Html/JS/create_key.js`
  - charge `api.usb_list()`;
  - valide le mot de passe maitre ;
  - appelle `api.init_usb(device, password)`.

- `Html/JS/login.js`
  - appelle `api.login(value)`;
  - ouvre `Dashboard.html` si le backend retourne `true`.

- `Html/JS/dashboard.js`
  - appelle `api.get_pswtable_data()`;
  - affiche la liste `sites`;
  - accepte les entrees au format `{ domaine, password }` et conserve une
    compatibilite d'affichage avec quelques anciennes cles (`url`, `domain`,
    `site`, `website`) ;
  - appelle `api.update_password_data({ sites: [...] })` pour ajouter une
    entree au format `{ domaine, password }` ;
  - ouvre `Settings.html` depuis le bouton Parametres.

## Contrat API attendu

Le frontend suppose que `window.pywebview.api` expose :

- `login`
- `reload_usb_check`
- `usb_list`
- `init_usb`
- `get_pswtable_data`
- `update_password_data`

`common.js` fournit aussi un fallback `window.api` utile pour certains tests
manuels.

## Etat courant

Fonctionnel :

- affichage des ecrans principaux ;
- listing USB dans l'ecran de creation ;
- validation locale du mot de passe maitre ;
- login et navigation vers le dashboard ;
- chargement du tableau depuis le fichier chiffre ;
- ajout d'un site persistant.
- affichage des domaines stockes sous la cle `domaine`.

Incomplet :

- `Nokey.html` reference `JS/nokey.js`, absent du depot ;
- le bouton retour de `CreateKey.html` appelle `reload_usb_check()` mais ne
  navigue pas avec le retour ;
- l'edition d'une ligne du dashboard est locale et non persistante ;
- `Settings.html` est encore un placeholder.
