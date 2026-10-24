# Crée l'archive de rendu Moodle : iloai-soane.zip
# Contenu : fichiers suivis par git + captures du dossier audit/.
# Exclus : .git, ce script, et tout fichier de travail non suivi.
# Usage (depuis le dossier du dépôt) : powershell -ExecutionPolicy Bypass -File creer-archive.ps1
param(
  [string]$Sortie = "$env:USERPROFILE\OneDrive\Desktop\BUT MMI\2ème année\3ème semestre\iloai-soane.zip"
)
$ErrorActionPreference = 'Stop'
$racine = $PSScriptRoot
$etape = Join-Path $env:TEMP 'iloai-soane'
if (Test-Path $etape) { Remove-Item -Recurse -Force $etape }
New-Item -ItemType Directory $etape | Out-Null

Push-Location $racine
try {
  $fichiers = @(git -c core.quotepath=off ls-files) | Where-Object { $_ -ne 'creer-archive.ps1' }
  $fichiers += @(Get-ChildItem audit -File | ForEach-Object { "audit/$($_.Name)" })
  foreach ($f in ($fichiers | Sort-Object -Unique)) {
    $dest = Join-Path $etape $f
    New-Item -ItemType Directory -Force (Split-Path $dest) | Out-Null
    Copy-Item -LiteralPath (Join-Path $racine $f) $dest
  }
} finally { Pop-Location }

if (Test-Path $Sortie) { Remove-Item -Force $Sortie }
# Chemins internes avec « / » (Compress-Archive de PowerShell 5.1 met des « \ »,
# mal décompressés sous macOS et Linux).
Add-Type -AssemblyName System.IO.Compression, System.IO.Compression.FileSystem
$zip = [System.IO.Compression.ZipFile]::Open($Sortie, 'Create')
try {
  Get-ChildItem $etape -Recurse -File | ForEach-Object {
    $nom = $_.FullName.Substring($etape.Length + 1).Replace('\', '/')
    [System.IO.Compression.ZipFileExtensions]::CreateEntryFromFile($zip, $_.FullName, $nom) | Out-Null
  }
} finally { $zip.Dispose() }
Remove-Item -Recurse -Force $etape

$captures = @(Get-ChildItem (Join-Path $racine 'audit') -Filter *.png).Count
"Archive créée : $Sortie ($([math]::Round((Get-Item $Sortie).Length / 1KB)) Ko, $captures capture(s) dans audit/)"
