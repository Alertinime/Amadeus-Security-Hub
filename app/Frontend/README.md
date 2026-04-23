# Frontend

Le frontend du projet n'est pas un projet Node ou SPA.

Il s'agit d'un ensemble de fichiers statiques charges par `pywebview` :

- `Html/Nokey.html`
- `Html/CreateKey.html`
- `Html/Login.html`
- `Html/Dashboard.html`
- `Html/Settings.html`
- `Html/securityhub.css`
- `Html/JS/common.js`
- `Html/JS/create_key.js`
- `Html/JS/login.js`
- `Html/JS/dashboard.js`

## Role

- afficher les ecrans principaux de l'application
- afficher la page principale apres authentification
- appeler les methodes Python exposees par `js_api`
- gerer la selection USB et la saisie du mot de passe

## Points utiles

- `common.js` centralise l'acces a `window.pywebview.api`
- `create_key.js` appelle `usb_list()` et `init_usb(...)`
- `login.js` appelle `login(...)`
- `dashboard.js` appelle `get_the_sites()` si la methode existe
- `Nokey.html` reference `JS/nokey.js`, mais ce fichier n'existe pas dans le depot

## Notes

- aucun bundler, serveur dev Node ou pipeline frontend n'apparait dans ce dossier
- la navigation entre pages n'est pas geree cote JavaScript a partir des retours de `reload_usb_check()`
