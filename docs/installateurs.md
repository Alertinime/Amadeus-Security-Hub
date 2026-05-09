# Installateurs

La solution utilise deux installateurs centraux :

- `install-windows.ps1` pour Windows.
- `install-linux.sh` pour Linux.

Ces deux fichiers sont les seuls points d'entree d'installation. Les fichiers dans `extension/NativesMessages` ne sont pas des installateurs : ce sont le host Native Messaging et ses lanceurs par systeme.

## Ce que font les installateurs

Les installateurs preparent l'environnement local necessaire a l'application et a l'extension navigateur.

Ils gerent :

- la creation de l'environnement Python `runtime/.venv` ;
- l'installation ou la mise a jour des dependances depuis `runtime/requirements.txt` ;
- la creation du manifest Native Messaging ;
- l'enregistrement du host Native Messaging pour le navigateur choisi ;
- la desinstallation de l'enregistrement Native Messaging.

## Prerequis

### Windows

- Python 3 installe et disponible via `py -3` ou `python`.
- PowerShell.
- L'extension chargee dans le navigateur en mode developpeur.
- L'ID de l'extension, visible dans la page des extensions du navigateur.

### Linux

- Python 3.
- Le module Python `venv`.
- Bash.
- L'extension chargee dans le navigateur en mode developpeur.
- L'ID de l'extension.

Sur certaines distributions Linux, `venv` peut demander un paquet systeme, par exemple `python3-venv`.

## ID de l'extension

L'ID de l'extension est utilise par le manifest Native Messaging pour declarer quelles extensions ont le droit de parler au host natif.

En developpement, l'extension contient une cle publique stable dans `extension/manifest.json`. Cette cle donne l'ID stable suivant :

```text
olgcbmgnoainnpfchiakbfcidhpcgdmo
```

Les installateurs utilisent cet ID par defaut. Il n'est donc pas necessaire de fournir l'ID tant que la cle publique du manifest ne change pas.

Pour le trouver :

1. Ouvrir la page des extensions du navigateur.
2. Activer le mode developpeur.
3. Copier l'ID affiche pour l'extension Amadeus Security Hub.

Si la cle change, ou si l'extension est publiee avec un autre ID, l'option `ExtensionId` permet d'overrider la valeur par defaut.

L'ID doit avoir 32 caracteres entre `a` et `p`.

## Windows

Commande generale :

```powershell
powershell -ExecutionPolicy Bypass -File .\install-windows.ps1 -Browser Edge
```

Navigateurs supportes :

- `Edge`
- `Chrome`
- `Chromium`
- `Brave`
- `All`

`Both` est encore accepte comme alias pour `Edge + Chrome`, mais `All` doit etre prefere.

### Exemples Windows

Installer pour Edge :

```powershell
powershell -ExecutionPolicy Bypass -File .\install-windows.ps1 -ExtensionId TON_ID_EXTENSION -Browser Edge
```

Installer pour Edge avec l'ID stable par defaut :

```powershell
powershell -ExecutionPolicy Bypass -File .\install-windows.ps1 -Browser Edge
```

Installer pour Brave :

```powershell
powershell -ExecutionPolicy Bypass -File .\install-windows.ps1 -ExtensionId TON_ID_EXTENSION -Browser Brave
```

Installer pour tous les navigateurs supportes :

```powershell
powershell -ExecutionPolicy Bypass -File .\install-windows.ps1 -ExtensionId TON_ID_EXTENSION -Browser All
```

Desinstaller pour Edge :

```powershell
powershell -ExecutionPolicy Bypass -File .\install-windows.ps1 -Action Uninstall -Browser Edge
```

Desinstaller pour tous les navigateurs supportes :

```powershell
powershell -ExecutionPolicy Bypass -File .\install-windows.ps1 -Action Uninstall -Browser All
```

### Emplacements Windows

L'installateur cree le manifest :

```text
extension/NativesMessages/com.amadeus.security_hub.windows.json
```

Il enregistre ensuite le host dans le registre utilisateur `HKCU`.

Emplacements utilises :

```text
HKCU\Software\Microsoft\Edge\NativeMessagingHosts\com.amadeus.security_hub
HKCU\Software\Google\Chrome\NativeMessagingHosts\com.amadeus.security_hub
HKCU\Software\Chromium\NativeMessagingHosts\com.amadeus.security_hub
HKCU\Software\BraveSoftware\Brave-Browser\NativeMessagingHosts\com.amadeus.security_hub
```

## Linux

Rendre le script executable :

```bash
chmod +x ./install-linux.sh
```

Commande generale :

```bash
./install-linux.sh --browser edge
```

Navigateurs supportes :

- `edge`
- `chrome`
- `chromium`
- `brave`
- `all`

### Exemples Linux

Installer pour Edge :

```bash
./install-linux.sh --extension-id TON_ID_EXTENSION --browser edge
```

Installer pour Edge avec l'ID stable par defaut :

```bash
./install-linux.sh --browser edge
```

Installer pour Brave :

```bash
./install-linux.sh --extension-id TON_ID_EXTENSION --browser brave
```

Installer pour tous les navigateurs supportes :

```bash
./install-linux.sh --extension-id TON_ID_EXTENSION --browser all
```

Desinstaller pour Edge :

```bash
./install-linux.sh --action uninstall --browser edge
```

Desinstaller pour tous les navigateurs supportes :

```bash
./install-linux.sh --action uninstall --browser all
```

### Emplacements Linux

L'installateur cree le manifest source :

```text
extension/NativesMessages/com.amadeus.security_hub.linux.json
```

Il copie ensuite ce manifest dans le dossier Native Messaging du navigateur choisi.

Emplacements utilises :

```text
~/.config/microsoft-edge/NativeMessagingHosts/com.amadeus.security_hub.json
~/.config/google-chrome/NativeMessagingHosts/com.amadeus.security_hub.json
~/.config/chromium/NativeMessagingHosts/com.amadeus.security_hub.json
~/.config/BraveSoftware/Brave-Browser/NativeMessagingHosts/com.amadeus.security_hub.json
```

## Fichiers Native Messaging

Le host natif se trouve dans :

```text
extension/NativesMessages/NativesPipeline.py
```

Les lanceurs sont :

```text
extension/NativesMessages/run-native-host.cmd
extension/NativesMessages/run-native-host.sh
```

Les manifests Native Messaging pointent vers ces lanceurs, pas directement vers Python. Cela permet d'utiliser en priorite le Python du virtualenv `runtime/.venv`.

## Verification

Apres installation :

1. Recharger l'extension dans le navigateur.
2. Ouvrir une page avec un champ mot de passe.
3. Cliquer dans le champ.
4. Cliquer sur `Generer`.
5. Verifier l'alerte affichee.

Si l'installation Native Messaging est correcte, l'alerte doit contenir une reponse du host natif, par exemple :

```json
{
  "ok": true,
  "response": {
    "type": "pong",
    "ok": true
  }
}
```

## Erreurs frequentes

### `Specified native messaging host not found`

Le navigateur ne trouve pas le host `com.amadeus.security_hub`.

Causes possibles :

- l'installateur n'a pas ete lance ;
- le mauvais navigateur a ete selectionne ;
- l'ID d'extension n'est pas celui de l'extension chargee ;
- l'extension n'a pas ete rechargee apres installation.

### `Access to the specified native messaging host is forbidden`

Le host existe, mais l'extension n'est pas autorisee dans `allowed_origins`.

Relancer l'installateur avec le bon ID d'extension.

### `Launcher introuvable`

Le fichier `run-native-host.cmd` ou `run-native-host.sh` est absent.

Verifier que le dossier `extension/NativesMessages` contient bien le lanceur correspondant au systeme.
