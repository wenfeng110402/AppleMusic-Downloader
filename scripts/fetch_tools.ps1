param(
    [string]$PlatformDir,
    [string]$Platform,
    [string]$Arch
)

function Get-EnvValue([string]$name) {
    return [Environment]::GetEnvironmentVariable($name)
}

function Test-Checksum([string]$filePath, [string]$envName) {
    $expected = Get-EnvValue $envName
    if ([string]::IsNullOrEmpty($expected)) { return $true }
    $hash = (Get-FileHash -Algorithm SHA256 -Path $filePath).Hash
    if ($hash.ToLower() -ne $expected.ToLower()) {
        Write-Error "Checksum mismatch for ${filePath}: expected ${expected} but got ${hash}"
        return $false
    }
    Write-Host "Checksum OK for ${filePath}"
    return $true
}

New-Item -ItemType Directory -Force -Path $PlatformDir | Out-Null

# Helper to download and extract/copy a package if the env URL is provided
function Invoke-FetchAndExtract([string]$envUrlName, [string]$envShaName, [string]$fileFilter, [string]$fallbackName) {
    $url = Get-EnvValue $envUrlName
    if ([string]::IsNullOrEmpty($url)) {
        Write-Host "${envUrlName} not set; skipping ${fallbackName}"
        return
    }
    Write-Host "Downloading ${fallbackName} from $url"
    $tmp = Join-Path $env:TEMP ([System.IO.Path]::GetRandomFileName())
    Invoke-WebRequest -Uri $url -OutFile $tmp -UseBasicParsing
    if (-not (Test-Checksum $tmp $envShaName)) { exit 3 }
    try {
        Expand-Archive -LiteralPath $tmp -DestinationPath "$env:TEMP\${fallbackName}_ex" -Force -ErrorAction Stop
        Get-ChildItem -Path "$env:TEMP\${fallbackName}_ex" -Recurse -Filter $fileFilter | ForEach-Object {
            Copy-Item $_.FullName -Destination $PlatformDir -Force
        }
    } catch {
        # fallback: assume it's a direct binary
        Copy-Item $tmp -Destination (Join-Path $PlatformDir $fallbackName) -Force
    }
}

Invoke-FetchAndExtract 'FFMPEG_URL' 'FFMPEG_SHA256' 'ffmpeg*' 'ffmpeg.exe'
Invoke-FetchAndExtract 'MP4DECRYPT_URL' 'MP4DECRYPT_SHA256' 'mp4decrypt*' 'mp4decrypt.exe'
Invoke-FetchAndExtract 'N_M3U8DL_RE_URL' 'N_M3U8DL_RE_SHA256' 'N_m3u8DL-RE*' 'N_m3u8DL-RE.exe'

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
