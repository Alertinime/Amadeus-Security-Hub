param(
  [ValidateSet("Install", "Uninstall")]
  [string] $Action = "Install",

  [ValidatePattern('^[a-p]{32}$')]
  [string] $ExtensionId = "olgcbmgnoainnpfchiakbfcidhpcgdmo",

  [ValidateSet("Edge", "Chrome", "Chromium", "Brave", "All", "Both")]
  [string] $Browser = "Edge"
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$runtimeDir = Join-Path $repoRoot "runtime"
$venvDir = Join-Path $runtimeDir ".venv"
$requirementsPath = Join-Path $runtimeDir "requirements.txt"
$nativeDir = Join-Path $repoRoot "extension\NativesMessages"
$hostName = "com.amadeus.security_hub"
$launcherPath = Join-Path $nativeDir "run-native-host.cmd"
$manifestPath = Join-Path $nativeDir "$hostName.windows.json"

function Invoke-Python {
  param(
    [Parameter(Mandatory = $true)]
    [string[]] $Arguments
  )

  if (Get-Command py -ErrorAction SilentlyContinue) {
    & py -3 @Arguments
    return
  }

  if (Get-Command python -ErrorAction SilentlyContinue) {
    & python @Arguments
    return
  }

  throw "Python est introuvable. Installe Python 3 puis relance cet installateur."
}

function Register-NativeHost {
  param(
    [Parameter(Mandatory = $true)]
    [string] $RegistryPath
  )

  & reg.exe add $RegistryPath /ve /t REG_SZ /d $manifestPath /f | Out-Null
}

function Unregister-NativeHost {
  param(
    [Parameter(Mandatory = $true)]
    [string] $RegistryPath
  )

  $previousErrorActionPreference = $ErrorActionPreference
  $ErrorActionPreference = "Continue"

  try {
    & reg.exe query $RegistryPath 2>$null | Out-Null
    if ($LASTEXITCODE -ne 0) {
      return
    }

    & reg.exe delete $RegistryPath /f 2>$null | Out-Null
    if ($LASTEXITCODE -ne 0) {
      throw "Impossible de supprimer la cle registre: $RegistryPath"
    }
  } finally {
    $ErrorActionPreference = $previousErrorActionPreference
  }
}

function Get-SelectedBrowsers {
  if ($Browser -eq "All") {
    return @("Edge", "Chrome", "Chromium", "Brave")
  }

  if ($Browser -eq "Both") {
    return @("Edge", "Chrome")
  }

  return @($Browser)
}

function Get-NativeHostRegistryPath {
  param(
    [Parameter(Mandatory = $true)]
    [string] $BrowserName
  )

  switch ($BrowserName) {
    "Edge" { return "HKCU\Software\Microsoft\Edge\NativeMessagingHosts\$hostName" }
    "Chrome" { return "HKCU\Software\Google\Chrome\NativeMessagingHosts\$hostName" }
    "Chromium" { return "HKCU\Software\Chromium\NativeMessagingHosts\$hostName" }
    "Brave" { return "HKCU\Software\BraveSoftware\Brave-Browser\NativeMessagingHosts\$hostName" }
    default { throw "Navigateur non supporte: $BrowserName" }
  }
}

if ($Action -eq "Uninstall") {
  foreach ($browserName in Get-SelectedBrowsers) {
    Unregister-NativeHost -RegistryPath (Get-NativeHostRegistryPath -BrowserName $browserName)
  }

  if (Test-Path $manifestPath) {
    Remove-Item -Path $manifestPath -Force
  }

  Write-Output "Desinstallation Windows terminee."
  Write-Output "Host Native Messaging retire: $hostName"
  exit 0
}

if (-not (Test-Path $requirementsPath)) {
  throw "requirements.txt introuvable: $requirementsPath"
}

if (-not (Test-Path $nativeDir)) {
  New-Item -ItemType Directory -Path $nativeDir -Force | Out-Null
}

if (-not (Test-Path $launcherPath)) {
  throw "Launcher introuvable: $launcherPath"
}

Invoke-Python -Arguments @("-m", "venv", $venvDir)

$venvPython = Join-Path $venvDir "Scripts\python.exe"
if (-not (Test-Path $venvPython)) {
  throw "Python du virtualenv introuvable: $venvPython"
}

& $venvPython -m pip install --upgrade pip
& $venvPython -m pip install --upgrade -r $requirementsPath

$manifest = [ordered]@{
  name = $hostName
  description = "Amadeus Security Hub native messaging host"
  path = $launcherPath
  type = "stdio"
  allowed_origins = @("chrome-extension://$ExtensionId/")
}

$manifest | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath $manifestPath -Encoding UTF8

foreach ($browserName in Get-SelectedBrowsers) {
  Register-NativeHost -RegistryPath (Get-NativeHostRegistryPath -BrowserName $browserName)
}

Write-Output "Installation Windows terminee."
Write-Output "Virtualenv: $venvDir"
Write-Output "Host Native Messaging: $hostName"
Write-Output "Manifest: $manifestPath"
Write-Output "Extension autorisee: chrome-extension://$ExtensionId/"
