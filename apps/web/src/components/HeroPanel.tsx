import type { ReactElement } from 'react'

type HeroPanelProps = {
  readonly accepted: number
  readonly current: Record<string, unknown> | null | undefined
  readonly goal: string | undefined
  readonly integrityGood: boolean
  readonly integrityPresent: boolean
  readonly note: string
  readonly phase: string
  readonly revision: number | undefined
  readonly title: string
}

function statusTone(phase: string): string {
  if (phase === 'DONE') return 'good'
  if (['BLOCKED', 'VERIFY_FAILED'].includes(phase)) return 'bad'
  if (phase === 'PUSH_REVIEW') return 'paused'
  if (['STOPPED', 'PIVOT'].includes(phase)) return 'terminal'
  if (phase === 'IDLE') return 'quiet'
  return 'live'
}

function currentIteration(current: Record<string, unknown> | null | undefined): number | string {
  const value = current?.iteration
  return typeof value === 'number' ? value : '—'
}

function integrityLabel(integrityPresent: boolean, integrityGood: boolean): string {
  if (!integrityPresent) return '—'
  return integrityGood ? 'PASS' : 'FAIL'
}

export function HeroPanel({
  accepted,
  current,
  goal,
  integrityGood,
  integrityPresent,
  note,
  phase,
  revision,
  title,
}: HeroPanelProps): ReactElement {
  return (
    <section className="hero-panel">
      <div className="hero-copy">
        <div className={`phase-badge phase-badge--${statusTone(phase)}`}><span /> {phase.replaceAll('_', ' ')}</div>
        <h1>{title}</h1>
        <p>{note}</p>
        {goal && <blockquote>“{goal}”</blockquote>}
      </div>
      <div className="hero-stats">
        <div><span>Revision</span><strong>{revision ?? '—'}</strong></div>
        <div><span>Iteration</span><strong>{currentIteration(current)}</strong></div>
        <div><span>Criteria earned</span><strong>{accepted}</strong></div>
        <div><span>Integrity</span><strong className={integrityGood ? 'ok-text' : 'bad-text'}>{integrityLabel(integrityPresent, integrityGood)}</strong></div>
      </div>
    </section>
  )
}
