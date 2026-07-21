import { useEffect, useState } from 'react';
import api from '../api';
import { Activity } from 'lucide-react';

export default function AuditLogsPage() {
  const [logs, setLogs] = useState<any[]>([]);
  useEffect(() => { api.get('/api/audit/logs?limit=100').then((r) => setLogs(r.data)); }, []);

  return (
    <div className="animate-fadeIn">
      <div className="page-header">
        <h2><Activity size={24} style={{ display: 'inline', marginRight: 8 }} />Journal d'Audit</h2>
        <p>Traçabilité des actions utilisateurs</p>
      </div>
      <div className="card" style={{ padding: 0, overflow: 'auto' }}>
        <table className="data-table">
          <thead><tr><th>Date</th><th>Utilisateur</th><th>Action</th><th>Entité</th><th>Détails</th></tr></thead>
          <tbody>
            {logs.length === 0 ? (
              <tr><td colSpan={5} style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-muted)' }}>Aucun log d'audit</td></tr>
            ) : logs.map((l) => (
              <tr key={l.id}>
                <td style={{ fontSize: '0.8125rem', color: 'var(--text-muted)' }}>{l.created_at ? new Date(l.created_at).toLocaleString('fr-FR') : ''}</td>
                <td style={{ fontWeight: 600 }}>{l.user_name}</td>
                <td><span className="badge badge-info">{l.action}</span></td>
                <td>{l.entity_type} {l.entity_id ? `#${l.entity_id}` : ''}</td>
                <td style={{ fontSize: '0.8125rem', color: 'var(--text-secondary)', maxWidth: 300, overflow: 'hidden', textOverflow: 'ellipsis' }}>{l.details}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
