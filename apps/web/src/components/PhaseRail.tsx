import type { ReactElement } from 'react'

type PhaseStep = {
  readonly id: string
  readonly label: string
}

type PhaseStatus = 'active' | 'failed' | 'paused' | 'terminal'

type PhasePresentation = {
  readonly activeIndex: number
  readonly status: PhaseStatus
  readonly steps: readonly PhaseStep[]
}

const stepIndex = {
  define: 0,
  push: 1,
  lock: 2,
  build: 3,
  verify: 4,
  review: 5,
  terminal: 6,
} as const

const phases: readonly PhaseStep[] = [
  { id: 'DRAFT', label: 'Define' },
  { id: 'PUSH', label: 'Push' },
  { id: 'LOCKED', label: 'Lock' },
  { id: 'IMPLEMENTING', label: 'Build' },
  { id: 'VERIFIED', label: 'Verify' },
  { id: 'REVIEWING', label: 'Pull' },
  { id: 'DONE', label: 'Sign off' },
] as const

function withStepLabel(index: number, label: string): readonly PhaseStep[] {
  return phases.map((step, currentIndex) => (currentIndex === index ? { ...step, label } : step))
}

const phasePresentation: Record<string, PhasePresentation> = {
  IDLE: { activeIndex: stepIndex.define, status: 'paused', steps: withStepLabel(stepIndex.define, 'Ready') },
  DRAFT: { activeIndex: stepIndex.define, status: 'active', steps: phases },
  PUSH: { activeIndex: stepIndex.push, status: 'active', steps: phases },
  LOCKED: { activeIndex: stepIndex.lock, status: 'active', steps: phases },
  SLICE_DRAFT: { activeIndex: stepIndex.lock, status: 'active', steps: withStepLabel(stepIndex.lock, 'Bound slice') },
  IMPLEMENTING: { activeIndex: stepIndex.build, status: 'active', steps: phases },
  VERIFY_FAILED: { activeIndex: stepIndex.verify, status: 'failed', steps: withStepLabel(stepIndex.verify, 'Failed evidence') },
  VERIFIED: { activeIndex: stepIndex.verify, status: 'active', steps: phases },
  REVIEWING: { activeIndex: stepIndex.review, status: 'active', steps: phases },
  REVIEWED: { activeIndex: stepIndex.terminal, status: 'paused', steps: withStepLabel(stepIndex.terminal, 'Decision pending') },
  PUSH_REVIEW: { activeIndex: stepIndex.review, status: 'paused', steps: withStepLabel(stepIndex.review, 'Paused review') },
  DONE: { activeIndex: stepIndex.terminal, status: 'active', steps: phases },
  STOPPED: { activeIndex: stepIndex.terminal, status: 'terminal', steps: withStepLabel(stepIndex.terminal, 'Stopped') },
  BLOCKED: { activeIndex: stepIndex.terminal, status: 'failed', steps: withStepLabel(stepIndex.terminal, 'Blocked') },
  PIVOT: { activeIndex: stepIndex.terminal, status: 'terminal', steps: withStepLabel(stepIndex.terminal, 'Pivot') },
}

export function PhaseRail({ phase }: { readonly phase: string }): ReactElement {
  const presentation = phasePresentation[phase] ?? { activeIndex: stepIndex.define, status: 'paused', steps: withStepLabel(stepIndex.define, phase) }
  return (
    <ol className="phase-rail" aria-label="Run progress">
      {presentation.steps.map((step, index) => (
        <li
          key={step.id}
          className={[
            index < presentation.activeIndex ? 'complete' : '',
            index === presentation.activeIndex ? `active active--${presentation.status}` : '',
          ].filter(Boolean).join(' ')}
        >
          <span className="phase-dot">{index < presentation.activeIndex ? '✓' : index + 1}</span>
          <span>{step.label}</span>
        </li>
      ))}
    </ol>
  )
}
