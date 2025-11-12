param(
    [string]$PlatformDir,
    [string]$Platform,
    [string]$Arch
)

function Get-EnvValue([string]$name) {
    return [Environment]::GetEnvironmentVariable($name)
}

function Require-Env([string]$name) {
    if (-not (Get-EnvValue $name)) {
        Write-Error "$name environment variable is not set."
        exit 2
    }
}

Require-Env 'FFMPEG_URL'
Require-Env 'MP4DECRYPT_URL'
Require-Env 'N_M3U8DL_RE_URL'

New-Item -ItemType Directory -Force -Path $PlatformDir | Out-Null

function Verify-Checksum([string]$filePath, [string]$envName) {
    $expected = Get-EnvValue $envName
    if ([string]::IsNullOrEmpty($expected)) { return $true }
    $hash = (Get-FileHash -Algorithm SHA256 -Path $filePath).Hash
    if ($hash.ToLower() -ne $expected.ToLower()) {
        Write-Error "Checksum mismatch for $filePath: expected $expected but got $hash"
        return $false
    }
    Write-Host "Checksum OK for $filePath"
    return $true
}

Write-Host "Downloading ffmpeg from $($(Get-EnvValue 'FFMPEG_URL'))"
$ff = Join-Path $env:TEMP "ff.tmp"
Invoke-WebRequest -Uri (Get-EnvValue 'FFMPEG_URL') -OutFile $ff
if (-not (Verify-Checksum $ff 'FFMPEG_SHA256')) { exit 3 }
try {
    Expand-Archive -LiteralPath $ff -DestinationPath "$env:TEMP\ff_ex" -Force -ErrorAction Stop
    Get-ChildItem -Path "$env:TEMP\ff_ex" -Recurse -Filter "ffmpeg*" | ForEach-Object {
        Copy-Item $_.FullName -Destination $PlatformDir -Force
    }
} catch {
    # fallback: assume it's a direct binary
    Copy-Item $ff -Destination (Join-Path $PlatformDir "ffmpeg.exe") -Force
}

Write-Host "Downloading mp4decrypt from $($(Get-EnvValue 'MP4DECRYPT_URL'))"
$mp = Join-Path $env:TEMP "mp4d.tmp"
Invoke-WebRequest -Uri (Get-EnvValue 'MP4DECRYPT_URL') -OutFile $mp
if (-not (Verify-Checksum $mp 'MP4DECRYPT_SHA256')) { exit 3 }
try {
    Expand-Archive -LiteralPath $mp -DestinationPath "$env:TEMP\mp4d_ex" -Force -ErrorAction Stop
    Get-ChildItem -Path "$env:TEMP\mp4d_ex" -Recurse -Include "mp4decrypt*" | ForEach-Object {
        Copy-Item $_.FullName -Destination $PlatformDir -Force
    }
} catch {
    Copy-Item $mp -Destination (Join-Path $PlatformDir "mp4decrypt.exe") -Force
}

Write-Host "Downloading N_m3u8DL-RE from $($(Get-EnvValue 'N_M3U8DL_RE_URL'))"
$nm = Join-Path $env:TEMP "nm.tmp"
Invoke-WebRequest -Uri (Get-EnvValue 'N_M3U8DL_RE_URL') -OutFile $nm
if (-not (Verify-Checksum $nm 'N_M3U8DL_RE_SHA256')) { exit 3 }
try {
    Expand-Archive -LiteralPath $nm -DestinationPath "$env:TEMP\nm_ex" -Force -ErrorAction Stop
    Get-ChildItem -Path "$env:TEMP\nm_ex" -Recurse -Include "N_m3u8DL-RE*" | ForEach-Object {
        Copy-Item $_.FullName -Destination $PlatformDir -Force
    }
} catch {
    Copy-Item $nm -Destination (Join-Path $PlatformDir "N_m3u8DL-RE.exe") -Force
}

Get-ChildItem -Path $PlatformDir | Format-Table
param(
    param(
        [string]$PlatformDir,
        [string]$Platform,
        [string]$Arch
    )

    if (-not $env:FFMPEG_URL) {
        Write-Error "FFMPEG_URL environment variable is not set."
        exit 2
    }
    if (-not $env:MP4DECRYPT_URL) {
        Write-Error "MP4DECRYPT_URL environment variable is not set."
        exit 2
    }
    if (-not $env:N_M3U8DL_RE_URL) {
        Write-Error "N_M3U8DL_RE_URL environment variable is not set."
        exit 2
    }

    New-Item -ItemType Directory -Force -Path $PlatformDir | Out-Null

    Write-Host "Downloading ffmpeg from $($env:FFMPEG_URL)"
    $ff = Join-Path $env:TEMP "ff.zip"
    Invoke-WebRequest -Uri $env:FFMPEG_URL -OutFile $ff
    try {
        Expand-Archive -LiteralPath $ff -DestinationPath "$env:TEMP\ff_ex" -Force
        Get-ChildItem -Path "$env:TEMP\ff_ex" -Recurse -Filter "ffmpeg*" | ForEach-Object {
            Copy-Item $_.FullName -Destination $PlatformDir -Force
        }
    } catch {
        # fallback: assume it's a direct binary
        Copy-Item $ff -Destination (Join-Path $PlatformDir "ffmpeg.exe") -Force
    }

    Write-Host "Downloading mp4decrypt from $($env:MP4DECRYPT_URL)"
    $mp = Join-Path $env:TEMP "mp4d.zip"
    Invoke-WebRequest -Uri $env:MP4DECRYPT_URL -OutFile $mp
    try {
        Expand-Archive -LiteralPath $mp -DestinationPath "$env:TEMP\mp4d_ex" -Force
        Get-ChildItem -Path "$env:TEMP\mp4d_ex" -Recurse -Include "mp4decrypt*" | ForEach-Object {
            Copy-Item $_.FullName -Destination $PlatformDir -Force
        }
    } catch {
        Copy-Item $mp -Destination (Join-Path $PlatformDir "mp4decrypt.exe") -Force
    }

    Write-Host "Downloading N_m3u8DL-RE from $($env:N_M3U8DL_RE_URL)"
    $nm = Join-Path $env:TEMP "nm.zip"
    Invoke-WebRequest -Uri $env:N_M3U8DL_RE_URL -OutFile $nm
    try {
        Expand-Archive -LiteralPath $nm -DestinationPath "$env:TEMP\nm_ex" -Force
        Get-ChildItem -Path "$env:TEMP\nm_ex" -Recurse -Include "N_m3u8DL-RE*" | ForEach-Object {
            Copy-Item $_.FullName -Destination $PlatformDir -Force
        }
    } catch {
        Copy-Item $nm -Destination (Join-Path $PlatformDir "N_m3u8DL-RE.exe") -Force
    }

    Get-ChildItem -Path $PlatformDir | Format-Table
    [string]$Platform,
    [string]$Arch
)

if (-not $env:FFMPEG_URL) {
    Write-Error "FFMPEG_URL environment variable is not set."
    exit 2
}
if (-not $env:MP4DECRYPT_URL) {
    Write-Error "MP4DECRYPT_URL environment variable is not set."
    exit 2
}
if (-not $env:N_M3U8DL_RE_URL) {
    Write-Error "N_M3U8DL_RE_URL environment variable is not set."
    exit 2
}

New-Item -ItemType Directory -Force -Path $PlatformDir | Out-Null

Write-Host "Downloading ffmpeg from $($env:FFMPEG_URL)"
$ff = Join-Path $env:TEMP "ff.zip"
Invoke-WebRequest -Uri $env:FFMPEG_URL -OutFile $ff
try {
    Expand-Archive -LiteralPath $ff -DestinationPath "$env:TEMP\ff_ex" -Force
    Get-ChildItem -Path "$env:TEMP\ff_ex" -Recurse -Filter "ffmpeg*" | ForEach-Object {
        Copy-Item $_.FullName -Destination $PlatformDir -Force
    }
