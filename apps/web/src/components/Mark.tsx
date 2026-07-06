export function Mark({ compact = false }: { compact?: boolean }) {
  return (
    <div className={compact ? 'mark mark--compact' : 'mark'} aria-label="Traction">
      <svg viewBox="0 0 48 48" role="img" aria-hidden="true">
        <path d="M9 11.5 24 5l15 6.5v10.2c0 10.1-6.2 17.7-15 21.3-8.8-3.6-15-11.2-15-21.3V11.5Z" />
        <path d="M15.5 24.5h17M18 19.5h12M19.5 29.5h9" />
      </svg>
      {!compact && (
        <div>
          <strong>Traction</strong>
          <span>Push, lock, build, pull, advance</span>
        </div>
      )}
    </div>
  )
}
