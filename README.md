# Amadeus Security Hub

Application desktop locale de gestion de mots de passe avec stockage sur support
USB et extension Chromium.

Le projet contient :

- `app/` : application desktop Python + pywebview.
- `extension/` : extension Chromium et host Native Messaging.
- `runtime/requirements.txt` : dependances Python.
- `install-windows.ps1` : installateur Windows.
- `install-linux.sh` : installateur Linux.

## Prerequis

### Windows

- Python 3 disponible via `py -3` ou `python`.
- PowerShell.
- Un navigateur Chromium supporte : Edge, Chrome, Chromium ou Brave.

### Linux

- Python 3.
- Module `venv` de Python, souvent fourni par `python3-venv`.
- `udisksctl` si l'application doit monter automatiquement les partitions USB.
- Un navigateur Chromium supporte : Edge, Chrome, Chromium ou Brave.

## Charger l'extension dans le navigateur

Dans le navigateur choisi :

1. Ouvrir la page des extensions :
   - Edge : `edge://extensions`
   - Chrome : `chrome://extensions`
   - Chromium : `chrome://extensions`
   - Brave : `brave://extensions`
2. Activer le mode developpeur.
3. Charger une extension non empaquetee.
4. Selectionner le dossier `extension/`.

Le manifest contient une cle stable. L'ID attendu par defaut est :

```text
olgcbmgnoainnpfchiakbfcidhpcgdmo
```

Si le navigateur affiche un autre ID, passe cet ID a l'installateur avec
`--extension-id` sous Linux ou `-ExtensionId` sous Windows.

## Installation avec installateur

Les installateurs creent le virtualenv, installent les dependances Python,
generent le manifest Native Messaging, puis enregistrent le host natif pour le
navigateur choisi.

### Windows

Depuis la racine du depot :

```powershell
powershell -ExecutionPolicy Bypass -File .\install-windows.ps1 -Browser Edge
```

Navigateurs acceptes :

```text
Edge, Chrome, Chromium, Brave, All
```

Exemples :

```powershell
powershell -ExecutionPolicy Bypass -File .\install-windows.ps1 -Browser Brave
powershell -ExecutionPolicy Bypass -File .\install-windows.ps1 -Browser All
powershell -ExecutionPolicy Bypass -File .\install-windows.ps1 -ExtensionId TON_ID_EXTENSION -Browser Brave
```

Desinstallation :

```powershell
powershell -ExecutionPolicy Bypass -File .\install-windows.ps1 -Action Uninstall -Browser Brave
```

### Linux

Depuis la racine du depot :

```bash
chmod +x ./install-linux.sh
./install-linux.sh --browser brave
```

Navigateurs acceptes :

```text
edge, chrome, chromium, brave, all
```

Exemples :

```bash
./install-linux.sh --browser brave
./install-linux.sh --browser all
./install-linux.sh --extension-id TON_ID_EXTENSION --browser brave
```

Desinstallation :

```bash
./install-linux.sh --action uninstall --browser brave
```

## Installation manuelle sans installateur

Cette section fait la meme chose que les installateurs, mais etape par etape.

### Windows manuel

Depuis la racine du depot :

```powershell
py -3 -m venv runtime\.venv
.\runtime\.venv\Scripts\python.exe -m pip install --upgrade pip
.\runtime\.venv\Scripts\python.exe -m pip install --upgrade -r runtime\requirements.txt
```

Creer le manifest Native Messaging :

```powershell
$hostName = "com.amadeus.security_hub"
$extensionId = "olgcbmgnoainnpfchiakbfcidhpcgdmo"
$launcherPath = (Resolve-Path ".\extension\NativesMessages\run-native-host.cmd").Path
$manifestPath = (Join-Path (Resolve-Path ".\extension\NativesMessages").Path "$hostName.windows.json")

$manifest = [ordered]@{
  name = $hostName
  description = "Amadeus Security Hub native messaging host"
  path = $launcherPath
  type = "stdio"
  allowed_origins = @("chrome-extension://$extensionId/")
}

$manifest | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath $manifestPath -Encoding UTF8
```

Enregistrer le host pour le navigateur voulu :

```powershell
$manifestPath = (Resolve-Path ".\extension\NativesMessages\com.amadeus.security_hub.windows.json").Path

# Edge
reg add "HKCU\Software\Microsoft\Edge\NativeMessagingHosts\com.amadeus.security_hub" /ve /t REG_SZ /d $manifestPath /f

# Chrome
reg add "HKCU\Software\Google\Chrome\NativeMessagingHosts\com.amadeus.security_hub" /ve /t REG_SZ /d $manifestPath /f

# Chromium
reg add "HKCU\Software\Chromium\NativeMessagingHosts\com.amadeus.security_hub" /ve /t REG_SZ /d $manifestPath /f

# Brave
reg add "HKCU\Software\BraveSoftware\Brave-Browser\NativeMessagingHosts\com.amadeus.security_hub" /ve /t REG_SZ /d $manifestPath /f
```

### Linux manuel

Depuis la racine du depot :

```bash
python3 -m venv runtime/.venv
runtime/.venv/bin/python -m pip install --upgrade pip
runtime/.venv/bin/python -m pip install --upgrade -r runtime/requirements.txt
chmod +x extension/NativesMessages/run-native-host.sh
```

Creer le manifest Native Messaging :

```bash
HOST_NAME="com.amadeus.security_hub"
EXTENSION_ID="olgcbmgnoainnpfchiakbfcidhpcgdmo"
REPO_ROOT="$(pwd)"
NATIVE_DIR="$REPO_ROOT/extension/NativesMessages"
LAUNCHER_PATH="$NATIVE_DIR/run-native-host.sh"
MANIFEST_PATH="$NATIVE_DIR/$HOST_NAME.linux.json"

cat > "$MANIFEST_PATH" <<EOF
{
  "name": "$HOST_NAME",
  "description": "Amadeus Security Hub native messaging host",
  "path": "$LAUNCHER_PATH",
  "type": "stdio",
  "allowed_origins": [
    "chrome-extension://$EXTENSION_ID/"
  ]
}
EOF
```

Copier le manifest dans le dossier du navigateur voulu :

```bash
# Edge
mkdir -p "$HOME/.config/microsoft-edge/NativeMessagingHosts"
cp "$MANIFEST_PATH" "$HOME/.config/microsoft-edge/NativeMessagingHosts/$HOST_NAME.json"

# Chrome
mkdir -p "$HOME/.config/google-chrome/NativeMessagingHosts"
cp "$MANIFEST_PATH" "$HOME/.config/google-chrome/NativeMessagingHosts/$HOST_NAME.json"

# Chromium
mkdir -p "$HOME/.config/chromium/NativeMessagingHosts"
cp "$MANIFEST_PATH" "$HOME/.config/chromium/NativeMessagingHosts/$HOST_NAME.json"

# Brave
mkdir -p "$HOME/.config/BraveSoftware/Brave-Browser/NativeMessagingHosts"
cp "$MANIFEST_PATH" "$HOME/.config/BraveSoftware/Brave-Browser/NativeMessagingHosts/$HOST_NAME.json"
```

## Lancer l'application

Depuis la racine du depot, lance l'application avec `app/` comme repertoire de
travail. C'est important car les pages HTML sont chargees avec des chemins
relatifs comme `Frontend/Html/Login.html`.

### Windows

```powershell
cd app
..\runtime\.venv\Scripts\python.exe main.py
```

### Linux

```bash
cd app
../runtime/.venv/bin/python main.py
```

L'application doit etre lancee et deverrouillee pour que l'extension puisse
lire ou enregistrer des mots de passe.

## Verification rapide

1. Installer les dependances et le host Native Messaging.
2. Charger l'extension dans le navigateur.
3. Lancer l'application desktop.
4. Inserer ou initialiser une cle USB Security Hub.
5. Se connecter avec le mot de passe maitre.
6. Ouvrir une page avec un champ mot de passe.
7. Cliquer dans le champ.
8. Verifier que le panneau de l'extension apparait.

Si le navigateur affiche `Specified native messaging host not found`, le host
Native Messaging n'est pas enregistre pour le bon navigateur ou le bon ID
d'extension.

Si l'extension repond `ipc_unavailable`, l'application desktop n'est pas lancee,
n'est pas deverrouillee, ou le serveur IPC local n'est pas disponible.

## Tests

Depuis la racine du depot :

```bash
PYTHONDONTWRITEBYTECODE=1 python -m unittest discover -s test
```
