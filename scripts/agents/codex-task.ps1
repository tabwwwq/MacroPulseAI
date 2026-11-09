<#
.SYNOPSIS
  Delegate a scoped side task to OpenAI Codex via non-interactive `codex exec`.

.DESCRIPTION
  Wraps the brief with the repository's collaboration rules (AGENTS.md), runs Codex in the repo root
  with the chosen sandbox, and stores everything under .agents/codex-runs/<timestamp>-<name>.*:
    *.prompt.md  - the exact prompt sent
    *.log        - Codex stdout (progress)
    *.err.log    - Codex stderr
    *.result.md  - Codex's final message (its report)
  Exit code mirrors Codex's exit code.

.EXAMPLE
  ./scripts/agents/codex-task.ps1 -Name data-feasibility -PromptFile .agents/briefs/data-feasibility.md -Network

.EXAMPLE
  ./scripts/agents/codex-task.ps1 -Name api-review -Sandbox read-only -Prompt "Review apps/api for bugs; do not edit files."
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory)]
    [ValidatePattern('^[a-z0-9][a-z0-9-]{0,40}$')]
    [string]$Name,

    [string]$Prompt,

    [string]$PromptFile,

    [ValidateSet('read-only', 'workspace-write')]
    [string]$Sandbox = 'workspace-write',

    # Allow outbound network inside the workspace-write sandbox (needed for live API checks).
    [switch]$Network,

    [string]$Model,

    [ValidateSet('', 'low', 'medium', 'high', 'xhigh')]
    [string]$Effort = ''
)

$ErrorActionPreference = 'Stop'
$root = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path

if (-not $Prompt -and -not $PromptFile) { throw 'Provide -Prompt or -PromptFile.' }
if ($PromptFile) { $Prompt = Get-Content -Raw -Encoding utf8 (Resolve-Path $PromptFile) }

function Resolve-CodexExe {
    $bundled = Get-ChildItem "$env:LOCALAPPDATA\OpenAI\Codex\bin\*\codex.exe" -ErrorAction SilentlyContinue |
        Sort-Object LastWriteTime -Descending | Select-Object -First 1
    if ($bundled) { return $bundled.FullName }
    $onPath = Get-Command codex -ErrorAction SilentlyContinue
    if ($onPath) { return $onPath.Source }
    throw 'Codex CLI not found. Install the Codex desktop app or run: npm i -g @openai/codex'
}
$exe = Resolve-CodexExe

$runs = Join-Path $root '.agents\codex-runs'
New-Item -ItemType Directory -Force $runs | Out-Null
$base = Join-Path $runs ("{0}-{1}" -f (Get-Date -Format 'yyyyMMdd-HHmmss'), $Name)

$preamble = @"
You are Codex, a delegated side-task engineer on the MacroPulse AI repository.
Read AGENTS.md first and follow it; CLAUDE.md is the authoritative specification.
Stay strictly inside the scope of the task below and touch only the files it allows.
Do not commit, push, switch branches, or delete files you did not create.
Never fabricate data, API responses, metrics or test results; mark anything you could not verify.
End with the report format from AGENTS.md (summary, files changed, commands run -> result, unverified).

--- TASK: $Name ---
"@
$full = $preamble + "`n" + $Prompt
[System.IO.File]::WriteAllText("$base.prompt.md", $full, [System.Text.UTF8Encoding]::new($false))

function Quote([string]$s) { if ($s -match '[\s"]') { '"' + ($s -replace '"', '\"') + '"' } else { $s } }

$argv = @('exec', '--cd', (Quote $root), '--sandbox', $Sandbox, '--skip-git-repo-check',
    '--color', 'never', '--output-last-message', (Quote "$base.result.md"))
if ($Network) { $argv += @('-c', 'sandbox_workspace_write.network_access=true') }
if ($Model) { $argv += @('-m', (Quote $Model)) }
if ($Effort) { $argv += @('-c', "model_reasoning_effort=$Effort") }
$argv += '-'   # read the prompt from stdin

Write-Host "[codex-task] $Name -> $base.*  (sandbox=$Sandbox, network=$($Network.IsPresent))"
$proc = Start-Process -FilePath $exe -ArgumentList $argv -WorkingDirectory $root -NoNewWindow -Wait -PassThru `
    -RedirectStandardInput "$base.prompt.md" -RedirectStandardOutput "$base.log" -RedirectStandardError "$base.err.log"

$code = $proc.ExitCode
Write-Host "[codex-task] exit code $code"
if (Test-Path "$base.result.md") {
    Write-Host '----- Codex report -----'
    Get-Content -Raw -Encoding utf8 "$base.result.md"
} else {
    Write-Host '(no final message written; see .log / .err.log)'
    Get-Content -Tail 30 "$base.err.log" -ErrorAction SilentlyContinue
}
exit $code
