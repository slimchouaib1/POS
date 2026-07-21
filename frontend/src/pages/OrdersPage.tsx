import { useEffect, useState } from 'react';
import api from '../api';
import type { Order } from '../types';
import { ClipboardList } from 'lucide-react';

const statusColors: Record<string, string> = {
  draft: 'badge-info', in_progress: 'badge-warning', served: 'badge-primary', paid: 'badge-success', cancelled: 'badge-danger',
};
const statusLabels: Record<string, string> = {
  draft: 'Brouillon', in_progress: 'En cours', served: 'Servie', paid: 'Payée', cancelled: 'Annulée',
};

export default function OrdersPage() {
  const [orders, setOrders] = useState<Order[]>([]);
  const [filterStatus, setFilterStatus] = useState('');

  useEffect(() => {
    const params = filterStatus ? `?status=${filterStatus}&limit=100` : '?limit=100';
    api.get(`/api/orders${params}`).then((r) => setOrders(r.data));
  }, [filterStatus]);

  return (
    <div className="animate-fadeIn">
      <div className="page-header">
        <h2><ClipboardList size={24} style={{ display: 'inline', marginRight: 8 }} />Commandes</h2>
        <p>{orders.length} commandes</p>
      </div>

      <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1rem', flexWrap: 'wrap' }}>
        {['', 'draft', 'in_progress', 'served', 'paid', 'cancelled'].map((s) => (
          <button key={s} className={`btn btn-sm ${filterStatus === s ? 'btn-primary' : 'btn-ghost'}`} onClick={() => setFilterStatus(s)}>
            {s ? statusLabels[s] : 'Toutes'}
          </button>
        ))}
      </div>

      <div className="card" style={{ padding: 0, overflow: 'auto' }}>
        <table className="data-table">
          <thead><tr><th>#</th><th>Table</th><th>Caissier</th><th>Articles</th><th>Total (DT)</th><th>Statut</th><th>Date</th></tr></thead>
          <tbody>
            {orders.map((o) => (
              <tr key={o.id}>
                <td style={{ fontWeight: 700 }}>#{o.id}</td>
                <td>{o.table_number ? `Table ${o.table_number}` : '—'}</td>
                <td>{o.cashier_name}</td>
                <td>{o.items.length}</td>
                <td style={{ fontWeight: 600, color: 'var(--accent)' }}>{o.total_amount.toFixed(2)}</td>
                <td><span className={`badge ${statusColors[o.status]}`}>{statusLabels[o.status]}</span></td>
                <td style={{ fontSize: '0.8125rem', color: 'var(--text-muted)' }}>{o.created_at ? new Date(o.created_at).toLocaleString('fr-FR') : ''}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
