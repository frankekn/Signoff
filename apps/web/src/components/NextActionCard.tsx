import type { ChangeEvent, FormEvent, ReactElement } from 'react'
import type { GripAction } from '../api'

type NextActionCardProps = {
  readonly actionPending: boolean
  readonly actions: readonly GripAction[]
  readonly agentInstruction: string
  readonly copied: boolean
  readonly next: string | undefined
  readonly note: string
  readonly noteAction: GripAction | null
  readonly noteError: string
  readonly onCancelNote: () => void
  readonly onCopyAgent: () => Promise<void>
  readonly onNoteChange: (value: string) => void
  readonly onRunAction: (action: GripAction) => void
  readonly onSubmitNote: () => void
}

export function NextActionCard({
  actionPending,
  actions,
  agentInstruction,
  copied,
  next,
  note,
  noteAction,
  noteError,
  onCancelNote,
  onCopyAgent,
  onNoteChange,
  onRunAction,
  onSubmitNote,
}: NextActionCardProps): ReactElement {
  const submitNote = (event: FormEvent<HTMLFormElement>): void => {
    event.preventDefault()
    onSubmitNote()
  }

  const updateNote = (event: ChangeEvent<HTMLTextAreaElement>): void => {
    onNoteChange(event.target.value)
  }

  return (
    <section className="next-card">
      <div className="next-copy">
        <span className="eyebrow">One legal next step</span>
        <h2>{next}</h2>
        <div className="agent-bridge">
          <code>{agentInstruction}</code>
          <button type="button" onClick={onCopyAgent}>
            {copied ? 'Copied' : 'Copy for agent'}
          </button>
        </div>
      </div>
      <div className="action-stack">
        {actions.map((action) => (
          <button type="button" key={action.id} className={`button button--${action.tone}`} disabled={actionPending} onClick={() => onRunAction(action)}>
            {action.label}
          </button>
        ))}
        {actions.length === 0 && <span className="terminal-note">No further action is legal in this run.</span>}
      </div>
      {noteAction && (
        <form className="note-panel" onSubmit={submitNote}>
          <div><span className="eyebrow">Required note</span><h3>{noteAction.label}</h3></div>
          <textarea
            value={note}
            onChange={updateNote}
            aria-label={`${noteAction.label} note`}
            placeholder={noteAction.id === 'finish_rework' ? 'Root cause for the next attempt.' : 'Evidence-based reason.'}
          />
          {noteError && <span className="note-error">{noteError}</span>}
          <div className="note-actions">
            <button type="button" className="button button--neutral" onClick={onCancelNote}>Cancel</button>
            <button type="submit" className={`button button--${noteAction.tone}`} disabled={actionPending}>{actionPending ? 'Submitting…' : 'Submit note'}</button>
          </div>
        </form>
      )}
    </section>
  )
}
