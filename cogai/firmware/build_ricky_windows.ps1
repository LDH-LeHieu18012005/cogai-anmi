param(
    [string]$TaskRoot = 'F:\DELL\CogAI-AnMi-S3',
    [switch]$ReuseBuild,
    [string]$OutputName = 'output-ricky-20261031'
)

$ErrorActionPreference = 'Stop'
$firmwareRoot = $PSScriptRoot
$workspaceRoot = (Resolve-Path (Join-Path $firmwareRoot '../..')).Path
$pythonRoot = Join-Path $workspaceRoot '.tools/python/cpython-3.12.10-windows-x86_64-none'
$pythonExe = Join-Path $pythonRoot 'python.exe'
$idfRoot = Join-Path $TaskRoot 'esp-idf'
$sourceRoot = Join-Path $TaskRoot 'source/firmware'
if ($OutputName -notmatch '^[a-zA-Z0-9_-]+$') { throw 'OutputName must be a directory name.' }
$outputRoot = Join-Path $TaskRoot $OutputName
$env:PATH = "$pythonRoot;$pythonRoot\Scripts;$env:PATH"
$env:IDF_PATH = $idfRoot
$env:IDF_TOOLS_PATH = Join-Path $TaskRoot 'tools'
$env:PYTHONUTF8 = '1'
$env:PYTHONIOENCODING = 'utf-8'
$env:PYTHONUNBUFFERED = '1'
$env:IDF_CCACHE_ENABLE = '0'

function Assert-Exit([string]$Step) {
    if ($LASTEXITCODE -ne 0) { throw "$Step failed with exit code $LASTEXITCODE" }
}

if (-not $ReuseBuild) {
Write-Output 'STAGE install ESP32-S3 tools'
& $pythonExe "$idfRoot/tools/idf_tools.py" --idf-path $idfRoot install --targets esp32s3
Assert-Exit 'Tool installation'

Write-Output 'STAGE install ESP-IDF Python dependencies'
& $pythonExe "$idfRoot/tools/idf_tools.py" --idf-path $idfRoot install-python-env --features core
Assert-Exit 'Python environment installation'
}

Write-Output 'STAGE activate ESP-IDF'
. "$idfRoot/export.ps1"
Assert-Exit 'ESP-IDF activation'

if ($ReuseBuild) {
    Write-Output 'STAGE update canonical Ricky board in existing build checkout'
    if (-not (Test-Path -LiteralPath $sourceRoot)) { throw 'No existing source checkout to reuse.' }
    foreach ($name in @('config.json', 'ricky_war_tank.cc')) {
        $relative = "main/boards/ricky-war-tank/$name"
        Copy-Item -LiteralPath (Join-Path "$firmwareRoot/xiaozhi-esp32" $relative) -Destination (Join-Path $sourceRoot $relative)
    }
} else {
Write-Output 'STAGE unpack verified source package'
if (Test-Path -LiteralPath $sourceRoot) {
    throw "Source directory already exists: $sourceRoot. Preserve it and select a fresh build directory."
}
Expand-Archive -LiteralPath (Join-Path $firmwareRoot 'dist/anmi-ricky-source.zip') -DestinationPath (Join-Path $TaskRoot 'source')
}

$env:FIRMWARE_SOURCE_REVISION = 'c435f99a88066029ec2dbd2d758c8cc9d051565b'
Write-Output 'STAGE compile Ricky AnMi Vietnamese, wake word disabled'
& python "$sourceRoot/docker/firmware-builder/firmware_builder.py" --source-dir $sourceRoot --output-dir $outputRoot --board-dir ricky-war-tank --board-name ricky-war-tank --language vi-VN --wake-word disabled
Assert-Exit 'Firmware compilation'

Write-Output 'STAGE verify firmware artifacts'
& python (Join-Path $firmwareRoot 'verify_firmware.py') $outputRoot
Assert-Exit 'Firmware verification'

$destination = Join-Path $firmwareRoot $OutputName
New-Item -ItemType Directory -Force -Path $destination | Out-Null
Copy-Item -Path "$outputRoot/*" -Destination $destination
Write-Output "BUILD SUCCEEDED: $destination"
Write-Output 'No flash command has been executed by this build script.'
