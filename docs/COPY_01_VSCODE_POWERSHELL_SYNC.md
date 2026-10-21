# Kopieren 01 — VS Code Terminal (PowerShell): sicher synchronisieren

**WO EINFÜGEN?** Auf dem **Betriebslaptop** in **VS Code → File / Datei → Open Folder / Ordner öffnen → `job-tracker-public`** und dann **Terminal → New Terminal → PowerShell**. **Nicht** in Copilot-Chat und **nicht** in Hostinger eingeben.

**WOFÜR?** Prüft das richtige GitHub-Repository, stoppt bei lokalen Änderungen und aktualisiert den lokalen `main` ausschließlich per Fast-Forward auf den aktuellen GitHub-Stand. **Kein Push, kein Löschen, kein Reset.**

Wenn das Projekt noch nicht auf dem Betriebslaptop vorhanden ist, zuerst in VS Code **Git: Clone** mit `https://github.com/hailbagel/job-tracker-public.git` ausführen und den geklonten Ordner öffnen.

## Kompletten PowerShell-Block kopieren und im VS-Code-Terminal einfügen

```powershell
$repoRoot = @(git rev-parse --show-toplevel)
if ($LASTEXITCODE -ne 0 -or $repoRoot.Count -ne 1) { throw "STOP: Kein Git-Repository in diesem VS-Code-Terminal. Zuerst job-tracker-public als Ordner öffnen." }
Set-Location $repoRoot[0]

$remoteResult = @(git remote get-url origin)
if ($LASTEXITCODE -ne 0 -or $remoteResult.Count -ne 1) { throw "STOP: Git-Remote origin fehlt." }
$remote = $remoteResult[0].Trim()
if ($remote -notmatch '(?i)github\.com[:/]hailbagel/job-tracker-public(\.git)?$') { throw "STOP: Falsches Git-Repository: $remote" }

$changes = @(git status --porcelain=v1 --untracked-files=all)
if ($LASTEXITCODE -ne 0) { throw "STOP: git status fehlgeschlagen." }
if ($changes.Count -gt 0) { $changes; throw "STOP: Lokale Änderungen/Dateien vorhanden. Nichts überschreiben; Ausgabe zur Prüfung schicken." }

git fetch origin main
if ($LASTEXITCODE -ne 0) { throw "STOP: git fetch fehlgeschlagen." }
git switch main
if ($LASTEXITCODE -ne 0) { throw "STOP: git switch main fehlgeschlagen." }
git pull --ff-only origin main
if ($LASTEXITCODE -ne 0) { throw "STOP: git pull (fast-forward only) fehlgeschlagen." }

$localSha = (git rev-parse HEAD).Trim()
$remoteSha = (git rev-parse refs/remotes/origin/main).Trim()
if ($localSha -ne $remoteSha) { throw "STOP: main weicht von origin/main ab." }

Write-Output "=== WORK LAPTOP REPOSITORY READY ==="
git status --short --branch
git log -1 --oneline
Write-Output "=== NEXT: docs/COPY_02_COPILOT_INDUSTRIAL_AGENT.md ==="
```

## Erfolgskriterium

Am Ende erscheint `=== WORK LAPTOP REPOSITORY READY ===`, gefolgt von `## main...origin/main` und dem neuesten Commit. Der jüngste Commit muss **nicht** derselbe wie auf einem älteren Screenshot sein: der Hostinger-Publisher kann weitere `data/`-Commits erzeugen.

**Bei `STOP` nicht weiterklicken, nichts stashen/resetten oder löschen.** Terminalausgabe zur Prüfung schicken.

**DANACH:** [COPY_02_COPILOT_INDUSTRIAL_AGENT.md](COPY_02_COPILOT_INDUSTRIAL_AGENT.md) öffnen. Dessen Text gehört in einen **neuen VS-Code-Copilot-Agent-Chat**.
