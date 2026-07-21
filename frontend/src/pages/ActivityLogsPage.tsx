import { useEffect, useState } from 'react';
import { Search, Download, Info } from 'lucide-react';
import CustomSelect from '../components/CustomSelect';
import api from '../api';

interface LogEntry {
  id: number;
  timestamp: string;
  user: string;
  userRole: string;
  action: string;
  module: string;
  target: string;
  severity: 'Normal' | 'Warning' | 'Critical';
  rawDetails: string;
}

export default function ActivityLogsPage() {
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [search, setSearch] = useState('');
  const [selectedLog, setSelectedLog] = useState<LogEntry | null>(null);

  useEffect(() => {
    api.get('/api/audit/logs?limit=100').then((r) => {
      if (r.data) {
        setLogs(r.data.map((l: any) => ({
          id: l.id,
          timestamp: l.created_at ? new Date(l.created_at).toLocaleString() : 'N/A',
          user: l.user_name || 'System',
          userRole: '', 
          action: l.action,
          module: l.entity_type,
          target: l.entity_id ? `#${l.entity_id}` : l.details?.slice(0, 30) || 'N/A',
          severity: (l.action.toLowerCase().includes('delete') || l.action.toLowerCase().includes('fail')) ? 'Critical' : 
                    (l.action.toLowerCase().includes('update') || l.action.toLowerCase().includes('adjust')) ? 'Warning' : 'Normal',
          rawDetails: l.details,
        })));
      }
    }).catch(console.error);
  }, []);

  const severityStyles: Record<string, { bg: string; color: string }> = {
    Normal: { bg: '#E8F5E9', color: '#28A745' },
    Warning: { bg: '#FFF8E1', color: '#F59E0B' },
    Critical: { bg: '#FFEBEE', color: '#DC3545' },
  };

  const filtered = logs.filter(l => {
    if (search && !l.user.toLowerCase().includes(search.toLowerCase()) &&
        !l.action.toLowerCase().includes(search.toLowerCase()) &&
        !l.target.toLowerCase().includes(search.toLowerCase())) return false;
    return true;
  });

  return (
    <div className="animate-fadeIn">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
        <div className="page-header" style={{ marginBottom: 0 }}>
          <h2>Activity Logs</h2>
          <p>Track all system actions and user activity</p>
        </div>
        <button className="btn btn-primary"><Download size={16} /> Export Logs</button>
      </div>

      {/* Filters */}
      <div className="card" style={{ marginBottom: '1.5rem', padding: '1rem 1.5rem' }}>
        <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
          <div style={{ position: 'relative', flex: 1 }}>
            <Search size={16} style={{ position: 'absolute', left: 12, top: 12, color: 'var(--color-text-muted)' }} />
            <input className="input" placeholder="Search by user, action, or target..." value={search} onChange={(e) => setSearch(e.target.value)} style={{ paddingLeft: '2.25rem' }} />
          </div>
          <CustomSelect options={[{ value: '', label: 'Last 7 Days' }]} value="" onChange={() => {}} style={{ width: 140 }} />
          <CustomSelect options={[{ value: '', label: 'All Users' }]} value="" onChange={() => {}} style={{ width: 140 }} />
          <CustomSelect options={[{ value: '', label: 'All Modules' }]} value="" onChange={() => {}} style={{ width: 140 }} />
          <CustomSelect options={[{ value: '', label: 'All Actions' }]} value="" onChange={() => {}} style={{ width: 140 }} />
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 350px', gap: '1.5rem' }}>
        {/* Logs Table */}
        <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
          <table className="data-table">
            <thead>
              <tr>
                <th>Timestamp</th>
                <th>User</th>
                <th>Action</th>
                <th>Module</th>
                <th>Target</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((l, i) => (
                <tr key={i} onClick={() => setSelectedLog(l)} style={{ cursor: 'pointer', background: selectedLog === l ? 'var(--color-bg-page)' : '' }}>
                  <td style={{ fontSize: '0.8125rem', color: 'var(--color-text-secondary)' }}>{l.timestamp}</td>
                  <td>
                    <div style={{ fontWeight: 600 }}>{l.user}</div>
                  </td>
                  <td style={{ fontWeight: 600 }}>{l.action}</td>
                  <td><span className="badge badge-info">{l.module}</span></td>
                  <td style={{ fontFamily: 'monospace', fontSize: '0.8125rem' }}>{l.target}</td>
                  <td>
                    <span style={{ display: 'inline-flex', alignItems: 'center', gap: '0.25rem', padding: '0.2rem 0.625rem', borderRadius: 9999, fontSize: '0.6875rem', fontWeight: 600, background: severityStyles[l.severity].bg, color: severityStyles[l.severity].color }}>
                      {l.severity}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          <div style={{ padding: '0.75rem 1.5rem', fontSize: '0.8125rem', color: 'var(--color-text-muted)', borderTop: '1px solid var(--color-border)', display: 'flex', justifyContent: 'space-between' }}>
            <span>Showing {filtered.length} logs</span>
            <div style={{ display: 'flex', gap: '0.375rem', alignItems: 'center' }}>
              <button className="btn btn-ghost btn-sm" disabled>Previous</button>
              <span style={{ width: 28, height: 28, borderRadius: '50%', background: 'var(--color-primary)', color: 'white', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '0.75rem', fontWeight: 700 }}>1</span>
              <button className="btn btn-ghost btn-sm">2</button>
              <button className="btn btn-ghost btn-sm">3</button>
              <button className="btn btn-ghost btn-sm">Next</button>
            </div>
          </div>
        </div>

        {/* Detail Panel */}
        <div className="card">
          {selectedLog ? (
            <div className="animate-slideIn">
              <h3 style={{ fontSize: '1rem', fontWeight: 700, marginBottom: '1rem' }}>Log Details</h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', fontSize: '0.875rem' }}>
                {Object.entries({
                  'ID': selectedLog.id,
                  'User': selectedLog.user,
                  'Action': selectedLog.action,
                  'Module': selectedLog.module,
                  'Target': selectedLog.target,
                  'Timestamp': selectedLog.timestamp,
                  'Severity': selectedLog.severity,
                  'Details': selectedLog.rawDetails,
                }).map(([key, value]) => (
                  <div key={key} style={{ display: 'flex', justifyContent: 'space-between', flexDirection: key === 'Details' ? 'column' : 'row', gap: key === 'Details' ? '0.25rem' : '1rem' }}>
                    <span style={{ color: 'var(--color-text-secondary)' }}>{key}</span>
                    <span style={{ fontWeight: 600, wordBreak: 'break-word' }}>{value}</span>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '3rem 1rem', color: 'var(--color-text-muted)' }}>
              <Info size={32} style={{ opacity: 0.3, marginBottom: '0.75rem' }} />
              <p style={{ fontWeight: 600 }}>No Activity Selected</p>
              <p style={{ fontSize: '0.8125rem' }}>Click on any activity log to view detailed information</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
