[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidateNotNullOrEmpty()]
    [string]$TechnicianName,

    [Parameter(Mandatory = $true)]
    [ValidateNotNullOrEmpty()]
    [string]$ItecsAccount,

    [string]$ConfigPath = (Join-Path $env:USERPROFILE ".codex\halopsa-mcp\config.json"),

    [switch]$Force
)

$ErrorActionPreference = "Stop"
$BaseUrl = "https://halopsa.itecs.io/api"
$TokenUrl = "https://halopsa.itecs.io/auth/token"

function Stop-Setup {
    param([Parameter(Mandatory = $true)][string]$Message)
    throw "HaloPSA setup failed: $Message"
}

if ([Environment]::OSVersion.Platform -ne [PlatformID]::Win32NT) {
    Stop-Setup "this configurator supports Windows only"
}
if ([string]::IsNullOrWhiteSpace($env:USERPROFILE)) {
    Stop-Setup "USERPROFILE is required"
}
if ($TechnicianName.Length -gt 100 -or $TechnicianName -match '[\r\n\t/\\"]') {
    Stop-Setup "technician name is empty, too long, or contains an unsupported character"
}
if ($ItecsAccount -match '[\r\n\t"]') {
    Stop-Setup "ITECS 1Password account contains an unsupported character"
}
if ((Test-Path -LiteralPath $ConfigPath) -and -not $Force) {
    Stop-Setup "config already exists at $ConfigPath; rerun with -Force to replace it"
}

$OpCommand = Get-Command op -CommandType Application -ErrorAction SilentlyContinue | Select-Object -First 1
if ($null -eq $OpCommand) {
    Stop-Setup "1Password CLI op.exe is not installed or is not on PATH"
}
$OpPath = $OpCommand.Source
$ItemTitle = "GO-MCP HaloPSA $TechnicianName Read Write"
$VaultPrefix = "op://Automation Vault/$ItemTitle"

function Read-OpField {
    param([Parameter(Mandatory = $true)][string]$Field)

    $Value = & $OpPath --account $ItecsAccount read "$VaultPrefix/$Field" 2>$null
    if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($Value)) {
        Stop-Setup "Automation Vault item '$ItemTitle' is missing, inaccessible, or incomplete at field $Field"
    }
    return ($Value -join "`n").TrimEnd([char[]]"`r`n")
}

$HaloClientId = Read-OpField "HALO_CLIENT_ID"
$HaloClientSecret = Read-OpField "HALO_CLIENT_SECRET"
$HaloScope = Read-OpField "HALO_SCOPE"
$HaloAgent = Read-OpField "HALO_AGENT"
$VaultBaseUrl = Read-OpField "HALO_BASE_URL"
$VaultTokenUrl = Read-OpField "HALO_TOKEN_URL"

if ($HaloAgent -cne $TechnicianName) {
    Stop-Setup "HALO_AGENT does not match technician '$TechnicianName'"
}
if ($VaultBaseUrl -cne $BaseUrl) {
    Stop-Setup "HALO_BASE_URL is not the approved ITECS HaloPSA API URL"
}
if ($VaultTokenUrl -cne $TokenUrl) {
    Stop-Setup "HALO_TOKEN_URL is not the approved ITECS HaloPSA token URL"
}

$Scopes = @($HaloScope -split '\s+' | Where-Object { $_ })
if ($Scopes -notcontains "read:tickets") {
    Stop-Setup "HALO_SCOPE is missing read:tickets"
}
if ($Scopes -notcontains "edit:tickets") {
    Stop-Setup "HALO_SCOPE is missing edit:tickets"
}
if ($Scopes -contains "read:crm" -or $Scopes -contains "read:distributionlists") {
    Stop-Setup "HALO_SCOPE contains a prohibited broad read scope"
}

try {
    $TokenResponse = Invoke-WebRequest -UseBasicParsing -Uri $TokenUrl -Method Post -ContentType "application/x-www-form-urlencoded" -Body @{
        grant_type    = "client_credentials"
        client_id     = $HaloClientId
        client_secret = $HaloClientSecret
        scope         = $HaloScope
    }
    if ([int]$TokenResponse.StatusCode -ne 200) {
        Stop-Setup "HaloPSA OAuth validation returned HTTP $($TokenResponse.StatusCode) for '$ItemTitle'"
    }
}
catch {
    Stop-Setup "HaloPSA OAuth validation failed for '$ItemTitle'"
}

$Config = [ordered]@{
    servers = @(
        [ordered]@{
            id                    = "itecs-halopsa"
            name                  = "ITECS HaloPSA"
            base_url              = $BaseUrl
            token_url             = $TokenUrl
            client_id_command     = @($OpPath, "--account", $ItecsAccount, "read", "$VaultPrefix/HALO_CLIENT_ID")
            client_secret_command = @($OpPath, "--account", $ItecsAccount, "read", "$VaultPrefix/HALO_CLIENT_SECRET")
            scope_command         = @($OpPath, "--account", $ItecsAccount, "read", "$VaultPrefix/HALO_SCOPE")
            timeout_seconds       = 30
            max_attempts          = 3
            default_page_size     = 25
        }
    )
}

$ConfigDirectory = Split-Path -Parent $ConfigPath
if ([string]::IsNullOrWhiteSpace($ConfigDirectory)) {
    Stop-Setup "config path must include a parent directory"
}
[IO.Directory]::CreateDirectory($ConfigDirectory) | Out-Null
$TemporaryConfig = Join-Path $ConfigDirectory (".halopsa-config-{0}.tmp" -f [Guid]::NewGuid().ToString("N"))

try {
    $Json = $Config | ConvertTo-Json -Depth 8
    [IO.File]::WriteAllText($TemporaryConfig, $Json + [Environment]::NewLine, [Text.UTF8Encoding]::new($false))
    if ((Test-Path -LiteralPath $ConfigPath) -and -not $Force) {
        Stop-Setup "config appeared at $ConfigPath during setup; no file was replaced"
    }
    Move-Item -LiteralPath $TemporaryConfig -Destination $ConfigPath -Force
}
finally {
    if (Test-Path -LiteralPath $TemporaryConfig) {
        Remove-Item -LiteralPath $TemporaryConfig -Force
    }
    $HaloClientId = $null
    $HaloClientSecret = $null
    $HaloScope = $null
    $TokenResponse = $null
}

Write-Host "HaloPSA OAuth validated for $ItemTitle."
Write-Host "Command-backed config written to $ConfigPath. Restart Codex Desktop and start a new task."
