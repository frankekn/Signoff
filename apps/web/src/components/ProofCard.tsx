import type { ReactElement } from 'react'
import type { RunSummary, ProofSummary } from '../api'

type ProofCardProps = {
  readonly inspectedRun: RunSummary | null | undefined
  readonly proof: ProofSummary
}

function shortHash(hash: string | undefined): string {
  if (!hash) return '—'
  return hash.slice(0, 12)
}

function proofTone(status: string): string {
  const normalized = status.toLowerCase()
  if (normalized === 'pass' || normalized === 'present') return 'good'
  if (normalized === 'fail' || normalized === 'timeout' || normalized === 'error') return 'bad'
  return 'quiet'
}

function contractFinalLabel(proof: ProofSummary): string {
  if (proof.contract.final === true) return 'true'
  if (proof.contract.final === false) return 'false'
  return 'UNKNOWN'
}

export function ProofCard({ inspectedRun, proof }: ProofCardProps): ReactElement {
  return (
    <section className="proof-card">
      <div className="proof-head">
        <div>
          <span className="eyebrow">Readable proof</span>
          <h2>{inspectedRun && !inspectedRun.active ? `Inspecting ${inspectedRun.phase.replaceAll('_', ' ')} run` : 'Active run proof'}</h2>
        </div>
        <code>{proof.runId}</code>
      </div>
      <div className="proof-grid">
        <div className="proof-tile">
          <span>Evidence</span>
          <strong className={`proof-value--${proofTone(proof.evidence.status)}`}>{proof.evidence.status}</strong>
          <small>{proof.evidence.path ?? proof.evidence.detail ?? 'not yet produced'}</small>
          <code>{shortHash(proof.evidence.hash)}</code>
        </div>
        <div className="proof-tile">
          <span>Scope</span>
          <strong className={`proof-value--${proofTone(proof.scope.status)}`}>{proof.scope.status}</strong>
          <small>{typeof proof.scope.changed_lines === 'number' ? `${proof.scope.changed_lines} changed lines` : proof.scope.detail ?? 'not yet produced'}</small>
        </div>
        <div className="proof-tile">
          <span>Patch</span>
          <strong className={`proof-value--${proofTone(proof.patch.status)}`}>{proof.patch.status}</strong>
          <small>{proof.patch.path ?? proof.patch.detail ?? 'not yet produced'}</small>
          <code>{shortHash(proof.patch.hash)}</code>
        </div>
        <div className="proof-tile">
          <span>Review gate</span>
          <strong className={`proof-value--${proofTone(proof.reviewGate.decision)}`}>{proof.reviewGate.decision}</strong>
          <small>{proof.reviewGate.proofLevel ?? proof.reviewGate.detail ?? 'not yet produced'}</small>
          <code>{shortHash(proof.reviewGate.hash)}</code>
        </div>
        <div className="proof-tile">
          <span>Accepted criteria</span>
          <strong>{proof.acceptedCriteria.count}</strong>
          <small>{proof.acceptedCriteria.items.length > 0 ? proof.acceptedCriteria.items.join(', ') : 'none accepted yet'}</small>
        </div>
        <div className="proof-tile">
          <span className="proof-contract-label">contract.final</span>
          <strong>{contractFinalLabel(proof)}</strong>
          <small>{proof.finalReceipt.path ?? `Final receipt: ${proof.finalReceipt.status}`}</small>
          <span className="proof-hash-label">Final receipt SHA-256</span>
          <code className="proof-hash--full">{proof.finalReceipt.hash ?? '—'}</code>
        </div>
      </div>
      <div className="proof-commands">
        <span>Command results</span>
        {proof.commands.length > 0 ? (
          proof.commands.map((command) => (
            <code key={command.id}>
              {command.id}: {command.status} exit {command.exitCode ?? '—'} · {command.command.join(' ')}
            </code>
          ))
        ) : (
          <code>UNKNOWN: not yet produced</code>
        )}
      </div>
    </section>
  )
}
