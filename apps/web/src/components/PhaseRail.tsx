const phases = [
  ['DRAFT', 'Define'],
  ['COUNCIL', 'Challenge'],
  ['LOCKED', 'Lock'],
  ['IMPLEMENTING', 'Build'],
  ['VERIFIED', 'Verify'],
  ['REVIEWING', 'Review'],
  ['DONE', 'Sign off'],
] as const

const aliases: Record<string, string> = {
  SLICE_DRAFT: 'LOCKED',
  VERIFY_FAILED: 'IMPLEMENTING',
  REVIEWED: 'REVIEWING',
  COUNCIL_REVIEW: 'COUNCIL',
  STOPPED: 'DONE',
  BLOCKED: 'DONE',
  PIVOT: 'DONE',
}

export function PhaseRail({ phase }: { phase: string }) {
  const normalized = aliases[phase] ?? phase
  const activeIndex = Math.max(0, phases.findIndex(([id]) => id === normalized))
  return (
    <ol className="phase-rail" aria-label="Mission progress">
      {phases.map(([id, label], index) => (
        <li key={id} className={index < activeIndex ? 'complete' : index === activeIndex ? 'active' : ''}>
          <span className="phase-dot">{index < activeIndex ? '✓' : index + 1}</span>
          <span>{label}</span>
        </li>
      ))}
    </ol>
  )
}
