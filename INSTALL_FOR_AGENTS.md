# Install Traction from a coding agent

Use this procedure when the user gives you the Traction repository URL and an outcome.

## Preconditions

- Work inside the user's target Git repository.
- Preserve all unrelated work and the current Git index.
- Require Git and Python 3.10+.
- Do not require Node.js, Docker, a hosted account, or a global install.

## Install

```sh
SOURCE_DIR="$(mktemp -d)"
git clone --depth 1 <TRACTION_REPOSITORY_URL> "$SOURCE_DIR/traction"
"$SOURCE_DIR/traction/install.sh" "$PWD"
./traction doctor
```

Windows PowerShell:

```powershell
$SourceDir = Join-Path $env:TEMP "traction"
git clone --depth 1 <TRACTION_REPOSITORY_URL> $SourceDir
& "$SourceDir\install.ps1" (Get-Location).Path
.\traction.ps1 doctor
```

Installation is repository-local and idempotent. It writes:

```text
traction / traction.cmd / traction.ps1
.traction/runtime/traction/
.agents/skills/{traction,loop}/
.claude/skills/{traction,loop}/
.gemini/skills/{traction,loop}/
managed Traction blocks in AGENTS.md, CLAUDE.md, and GEMINI.md
```

## Start the exact user outcome

Do not paraphrase the user's sentence:

```sh
./traction start "<EXACT USER OUTCOME>"
./traction status
./traction next
```

Read `.agents/skills/traction/SKILL.md`, then perform only the legal next action returned by `./traction next` until the runtime emits `DONE`, `STOPPED`, `PIVOT`, or `BLOCKED`.

Never bypass a failed gate, invent reviewer identities, edit locked artifacts, or describe a test as passed unless `./traction verify` executed it. The UI is optional for the agent; the user can observe the same run with `./traction ui`.
