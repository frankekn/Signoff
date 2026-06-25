# Install Signoff from a coding agent

Use this procedure when the user gives you the Signoff repository URL and an outcome.

## Preconditions

- Work inside the user's target Git repository.
- Preserve all unrelated work and the current Git index.
- Require Git and Python 3.10+.
- Do not require Node.js, Docker, a hosted account, or a global install.

## Install

```sh
SOURCE_DIR="$(mktemp -d)"
git clone --depth 1 <SIGNOFF_REPOSITORY_URL> "$SOURCE_DIR/signoff"
"$SOURCE_DIR/signoff/install.sh" "$PWD"
./signoff doctor
```

Windows PowerShell:

```powershell
$SourceDir = Join-Path $env:TEMP "signoff"
git clone --depth 1 <SIGNOFF_REPOSITORY_URL> $SourceDir
& "$SourceDir\install.ps1" (Get-Location).Path
.\signoff.ps1 doctor
```

Installation is repository-local and idempotent. It writes:

```text
signoff / signoff.cmd / signoff.ps1
.signoff/runtime/signoff/
.agents/skills/{signoff,council,roast}/
.claude/skills/{signoff,council,roast}/
.gemini/skills/{signoff,council,roast}/
managed Signoff blocks in AGENTS.md, CLAUDE.md, and GEMINI.md
```

## Start the exact user outcome

Do not paraphrase the user's sentence:

```sh
./signoff start "<EXACT USER OUTCOME>"
./signoff status
./signoff next
```

Read `.agents/skills/signoff/SKILL.md`, then perform only the legal next action returned by `./signoff next` until the runtime emits `DONE`, `STOPPED`, `PIVOT`, or `BLOCKED`.

Never bypass a failed gate, invent reviewer identities, edit locked artifacts, or describe a test as passed unless `./signoff verify` executed it. The UI is optional for the agent; the user can observe the same mission with `./signoff ui`.
