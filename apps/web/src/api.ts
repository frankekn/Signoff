export type Tone = 'primary' | 'neutral' | 'danger'

export interface CourtAction {
  id: string
  label: string
  tone: Tone
  requiresNote?: boolean
}

export interface RunSummary {
  runId: string
  goal: string
  phase: string
  revision?: number
  iteration?: number
  updatedAt?: string
  active: boolean
  error?: string
}

export interface CourtStatus {
  run_id?: string
  active_run_id?: string | null
  phase: string
  revision?: number
  iteration?: number
  accepted_criteria?: string[]
  current?: Record<string, unknown> | null
  next: string
  integrity?: Record<string, unknown>
}

export interface ProofCommand {
  id: string
  command: string[]
  status: string
  exitCode?: number | null
  acceptanceIds: string[]
}

export interface ProofStatus {
  status: string
  detail?: string
  hash?: string
  path?: string
  patchHash?: string
}

export interface ReviewGateProof extends ProofStatus {
  decision: string
  proofLevel?: string
}

export interface ProofSummary {
  runId: string
  phase: string
  iteration?: number | null
  commands: ProofCommand[]
  scope: ProofStatus & Record<string, unknown>
  evidence: ProofStatus
  patch: ProofStatus
  reviewGate: ReviewGateProof
  acceptedCriteria: {
    count: number
    items: string[]
  }
  contract: {
    final: boolean | null
  }
  finalReceipt: ProofStatus
}

export interface Overview {
  product: string
  version: string
  project: string
  goal: string
  status: CourtStatus
  next: string
  canStartRun: boolean
  blockedByIntegrity: boolean
  integrityStatus: string
  integrityMessage: string
  actions: CourtAction[]
  editablePaths: string[]
  runs: RunSummary[]
  proofSummary: ProofSummary | null
  inspectedRun: RunSummary | null
}

export interface Artifact {
  path: string
  name: string
  size: number
  editable: boolean
  kind: string
}

export interface LedgerEvent {
  seq: number
  time: string
  type: string
  payload: Record<string, unknown>
  hash: string
}

interface ApiEnvelope<T> {
  ok: boolean
  data: T
  error?: string
}

async function request<T>(url: string, init?: RequestInit): Promise<T> {
  const response = await fetch(url, {
    ...init,
    headers: {
      'Content-Type': 'application/json',
      ...(init?.headers ?? {}),
    },
  })
  const payload = (await response.json()) as ApiEnvelope<T>
  if (!response.ok || !payload.ok) {
    throw new Error(payload.error || `Request failed: ${response.status}`)
  }
  return payload.data
}

export const api = {
  overview: (inspectRunId?: string) =>
    request<Overview>(`/api/overview${inspectRunId ? `?inspectRunId=${encodeURIComponent(inspectRunId)}` : ''}`),
  artifacts: (runId?: string) =>
    request<Artifact[]>(`/api/artifacts${runId ? `?runId=${encodeURIComponent(runId)}` : ''}`),
  artifact: (path: string) => request<{ path: string; content: string; size: number }>(`/api/artifact?path=${encodeURIComponent(path)}`),
  events: (runId?: string) =>
    request<LedgerEvent[]>(`/api/events${runId ? `?runId=${encodeURIComponent(runId)}` : ''}`),
  createRun: (goal: string) =>
    request<Record<string, unknown>>('/api/runs', {
      method: 'POST',
      body: JSON.stringify({ goal }),
    }),
  action: (action: string, note = '') =>
    request<Record<string, unknown>>('/api/action', {
      method: 'POST',
      body: JSON.stringify({ action, note }),
    }),
  saveArtifact: (path: string, content: string) =>
    request<{ path: string; saved: boolean }>('/api/artifact', {
      method: 'PUT',
      body: JSON.stringify({ path, content }),
    }),
}
