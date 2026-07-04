import { useQuery } from '@tanstack/react-query'
import { api } from '../api'

function label(type: string) {
  return type
    .split('.')
    .map((part) => part.replace(/_/g, ' '))
    .join(' · ')
}

export function Timeline({ runId }: { runId?: string }) {
  const query = useQuery({
    queryKey: ['events', runId],
    queryFn: () => api.events(runId),
    enabled: Boolean(runId),
    refetchInterval: 3_000,
  })

  if (!runId) return <div className="empty-state">Run activity will appear here.</div>
  if (query.isLoading) return <div className="empty-state">Loading history…</div>
  if (query.error) return <div className="inline-error">{query.error.message}</div>

  return (
    <ol className="timeline">
      {[...(query.data ?? [])].reverse().map((event) => (
        <li key={event.hash}>
          <span className="timeline-node" />
          <div>
            <strong>{label(event.type)}</strong>
            <time>{new Date(event.time).toLocaleString()}</time>
            <pre>{JSON.stringify(event.payload, null, 2)}</pre>
          </div>
        </li>
      ))}
    </ol>
  )
}
