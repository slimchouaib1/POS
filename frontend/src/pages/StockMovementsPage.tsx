import { useState, useEffect } from 'react';
import { Download } from 'lucide-react';
import CustomSelect from '../components/CustomSelect';
import api from '../api';

interface Movement {
  id: number;
  date: string;
  item: string;
  type: string;
  change: string;
  user: string;
  ref: string;
}

export default function StockMovementsPage() {
  const [movements, setMovements] = useState<Movement[]>([]);
  const [dateRange, setDateRange] = useState('');
  const [typeFilter, setTypeFilter] = useState('');

  useEffect(() => {
    api.get('/api/stock/ingredients/movements?limit=100').then((r) => {
      if (r.data) {
        setMovements(r.data.map((m: any) => {
          let type = 'Adjustment';
          if (m.reason.toLowerCase() === 'restock') type = 'Purchase';
          if (m.reason.toLowerCase() === 'sale') type = 'Sale';
          if (m.reason.toLowerCase() === 'waste') type = 'Waste';
          if (m.reason.toLowerCase() === 'refund') type = 'Refund';
          return {
            id: m.id,
            date: m.created_at ? new Date(m.created_at).toLocaleString() : '',
            item: m.ingredient_name,
            type,
            change: m.quantity_change > 0 ? `+${m.quantity_change}` : `${m.quantity_change}`,
            user: m.triggered_by_name || 'System',
            ref: m.details || m.reason
          };
        }));
      }
    }).catch(console.error);
  }, []);

  const filtered = movements.filter(m => {
    if (typeFilter && m.type !== typeFilter) return false;
    return true;
  });

  return (
    <div className="animate-fadeIn">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
        <div className="page-header" style={{ marginBottom: 0 }}>
          <h2>Stock Movement History</h2>
          <p>Track every stock transaction and audit trail</p>
        </div>
        <button className="btn btn-outline"><Download size={16} /> Export to CSV</button>
      </div>

      {/* Filters */}
      <div className="card" style={{ marginBottom: '1.5rem', padding: '1rem 1.5rem' }}>
        <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
          <div>
            <label style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--color-text-muted)', display: 'block', marginBottom: '0.25rem' }}>Date Range</label>
            <CustomSelect
              options={[
                { value: '', label: 'All Time' },
                { value: '7d', label: 'Last 7 Days' },
                { value: '30d', label: 'Last 30 Days' },
              ]}
              value={dateRange}
              onChange={setDateRange}
              style={{ width: 160 }}
            />
          </div>
          <div>
            <label style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--color-text-muted)', display: 'block', marginBottom: '0.25rem' }}>Movement Type</label>
            <CustomSelect
              options={[
                { value: '', label: 'All Types' },
                { value: 'Purchase', label: 'Purchase' },
                { value: 'Sale', label: 'Sale' },
                { value: 'Waste', label: 'Waste' },
              ]}
              value={typeFilter}
              onChange={setTypeFilter}
              style={{ width: 160 }}
            />
          </div>
          <div>
            <label style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--color-text-muted)', display: 'block', marginBottom: '0.25rem' }}>Product</label>
            <CustomSelect options={[{ value: '', label: 'All Products' }]} value="" onChange={() => {}} style={{ width: 160 }} />
          </div>
          <div>
            <label style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--color-text-muted)', display: 'block', marginBottom: '0.25rem' }}>Supplier</label>
            <CustomSelect options={[{ value: '', label: 'All Suppliers' }]} value="" onChange={() => {}} style={{ width: 160 }} />
          </div>
        </div>
      </div>

      {/* Table */}
      <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
        <table className="data-table">
          <thead>
            <tr>
              <th>Date & Time</th>
              <th>Item Name</th>
              <th>Movement Type</th>
              <th>Quantity Change</th>
              <th>Responsible User</th>
              <th>Reference</th>
            </tr>
          </thead>
          <tbody>
            {filtered.length > 0 ? filtered.map((m) => (
              <tr key={m.id}>
                <td style={{ color: 'var(--color-text-secondary)' }}>{m.date}</td>
                <td style={{ fontWeight: 600 }}>{m.item}</td>
                <td>
                  <span className={`badge ${m.type === 'Purchase' || m.type === 'Refund' ? 'badge-success' : m.type === 'Sale' ? 'badge-info' : m.type === 'Waste' ? 'badge-danger' : 'badge-warning'}`}>
                    {m.type}
                  </span>
                </td>
                <td>
                  <span style={{ display: 'flex', alignItems: 'center', gap: '0.25rem', color: m.change.startsWith('+') ? 'var(--color-success)' : 'var(--color-danger)', fontWeight: 600 }}>
                    {m.change}
                  </span>
                </td>
                <td>{m.user}</td>
                <td style={{ fontFamily: 'monospace', fontSize: '0.8125rem' }}>{m.ref}</td>
              </tr>
            )) : (
              <tr><td colSpan={6} style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-muted)' }}>No stock movements found</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
