# Native PowerShell 5.1 test. All credentials and OAuth responses are synthetic.
$ErrorActionPreference = 'Stop'
$Setup = Join-Path $PSScriptRoot 'configure-halopsa-mcp-windows.ps1'
$Scratch = Join-Path ([IO.Path]::GetTempPath()) ("Halo Tech O'Neil " + [Guid]::NewGuid().ToString('N'))
[IO.Directory]::CreateDirectory($Scratch) | Out-Null
$OriginalPath = $env:PATH
$OriginalMode = $env:HALOPSA_SETUP_TEST_MODE
$global:HaloSetupTestOAuthCalls = 0

function Invoke-WebRequest {
    param([switch]$UseBasicParsing, $TimeoutSec, $Uri, $Method, $ContentType, $Body)
    if ($Uri -ne 'https://halopsa.itecs.io/auth/token' -or $Method -ne 'Post' -or
        $Body.client_id -ne 'synthetic-id' -or $Body.client_secret -ne 'synthetic-secret') {
        throw 'Unexpected synthetic OAuth request'
    }
    $global:HaloSetupTestOAuthCalls++
    if ($env:HALOPSA_SETUP_TEST_MODE -eq 'oauth-failure') { throw 'Synthetic OAuth rejection' }
    return @{ StatusCode = 200 }
}

function Expect-Failure {
    param([scriptblock]$Action, [string]$Expected)
    try { & $Action | Out-Null } catch {
        if ($_.Exception.Message.Contains('synthetic-sensitive-error')) { throw 'Setup repeated credential-wrapper output' }
        if ($_.Exception.Message -notlike "*$Expected*") { throw }
        return
    }
    throw "Expected setup failure: $Expected"
}

try {
    $Wrapper = Join-Path $Scratch 'op-itecs.ps1'
    $Stub = @'
param([string]$Operation, [string]$Reference)
if ($Operation -ne 'read' -or $Reference -notlike "op://Automation Vault/GO-MCP HaloPSA O'Neil Read Write/*") { exit 9 }
$Field = ($Reference -split '/')[-1]
if ($env:HALOPSA_SETUP_TEST_MODE -eq 'wrapper-failure' -and $Field -eq 'HALO_CLIENT_SECRET') {
    [Console]::Out.WriteLine('synthetic-sensitive-error')
    [Console]::Error.WriteLine('synthetic-sensitive-error')
    exit 8
}
switch ($Field) {
    HALO_CLIENT_ID { 'synthetic-id' }
    HALO_CLIENT_SECRET { 'synthetic-secret' }
    HALO_SCOPE {
        if ($env:HALOPSA_SETUP_TEST_MODE -eq 'bad-scope') { 'read:distributionlists' } else { 'read:tickets edit:tickets' }
    }
    HALO_AGENT { if ($env:HALOPSA_SETUP_TEST_MODE -eq 'wrong-agent') { 'Other' } else { "O'Neil" } }
    HALO_BASE_URL { if ($env:HALOPSA_SETUP_TEST_MODE -eq 'wrong-url') { 'https://example.invalid' } else { 'https://halopsa.itecs.io/api' } }
    HALO_TOKEN_URL { 'https://halopsa.itecs.io/auth/token' }
    default { exit 7 }
}
'@
    [IO.File]::WriteAllText($Wrapper, $Stub, [Text.UTF8Encoding]::new($false))
    $Batch = Join-Path $Scratch 'op-itecs.cmd'
    [IO.File]::WriteAllText($Batch, "@echo off`r`npowershell.exe -NoLogo -NoProfile -NonInteractive -File `"%~dp0op-itecs.ps1`" %*`r`nexit /b %errorlevel%`r`n", [Text.ASCIIEncoding]::new())
    $ConfigPath = Join-Path $Scratch 'profile\config.json'
    foreach ($Command in @($Wrapper, $Batch)) {
        $env:HALOPSA_SETUP_TEST_MODE = ''
        & $Setup -TechnicianName "O'Neil" -OpCommand $Command -ConfigPath $ConfigPath -Force | Out-Null
        $Raw = [IO.File]::ReadAllText($ConfigPath)
        if ($Raw.Contains('synthetic-id') -or $Raw.Contains('synthetic-secret')) { throw 'Resolved credential persisted' }
        if ([IO.File]::ReadAllBytes($ConfigPath)[0] -eq 239) { throw 'Config contains a UTF-8 BOM' }
        $Config = $Raw | ConvertFrom-Json
        $Server = $Config.servers[0]
        foreach ($Key in @('client_id_command', 'client_secret_command', 'scope_command')) {
            $Args = @($Server.$Key)
            $Output = & $Args[0] $Args[1..($Args.Length - 1)]
            if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace(($Output -join ''))) { throw 'Generated command failed' }
            if ($Key -eq 'client_id_command' -and $Output -ne 'synthetic-id') { throw 'Generated command changed the field' }
            if ($Key -eq 'client_secret_command' -and $Output -ne 'synthetic-secret') { throw 'Generated command changed the field' }
        }
        $Discovery = & python -X utf8 (Join-Path $PSScriptRoot 'doctor.py') --discover --config $ConfigPath
        if ($LASTEXITCODE -ne 0 -or ($Discovery | ConvertFrom-Json).discovery -ne 'ok') {
            throw 'The native Go connector could not execute the generated credential commands'
        }
        $Before = [IO.File]::ReadAllText($ConfigPath)
        Expect-Failure { & $Setup -TechnicianName "O'Neil" -OpCommand $Command -ConfigPath $ConfigPath } 'config already exists'
        foreach ($Mode in @('wrapper-failure', 'wrong-agent', 'wrong-url', 'bad-scope', 'oauth-failure')) {
            $env:HALOPSA_SETUP_TEST_MODE = $Mode
            Expect-Failure { & $Setup -TechnicianName "O'Neil" -OpCommand $Command -ConfigPath $ConfigPath -Force } 'HaloPSA setup failed'
            if ([IO.File]::ReadAllText($ConfigPath) -cne $Before) { throw 'Failed setup changed the existing config' }
        }
    }
    $env:HALOPSA_SETUP_TEST_MODE = ''
    $env:PATH = "$Scratch;$OriginalPath"
    & $Setup -TechnicianName "O'Neil" -ConfigPath $ConfigPath -Force | Out-Null
    Expect-Failure { & $Setup -TechnicianName "O'Neil" -OpCommand '.\op-itecs.cmd' -ConfigPath $ConfigPath -Force } 'absolute managed wrapper path'
    if ($global:HaloSetupTestOAuthCalls -lt 3) { throw 'Synthetic OAuth was not exercised' }
    Write-Output 'Windows setup passed: managed ps1/cmd wrappers, native Go MCP discovery with generated credential commands, PATH discovery, safe overwrite and fail-closed validation; no live requests.'
}
finally {
    $env:PATH = $OriginalPath
    $env:HALOPSA_SETUP_TEST_MODE = $OriginalMode
    # Scratch is an explicitly created, unique directory under the OS temp folder.
    if ([IO.Path]::GetFullPath($Scratch).StartsWith([IO.Path]::GetFullPath([IO.Path]::GetTempPath()), [StringComparison]::OrdinalIgnoreCase)) {
        Remove-Item -LiteralPath $Scratch -Recurse -Force
    }
}
