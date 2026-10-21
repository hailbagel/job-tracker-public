# Kopieren 01A — `patrick.json` privat sichern (nach STOP in Schritt 01)

**Warum erscheint das?** Beim Ausführen von `docs/COPY_01_VSCODE_POWERSHELL_SYNC.md` auf dem **Betriebslaptop** meldet `git status` genau `?? patrick.json`; der sichere Synchronisationsbefehl bricht daher ab. Das ist beabsichtigt.

**WO EINFÜGEN?** VS Code → Ordner `job-tracker-public` geöffnet → **Terminal → PowerShell**. **NICHT** in Copilot-Chat, **NICHT** in Hostinger und **NICHT** in GitHub-Webeditor.

**WOFÜR?** Dieser einmalige lokale Reparaturschritt verschiebt die `patrick.json` aus dem öffentlichen Repo-Stamm in den laut `.gitignore` ausgeschlossenen Privatordner `configs/private_profiles/patrick.json`. Die Datei bleibt auf dem Laptop; **kein Inhalt wird angezeigt, gepusht, kopiert oder gelöscht**. Dieser Pfad ist außerdem die vom Projekt dokumentierte lokale Ablage für private Profilbelege.

## Kompletten PowerShell-Block kopieren und im VS-Code-Terminal ausführen

```powershell
$ErrorActionPreference = "Stop"

$repoRoots = @(git rev-parse --show-toplevel)
if ($LASTEXITCODE -ne 0 -or $repoRoots.Count -ne 1) { throw "STOP: VS Code Terminal muss im vorhandenen Git-Repo job-tracker-public stehen." }
$repoRoot = $repoRoots[0].Trim()
Set-Location -LiteralPath $repoRoot

$origin = (git remote get-url origin).Trim()
if ($LASTEXITCODE -ne 0 -or $origin -notmatch '(?i)github\.com[:/]hailbagel/job-tracker-public(\.git)?$') { throw "STOP: Falsches origin: $origin" }

$status = @(git status --porcelain=v1 --untracked-files=all)
if ($LASTEXITCODE -ne 0) { throw "STOP: git status fehlgeschlagen." }
if ($status.Count -ne 1 -or $status[0] -ne '?? patrick.json') {
    $status
    throw "STOP: Es muss EXAKT eine unversionierte Datei patrick.json geben. Andere Aenderungen zuerst separat pruefen."
}

$source = Join-Path $repoRoot "patrick.json"
$privateDir = Join-Path $repoRoot "configs/private_profiles"
$target = Join-Path $privateDir "patrick.json"
if (-not (Test-Path -LiteralPath $source -PathType Leaf)) { throw "STOP: patrick.json fehlt im Projektstamm." }
if (Test-Path -LiteralPath $target) { throw "STOP: Privates Ziel existiert bereits. Nichts ueberschreiben." }

git check-ignore -q -- configs/private_profiles/patrick.json
if ($LASTEXITCODE -ne 0) { throw "STOP: Der private Zielpfad ist NICHT in .gitignore geschuetzt." }

New-Item -ItemType Directory -Path $privateDir -Force | Out-Null
Move-Item -LiteralPath $source -Destination $target -ErrorAction Stop
if (-not (Test-Path -LiteralPath $target -PathType Leaf)) { throw "STOP: Ziel fehlt nach Move-Item." }
if (Test-Path -LiteralPath $source) { throw "STOP: Quellpfad existiert noch. Bitte manuell pruefen." }

$after = @(git status --porcelain=v1 --untracked-files=all)
if ($LASTEXITCODE -ne 0 -or $after.Count -ne 0) {
    $after
    throw "STOP: Git-Arbeitsverzeichnis ist noch nicht sauber."
}
Write-Output "=== PATRICK PRIVATE FILE PROTECTED; WORKTREE CLEAN ==="
Write-Output "Private Datei befindet sich jetzt unter configs/private_profiles/patrick.json (lokal, gitignored)."
Write-Output "NEXT: docs/COPY_01_VSCODE_POWERSHELL_SYNC.md im VS-Code PowerShell-Terminal ausfuehren."
```

### Sicherheitsregeln

- Vor Änderungen wird geprüft, ob **ausschließlich** `?? patrick.json` unversioniert ist. Bei *irgendeiner* anderen lokalen Änderung: **STOP**, nichts überschreiben.
- Verschieben nur, wenn `configs/private_profiles/patrick.json` noch **nicht** existiert.
- Der Zielpfad muss durch die Git-`.gitignore`-Regeln ausgeschlossen sein; andernfalls **STOP**.
- Kein `git add`, `git commit`, `git push`, `git clean`, `git reset` oder `git stash`.
- Wer die private Datei vorher unter `./patrick.json` referenziert hat, muss spätere lokale Profileinstellungen ggf. auf `configs/private_profiles/patrick.json` anpassen; **nicht** die Profilinhalte veröffentlichen.
- Der Code ändert **nichts auf Hostinger** und **keine GitHub-Dateien**.

### Erfolg

`=== PATRICK PRIVATE FILE PROTECTED; WORKTREE CLEAN ===`

**Danach in derselben VS-Code-PowerShell-Sitzung** den Synchronisationsblock aus [COPY_01_VSCODE_POWERSHELL_SYNC.md](COPY_01_VSCODE_POWERSHELL_SYNC.md) ausführen. Nach `WORK LAPTOP REPOSITORY READY` den Copilot-Block aus [COPY_02_COPILOT_INDUSTRIAL_AGENT.md](COPY_02_COPILOT_INDUSTRIAL_AGENT.md) in **VS Code → Copilot Agent → neuer Chat** einfügen.
