export type Tone = 'primary' | 'neutral' | 'danger'

export interface CourtAction {
  id: string
  label: string
  tone: Tone
  requiresNote?: boolean
}

export interface MissionSummary {
  missionId: string
  goal: string
  phase: string
  revision?: number
  iteration?: number
  updatedAt?: string
  active: boolean
  error?: string
}

export interface CourtStatus {
  mission_id?: string
  active_mission_id?: string | null
  phase: string
  revision?: number
  iteration?: number
  accepted_criteria?: string[]
  current?: Record<string, unknown> | null
  next: string
  integrity?: Record<string, unknown>
}

export interface Overview {
  product: string
  version: string
  project: string
  goal: string
  status: CourtStatus
  next: string
  actions: CourtAction[]
  editablePaths: string[]
  missions: MissionSummary[]
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
  overview: () => request<Overview>('/api/overview'),
  artifacts: (missionId?: string) =>
    request<Artifact[]>(`/api/artifacts${missionId ? `?missionId=${encodeURIComponent(missionId)}` : ''}`),
  artifact: (path: string) => request<{ path: string; content: string; size: number }>(`/api/artifact?path=${encodeURIComponent(path)}`),
  events: (missionId?: string) =>
    request<LedgerEvent[]>(`/api/events${missionId ? `?missionId=${encodeURIComponent(missionId)}` : ''}`),
  createMission: (goal: string) =>
    request<Record<string, unknown>>('/api/missions', {
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
