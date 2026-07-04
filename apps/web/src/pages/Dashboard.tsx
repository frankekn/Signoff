import { useCallback, useEffect, useMemo, useState, type ReactElement } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api, type GripAction } from '../api'
import { ArtifactPanel } from '../components/ArtifactPanel'
import { HeroPanel } from '../components/HeroPanel'
import { Mark } from '../components/Mark'
import { NextActionCard } from '../components/NextActionCard'
import { PhaseRail } from '../components/PhaseRail'
import { ProofCard } from '../components/ProofCard'
import { StartRunCard } from '../components/StartRunCard'
import { Timeline } from '../components/Timeline'

const phaseCopy: Record<string, { title: string; note: string }> = {
  IDLE: { title: 'Ready for a run', note: 'Describe the outcome. Signoff will preserve it as the immutable target.' },
  DRAFT: { title: 'Define what success means', note: 'Complete the charter and falsifiable acceptance criteria before implementation begins.' },
  PUSH: { title: 'Challenge the route', note: 'Independent agents answer the same claims and expose what would prove them wrong.' },
  LOCKED: { title: 'The goal is locked', note: 'Create one small implementation slice with explicit scope and executable checks.' },
  SLICE_DRAFT: { title: 'Bound the next change', note: 'Choose allowed paths, budgets, builder identity, and verification commands.' },
  IMPLEMENTING: { title: 'Build only the active slice', note: 'The contract is fixed. Scope and proof are measured from a sealed Git baseline.' },
  VERIFY_FAILED: { title: 'Evidence did not hold', note: 'Fix the failed check or scope breach. The acceptance target remains locked.' },
  VERIFIED: { title: 'Executable evidence passed', note: 'Now independent reviewers inspect the exact sealed patch and evidence.' },
  REVIEWING: { title: 'Independent review in progress', note: 'Each criterion must be PASS, FAIL, or UNKNOWN; unresolved doubt cannot be hidden.' },
  REVIEWED: { title: 'A decision is ready', note: 'Sign off only when the deterministic gate permits it, otherwise rework or accept the slice.' },
  PUSH_REVIEW: { title: 'Implementation is paused', note: 'Repeated failure or exhausted budget requires an explicit pivot or stop.' },
  DONE: { title: 'Signed off', note: 'The final patch is tied to a replayable receipt and the locked user outcome.' },
  STOPPED: { title: 'Stopped honestly', note: 'The loop ended without pretending the goal was achieved.' },
  BLOCKED: { title: 'Blocked', note: 'External evidence or capability is missing. Resolve it before continuing.' },
  PIVOT: { title: 'Pivot required', note: 'The previous route is archived. A revised contract must be explicit.' },
}

function containsFailure(value: unknown): boolean {
  if (!value || typeof value !== 'object') return false
  if ('status' in value && (value as { status?: unknown }).status === 'fail') return true
  return Object.values(value as Record<string, unknown>).some(containsFailure)
}

export function Dashboard(): ReactElement {
  const queryClient = useQueryClient()
  const [goal, setGoal] = useState('')
  const [tab, setTab] = useState<'artifacts' | 'timeline'>('artifacts')
  const [copied, setCopied] = useState(false)
  const [noteAction, setNoteAction] = useState<GripAction | null>(null)
  const [note, setNote] = useState('')
  const [noteError, setNoteError] = useState('')
  const [selectedRunId, setSelectedRunId] = useState<string | undefined>()
  const [artifactDirty, setArtifactDirty] = useState(false)
  const [runWarning, setRunWarning] = useState('')

  const overviewQuery = useQuery({
    queryKey: ['overview', selectedRunId],
    queryFn: () => api.overview(selectedRunId),
    refetchInterval: 2_000,
  })
  const overview = overviewQuery.data
  const phase = overview?.status.phase ?? 'IDLE'
  const canStartRun = overview?.canStartRun ?? false
  const actionCount = overview?.actions.length ?? 0
  const showNextCard = phase !== 'IDLE' && (!canStartRun || actionCount > 0)
  const copy = phaseCopy[phase] ?? { title: phase, note: overview?.next ?? '' }
  const runId = overview?.status.run_id
  const runIds = useMemo(() => overview?.runs.map((run) => run.runId) ?? [], [overview])

  useEffect(() => {
    if (!overview) return
    if (!selectedRunId || !runIds.includes(selectedRunId)) {
      setSelectedRunId(runId)
    }
  }, [runId, runIds, overview, selectedRunId])

  const createMutation = useMutation({
    mutationFn: () => api.createRun(goal),
    onSuccess: async () => {
      setGoal('')
      setSelectedRunId(undefined)
      await queryClient.invalidateQueries()
    },
  })

  const actionMutation = useMutation({
    mutationFn: ({ action, note }: { action: string; note: string }) => api.action(action, note),
    onSuccess: async () => {
      setNoteAction(null)
      setNote('')
      setNoteError('')
      await queryClient.invalidateQueries()
    },
  })

  const runAction = (action: GripAction): void => {
    if (action.requiresNote) {
      setNoteAction(action)
      setNote('')
      setNoteError('')
      return
    }
    actionMutation.mutate({ action: action.id, note: '' })
  }

  const submitNoteAction = (): void => {
    if (!noteAction) return
    const trimmed = note.trim()
    if (!trimmed) {
      setNoteError('A note is required for this action.')
      return
    }
    actionMutation.mutate({ action: noteAction.id, note: trimmed })
  }

  const updateNote = (value: string): void => {
    setNote(value)
    if (noteError) setNoteError('')
  }

  const copyAgentInstruction = async (): Promise<void> => {
    await navigator.clipboard.writeText(agentInstruction)
    setCopied(true)
    window.setTimeout(() => setCopied(false), 1_500)
  }

  const updateArtifactDirty = useCallback((dirty: boolean): void => {
    setArtifactDirty(dirty)
    if (!dirty) setRunWarning('')
  }, [])

  const selectRun = (nextRunId: string): void => {
    if (artifactDirty && nextRunId !== selectedRunId) {
      setRunWarning('Save or discard the current draft before switching runs.')
      return
    }
    setRunWarning('')
    setSelectedRunId(nextRunId)
  }

  const selectTab = (nextTab: 'artifacts' | 'timeline'): void => {
    if (artifactDirty && nextTab !== tab) {
      setRunWarning('Save or discard the current draft before switching artifacts or runs.')
      return
    }
    setRunWarning('')
    setTab(nextTab)
  }

  const integrity = overview?.status.integrity
  const integrityGood = Boolean(integrity && !containsFailure(integrity))
  const accepted = overview?.status.accepted_criteria?.length ?? 0
  const proof = overview?.proofSummary
  const inspectedRun = overview?.inspectedRun

  const agentInstruction = useMemo(() => {
    if (!overview) return 'Read AGENTS.md. Wait for the live Signoff overview before editing.'
    const editablePaths = overview.editablePaths.length > 0
      ? overview.editablePaths.map((path) => `- ${path}`).join('\n')
      : '- None currently editable.'
    const actions = overview.actions.length > 0
      ? overview.actions.map((action) => `- ${action.label} (${action.id}${action.requiresNote ? ', note required' : ''})`).join('\n')
      : '- No UI action is currently legal.'
    return `Read AGENTS.md.
Run id: ${overview.status.run_id ?? 'none'}
Phase: ${overview.status.phase}
Live next action: ${overview.next}
Editable paths:
${editablePaths}
Action limits:
${actions}
Do not edit locked or generated artifacts. Do not edit receipts or files outside editable paths.`
  }, [overview])

  return (
    <div className="app-shell">
      <header className="topbar">
        <Mark />
        <div className="topbar-right">
          <span className="project-path" title={overview?.project}>{overview?.project ?? 'Connecting…'}</span>
          <span className={overviewQuery.isError ? 'connection connection--bad' : 'connection'}>
            <i /> {overviewQuery.isError ? 'Offline' : 'Local'}
          </span>
        </div>
      </header>

      <main>
        <HeroPanel
          accepted={accepted}
          current={overview?.status.current}
          goal={overview?.goal}
          integrityGood={integrityGood}
          integrityPresent={Boolean(integrity)}
          note={copy.note}
          phase={phase}
          revision={overview?.status.revision}
          title={copy.title}
        />

        <PhaseRail phase={phase} />

        {proof && <ProofCard inspectedRun={inspectedRun} proof={proof} />}

        {canStartRun && (
          <StartRunCard
            activeRunId={runId}
            goal={goal}
            inspectingHistorical={Boolean(inspectedRun && !inspectedRun.active)}
            pending={createMutation.isPending}
            phase={phase}
            onGoalChange={setGoal}
            onStartRun={() => createMutation.mutate()}
          />
        )}

        {showNextCard && (
          <NextActionCard
            actionPending={actionMutation.isPending}
            actions={overview?.actions ?? []}
            agentInstruction={agentInstruction}
            copied={copied}
            next={overview?.next}
            note={note}
            noteAction={noteAction}
            noteError={noteError}
            onCancelNote={() => setNoteAction(null)}
            onCopyAgent={copyAgentInstruction}
            onNoteChange={updateNote}
            onRunAction={runAction}
            onSubmitNote={submitNoteAction}
          />
        )}

        {(overviewQuery.error || createMutation.error || actionMutation.error) && (
          <div className="global-error">
            {(overviewQuery.error ?? createMutation.error ?? actionMutation.error)?.message}
          </div>
        )}

        <section className="workspace-card">
          <div className="workspace-head">
            <div>
              <span className="eyebrow">Observable by default</span>
              <h2>Run record</h2>
            </div>
            <div className="workspace-controls">
              {overview && overview.runs.length > 1 && (
                <div className="run-selector" aria-label="Run history">
                  {overview.runs.map((run) => (
                    <button
                      type="button"
                      key={run.runId}
                      className={run.runId === selectedRunId ? 'active' : ''}
                      onClick={() => selectRun(run.runId)}
                    >
                      <span>{run.active ? 'Active' : run.phase.replaceAll('_', ' ')}</span>
                      <strong>{run.runId.replace(/^run-\d{8}-\d{6}-/, '')}</strong>
                    </button>
                  ))}
                </div>
              )}
              <div className="segmented">
                <button type="button" className={tab === 'artifacts' ? 'active' : ''} onClick={() => selectTab('artifacts')}>Artifacts</button>
                <button type="button" className={tab === 'timeline' ? 'active' : ''} onClick={() => selectTab('timeline')}>Timeline</button>
              </div>
            </div>
          </div>
          {runWarning && <div className="dirty-warning dirty-warning--workspace">{runWarning}</div>}
          {tab === 'artifacts' ? <ArtifactPanel runId={selectedRunId} onDirtyChange={updateArtifactDirty} /> : <Timeline runId={selectedRunId} />}
        </section>
      </main>

      <footer>
        <span>Signoff {overview?.version ?? ''}</span>
        <span>Local-first · No hosted account · Receipts stay in your repository</span>
      </footer>
    </div>
  )
}
