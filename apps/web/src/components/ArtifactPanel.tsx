import { useEffect, useMemo, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api, type Artifact } from '../api'

function prettySize(bytes: number) {
  if (bytes < 1_024) return `${bytes} B`
  if (bytes < 1_048_576) return `${(bytes / 1_024).toFixed(1)} KB`
  return `${(bytes / 1_048_576).toFixed(1)} MB`
}

function priority(path: string) {
  if (path.endsWith('CHARTER.md')) return 0
  if (path.endsWith('SPEC.json')) return 1
  if (path.endsWith('COUNCIL.json')) return 2
  if (path.endsWith('CONTRACT.json')) return 3
  if (path.endsWith('EVIDENCE.json')) return 4
  if (path.endsWith('JUDGMENT.json')) return 5
  if (path.endsWith('FINAL_RECEIPT.json')) return 6
  return 20
}

export function ArtifactPanel({ missionId }: { missionId?: string }) {
  const queryClient = useQueryClient()
  const [selectedPath, setSelectedPath] = useState('')
  const [draft, setDraft] = useState('')
  const [dirty, setDirty] = useState(false)

  const artifactsQuery = useQuery({
    queryKey: ['artifacts', missionId],
    queryFn: () => api.artifacts(missionId),
    enabled: Boolean(missionId),
    refetchInterval: 3_000,
  })

  const artifacts = useMemo(
    () => [...(artifactsQuery.data ?? [])].sort((a, b) => priority(a.path) - priority(b.path) || a.path.localeCompare(b.path)),
    [artifactsQuery.data],
  )

  useEffect(() => {
    if (!selectedPath && artifacts.length > 0) {
      setSelectedPath(artifacts.find((item) => item.editable)?.path ?? artifacts[0].path)
    }
    if (selectedPath && !artifacts.some((item) => item.path === selectedPath)) {
      setSelectedPath(artifacts[0]?.path ?? '')
    }
  }, [artifacts, selectedPath])

  const artifactQuery = useQuery({
    queryKey: ['artifact', selectedPath],
    queryFn: () => api.artifact(selectedPath),
    enabled: Boolean(selectedPath),
  })

  useEffect(() => {
    if (artifactQuery.data && !dirty) setDraft(artifactQuery.data.content)
  }, [artifactQuery.data, dirty])

  useEffect(() => {
    setDirty(false)
  }, [selectedPath])

  const saveMutation = useMutation({
    mutationFn: () => api.saveArtifact(selectedPath, draft),
    onSuccess: async () => {
      setDirty(false)
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ['artifact', selectedPath] }),
        queryClient.invalidateQueries({ queryKey: ['artifacts'] }),
        queryClient.invalidateQueries({ queryKey: ['overview'] }),
      ])
    },
  })

  const selected: Artifact | undefined = artifacts.find((item) => item.path === selectedPath)

  if (!missionId) {
    return <div className="empty-state">Start a mission to see its contract, evidence, and receipts.</div>
  }

  return (
    <div className="artifact-layout">
      <aside className="artifact-list" aria-label="Mission artifacts">
        {artifacts.map((artifact) => (
          <button
            type="button"
            key={artifact.path}
            className={artifact.path === selectedPath ? 'artifact-row selected' : 'artifact-row'}
            onClick={() => setSelectedPath(artifact.path)}
          >
            <span>
              <strong>{artifact.name}</strong>
              <small>{artifact.path.replace(/^\.signoff\/missions\/[^/]+\//, '')}</small>
            </span>
            <span className={artifact.editable ? 'edit-pill' : 'read-pill'}>{artifact.editable ? 'Edit' : prettySize(artifact.size)}</span>
          </button>
        ))}
      </aside>
      <section className="editor-shell">
        <div className="editor-toolbar">
          <div>
            <strong>{selected?.name ?? 'Artifact'}</strong>
            <span>{selected?.editable ? 'Editable in this phase' : 'Sealed or generated'}</span>
          </div>
          {selected?.editable && (
            <button
              type="button"
              className="button button--small button--primary"
              disabled={!dirty || saveMutation.isPending}
              onClick={() => saveMutation.mutate()}
            >
              {saveMutation.isPending ? 'Saving…' : dirty ? 'Save changes' : 'Saved'}
            </button>
          )}
        </div>
        {artifactQuery.isLoading ? (
          <div className="editor-loading">Loading artifact…</div>
        ) : (
          <textarea
            spellCheck={false}
            value={draft}
            readOnly={!selected?.editable}
            onChange={(event) => {
              setDraft(event.target.value)
              setDirty(true)
            }}
            aria-label={selected?.name ?? 'Artifact content'}
          />
        )}
        {(artifactQuery.error || saveMutation.error) && (
          <div className="inline-error">{(artifactQuery.error ?? saveMutation.error)?.message}</div>
        )}
      </section>
    </div>
  )
}
