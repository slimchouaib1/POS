import { Settings } from 'lucide-react';

export default function SettingsPage() {
  return (
    <div className="animate-fadeIn">
      <div className="page-header">
        <h2><Settings size={24} style={{ display: 'inline', marginRight: 8 }} />Settings</h2>
        <p>Smart POS System Configuration</p>
      </div>
      <div className="grid-2">
        <div className="card">
          <h3 style={{ fontSize: '1rem', fontWeight: 600, marginBottom: '1rem' }}>System Information</h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', fontSize: '0.875rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}><span style={{ color: 'var(--text-secondary)' }}>Application</span><span style={{ fontWeight: 600 }}>POS Intelligent Timsoft</span></div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}><span style={{ color: 'var(--text-secondary)' }}>Version</span><span style={{ fontWeight: 600 }}>1.0.0</span></div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}><span style={{ color: 'var(--text-secondary)' }}>Backend</span><span style={{ fontWeight: 600 }}>FastAPI + Python</span></div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}><span style={{ color: 'var(--text-secondary)' }}>Frontend</span><span style={{ fontWeight: 600 }}>React + TypeScript</span></div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}><span style={{ color: 'var(--text-secondary)' }}>Database</span><span style={{ fontWeight: 600 }}>SQLite</span></div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}><span style={{ color: 'var(--text-secondary)' }}>Auth</span><span style={{ fontWeight: 600 }}>JWT + RBAC</span></div>
          </div>
        </div>
        <div className="card">
          <h3 style={{ fontSize: '1rem', fontWeight: 600, marginBottom: '1rem' }}>AI Modules</h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', fontSize: '0.875rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}><span style={{ color: 'var(--text-secondary)' }}>Recommendations</span><span className="badge badge-success">FP-Growth</span></div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}><span style={{ color: 'var(--text-secondary)' }}>Forecasting</span><span className="badge badge-success">XGBoost</span></div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}><span style={{ color: 'var(--text-secondary)' }}>Anomaly Detection</span><span className="badge badge-success">Random Forest</span></div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}><span style={{ color: 'var(--text-secondary)' }}>Segmentation</span><span className="badge badge-success">RFM + KMeans</span></div>
          </div>
        </div>
      </div>
    </div>
  );
}
