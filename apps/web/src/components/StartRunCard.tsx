import type { ChangeEvent, FormEvent, ReactElement } from 'react'

type StartRunCardProps = {
  readonly activeRunId: string | undefined
  readonly goal: string
  readonly inspectingHistorical: boolean
  readonly pending: boolean
  readonly phase: string
  readonly onGoalChange: (goal: string) => void
  readonly onStartRun: () => void
}

export function StartRunCard({ activeRunId, goal, inspectingHistorical, pending, phase, onGoalChange, onStartRun }: StartRunCardProps): ReactElement {
  const submitRun = (event: FormEvent<HTMLFormElement>): void => {
    event.preventDefault()
    if (goal.trim()) onStartRun()
  }

  const updateGoal = (event: ChangeEvent<HTMLTextAreaElement>): void => {
    onGoalChange(event.target.value)
  }

  return (
    <section className="start-card">
      <div>
        <span className="eyebrow">One sentence is enough</span>
        <h2>{phase === 'IDLE' ? 'What should the repository achieve?' : 'Start the next run'}</h2>
        {inspectingHistorical && phase === 'DONE' && (
          <p className="active-scope-note">Active run {activeRunId ?? 'unknown'} is DONE. This control is active-scoped; the inspected run remains read-only. Active receipt: FINAL_RECEIPT.json.</p>
        )}
        <p>Use observable language. Traction stores this exact sentence and prevents later steps from quietly rewriting it.</p>
      </div>
      <form onSubmit={submitRun}>
        <textarea
          value={goal}
          onChange={updateGoal}
          placeholder="Example: Add Google sign-in without changing existing email login behavior."
          aria-label="Run outcome"
        />
        <button className="button button--primary" type="submit" disabled={!goal.trim() || pending}>
          {pending ? 'Starting…' : 'Start run'}
        </button>
      </form>
    </section>
  )
}
