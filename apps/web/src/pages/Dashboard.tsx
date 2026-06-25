import { useMemo, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api, type CourtAction } from '../api'
import { ArtifactPanel } from '../components/ArtifactPanel'
import { Mark } from '../components/Mark'
import { PhaseRail } from '../components/PhaseRail'
import { Timeline } from '../components/Timeline'

const phaseCopy: Record<string, { title: string; note: string }> = {
  IDLE: { title: 'Ready for a mission', note: 'Describe the outcome. Signoff will preserve it as the immutable target.' },
  DRAFT: { title: 'Define what success means', note: 'Complete the charter and falsifiable acceptance criteria before implementation begins.' },
  COUNCIL: { title: 'Challenge the route', note: 'Independent agents answer the same claims and expose what would prove them wrong.' },
  LOCKED: { title: 'The goal is locked', note: 'Create one small implementation slice with explicit scope and executable checks.' },
  SLICE_DRAFT: { title: 'Bound the next change', note: 'Choose allowed paths, budgets, builder identity, and verification commands.' },
  IMPLEMENTING: { title: 'Build only the active slice', note: 'The contract is fixed. Scope and proof are measured from a sealed Git baseline.' },
  VERIFY_FAILED: { title: 'Evidence did not hold', note: 'Fix the failed check or scope breach. The acceptance target remains locked.' },
  VERIFIED: { title: 'Executable evidence passed', note: 'Now independent reviewers inspect the exact sealed patch and evidence.' },
  REVIEWING: { title: 'Independent review in progress', note: 'Each criterion must be PASS, FAIL, or UNKNOWN; unresolved doubt cannot be hidden.' },
  REVIEWED: { title: 'A decision is ready', note: 'Sign off only when the deterministic gate permits it, otherwise rework or accept the slice.' },
  COUNCIL_REVIEW: { title: 'Implementation is paused', note: 'Repeated failure or exhausted budget requires an explicit pivot or stop.' },
  DONE: { title: 'Signed off', note: 'The final patch is tied to a replayable receipt and the locked user outcome.' },
  STOPPED: { title: 'Stopped honestly', note: 'The loop ended without pretending the goal was achieved.' },
  BLOCKED: { title: 'Blocked', note: 'External evidence or capability is missing. Resolve it before continuing.' },
  PIVOT: { title: 'Pivot required', note: 'The previous route is archived. A revised contract must be explicit.' },
}

function statusTone(phase: string) {
  if (phase === 'DONE') return 'good'
  if (['STOPPED', 'BLOCKED', 'VERIFY_FAILED'].includes(phase)) return 'bad'
  if (phase === 'IDLE') return 'quiet'
  return 'live'
}

function containsFailure(value: unknown): boolean {
  if (!value || typeof value !== 'object') return false
  if ('status' in value && (value as { status?: unknown }).status === 'fail') return true
  return Object.values(value as Record<string, unknown>).some(containsFailure)
}

function currentIteration(current: Record<string, unknown> | null | undefined) {
  const value = current?.iteration
  return typeof value === 'number' ? value : '—'
}

export function Dashboard() {
  const queryClient = useQueryClient()
  const [goal, setGoal] = useState('')
  const [tab, setTab] = useState<'artifacts' | 'timeline'>('artifacts')
  const [copied, setCopied] = useState(false)

  const overviewQuery = useQuery({
    queryKey: ['overview'],
    queryFn: api.overview,
    refetchInterval: 2_000,
  })
  const overview = overviewQuery.data
  const phase = overview?.status.phase ?? 'IDLE'
  const copy = phaseCopy[phase] ?? { title: phase, note: overview?.next ?? '' }
  const missionId = overview?.status.mission_id

  const createMutation = useMutation({
    mutationFn: () => api.createMission(goal),
    onSuccess: async () => {
      setGoal('')
      await queryClient.invalidateQueries()
    },
  })

  const actionMutation = useMutation({
    mutationFn: ({ action, note }: { action: string; note: string }) => api.action(action, note),
    onSuccess: async () => {
      await queryClient.invalidateQueries()
    },
  })

  const runAction = (action: CourtAction) => {
    let note = ''
    if (action.requiresNote) {
      const answer = window.prompt(action.id === 'finish_rework' ? 'What root cause must the next attempt address?' : 'Record the evidence-based reason:')
      if (!answer) return
      note = answer
    }
    actionMutation.mutate({ action: action.id, note })
  }

  const integrity = overview?.status.integrity
  const integrityGood = Boolean(integrity && !containsFailure(integrity))
  const accepted = overview?.status.accepted_criteria?.length ?? 0

  const agentInstruction = useMemo(
    () => `Read AGENTS.md. Run ./signoff status and ./signoff next. Perform exactly the legal next action. Do not edit locked artifacts or generated receipts.`,
    [],
  )

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
        <section className="hero-panel">
          <div className="hero-copy">
            <div className={`phase-badge phase-badge--${statusTone(phase)}`}><span /> {phase.replaceAll('_', ' ')}</div>
            <h1>{copy.title}</h1>
            <p>{copy.note}</p>
            {overview?.goal && <blockquote>“{overview.goal}”</blockquote>}
          </div>
          <div className="hero-stats">
            <div><span>Revision</span><strong>{overview?.status.revision ?? '—'}</strong></div>
            <div><span>Iteration</span><strong>{currentIteration(overview?.status.current)}</strong></div>
            <div><span>Criteria earned</span><strong>{accepted}</strong></div>
            <div><span>Integrity</span><strong className={integrityGood ? 'ok-text' : 'bad-text'}>{integrity ? integrityGood ? 'PASS' : 'FAIL' : '—'}</strong></div>
          </div>
        </section>

        <PhaseRail phase={phase} />

        {phase === 'IDLE' ? (
          <section className="start-card">
            <div>
              <span className="eyebrow">One sentence is enough</span>
              <h2>What should the repository achieve?</h2>
              <p>Use observable language. Signoff stores this exact sentence and prevents later steps from quietly rewriting it.</p>
            </div>
            <form
              onSubmit={(event) => {
                event.preventDefault()
                if (goal.trim()) createMutation.mutate()
              }}
            >
              <textarea
                value={goal}
                onChange={(event) => setGoal(event.target.value)}
                placeholder="Example: Add Google sign-in without changing existing email login behavior."
                aria-label="Mission outcome"
              />
              <button className="button button--primary" type="submit" disabled={!goal.trim() || createMutation.isPending}>
                {createMutation.isPending ? 'Starting…' : 'Start mission'}
              </button>
            </form>
          </section>
        ) : (
          <section className="next-card">
            <div className="next-copy">
              <span className="eyebrow">One legal next step</span>
              <h2>{overview?.next}</h2>
              <div className="agent-bridge">
                <code>{agentInstruction}</code>
                <button
                  type="button"
                  onClick={async () => {
                    await navigator.clipboard.writeText(agentInstruction)
                    setCopied(true)
                    window.setTimeout(() => setCopied(false), 1_500)
                  }}
                >
                  {copied ? 'Copied' : 'Copy for agent'}
                </button>
              </div>
            </div>
            <div className="action-stack">
              {overview?.actions.map((action) => (
                <button
                  type="button"
                  key={action.id}
                  className={`button button--${action.tone}`}
                  disabled={actionMutation.isPending}
                  onClick={() => runAction(action)}
                >
                  {action.label}
                </button>
              ))}
              {overview?.actions.length === 0 && <span className="terminal-note">No further action is legal in this mission.</span>}
            </div>
          </section>
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
              <h2>Mission record</h2>
            </div>
            <div className="segmented">
              <button type="button" className={tab === 'artifacts' ? 'active' : ''} onClick={() => setTab('artifacts')}>Artifacts</button>
              <button type="button" className={tab === 'timeline' ? 'active' : ''} onClick={() => setTab('timeline')}>Timeline</button>
            </div>
          </div>
          {tab === 'artifacts' ? <ArtifactPanel missionId={missionId} /> : <Timeline missionId={missionId} />}
        </section>
      </main>

      <footer>
        <span>Signoff {overview?.version ?? ''}</span>
        <span>Local-first · No hosted account · Receipts stay in your repository</span>
      </footer>
    </div>
  )
}
