import { useEffect, useState } from 'react';
import api from '../api';
import { Activity } from 'lucide-react';

interface AuditLog {
  id: number;
  user_id: number | null;
  user_name: string;
  action: string;
  entity_type: string;
  entity_id: number | null;
  details: string;
  ip_address: string;
  created_at: string | null;
}

export default function AuditLogsPage() {
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get('/api/audit/logs?limit=100')
      .then((r) => setLogs(r.data))
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="animate-fadeIn">
      <div className="page-header">
        <h2><Activity size={24} style={{ display: 'inline', marginRight: 8 }} />Audit Logs</h2>
        <p>Most recent 100 sensitive system actions from the backend audit trail</p>
      </div>

      <div className="card" style={{ padding: 0, overflow: 'auto' }}>
        <table className="data-table">
          <thead>
            <tr>
              <th>Timestamp</th>
              <th>Actor</th>
              <th>Action</th>
              <th>Entity</th>
              <th>Details</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td colSpan={5} style={{ textAlign: 'center', padding: '2rem', color: 'var(--color-text-muted)' }}>
                  Loading audit logs...
                </td>
              </tr>
            ) : logs.length === 0 ? (
              <tr>
                <td colSpan={5} style={{ textAlign: 'center', padding: '2rem', color: 'var(--color-text-muted)' }}>
                  No audit logs found.
                </td>
              </tr>
            ) : logs.map((log) => (
              <tr key={log.id}>
                <td style={{ fontSize: '0.8125rem', color: 'var(--color-text-muted)' }}>
                  {log.created_at ? new Date(log.created_at).toLocaleString() : ''}
                </td>
                <td style={{ fontWeight: 600 }}>{log.user_name}</td>
                <td><span className="badge badge-info">{log.action}</span></td>
                <td>{log.entity_type} {log.entity_id ? `#${log.entity_id}` : ''}</td>
                <td style={{ fontSize: '0.8125rem', color: 'var(--color-text-secondary)', maxWidth: 420, whiteSpace: 'normal' }}>
                  {log.details}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
