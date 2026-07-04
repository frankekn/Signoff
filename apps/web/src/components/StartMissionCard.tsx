import type { ChangeEvent, FormEvent, ReactElement } from 'react'

type StartMissionCardProps = {
  readonly activeMissionId: string | undefined
  readonly goal: string
  readonly inspectingHistorical: boolean
  readonly pending: boolean
  readonly phase: string
  readonly onGoalChange: (goal: string) => void
  readonly onStartMission: () => void
}

export function StartMissionCard({ activeMissionId, goal, inspectingHistorical, pending, phase, onGoalChange, onStartMission }: StartMissionCardProps): ReactElement {
  const submitMission = (event: FormEvent<HTMLFormElement>): void => {
    event.preventDefault()
    if (goal.trim()) onStartMission()
  }

  const updateGoal = (event: ChangeEvent<HTMLTextAreaElement>): void => {
    onGoalChange(event.target.value)
  }

  return (
    <section className="start-card">
      <div>
        <span className="eyebrow">One sentence is enough</span>
        <h2>{phase === 'IDLE' ? 'What should the repository achieve?' : 'Start the next mission'}</h2>
        {inspectingHistorical && phase === 'DONE' && (
          <p className="active-scope-note">Active mission {activeMissionId ?? 'unknown'} is DONE. This control is active-scoped; the inspected mission remains read-only. Active receipt: FINAL_RECEIPT.json.</p>
        )}
        <p>Use observable language. Signoff stores this exact sentence and prevents later steps from quietly rewriting it.</p>
      </div>
      <form onSubmit={submitMission}>
        <textarea
          value={goal}
          onChange={updateGoal}
          placeholder="Example: Add Google sign-in without changing existing email login behavior."
          aria-label="Mission outcome"
        />
        <button className="button button--primary" type="submit" disabled={!goal.trim() || pending}>
          {pending ? 'Starting…' : 'Start mission'}
        </button>
      </form>
    </section>
  )
}
