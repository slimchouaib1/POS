import { useState, useEffect } from 'react';
import { Download, DollarSign } from 'lucide-react';
import api from '../api';

interface Transaction {
  id: string;
  date: string;
  table: string;
  server: string;
  payment: string;
  subtotal: number;
  discount: number;
  total: number;
  status: string;
}

export default function SalesReportsPage() {
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [revenueByDay, setRevenueByDay] = useState<{ day: string; value: number }[]>([]);
  const [grossSales, setGrossSales] = useState(0);

  useEffect(() => {
    // Fetch KPIs
    api.get('/api/reports/dashboard').then((r) => {
      if (r.data) {
        setGrossSales(r.data.total_revenue);
      }
    }).catch(console.error);

    // Fetch Daily Revenue
    api.get('/api/reports/sales?period=daily&days=7').then((r) => {
      if (r.data && r.data.data) {
        setRevenueByDay(r.data.data.map((d: any) => ({
          day: new Date(d.date).toLocaleDateString('en-US', { weekday: 'short' }),
          value: d.revenue
        })));
      }
    }).catch(console.error);

    // Fetch Transactions
    api.get('/api/orders?status=paid&limit=50').then((r) => {
      if (r.data) {
        setTransactions(r.data.map((o: any) => {
          const subtotal = o.items ? o.items.reduce((sum: number, i: any) => sum + i.subtotal, 0) : 0;
          return {
            id: `#ORD-${o.id}`,
            date: o.created_at ? new Date(o.created_at).toLocaleString() : '',
            table: o.table_number ? `Table ${o.table_number}` : 'Takeaway',
            server: o.cashier_name || 'System',
            payment: o.status === 'paid' ? 'Paid' : 'Pending',
            subtotal: subtotal,
            discount: o.discount_amount || 0,
            total: o.total_amount || 0,
            status: o.status === 'paid' ? 'Completed' : o.status
          };
        }));
      }
    }).catch(console.error);
  }, []);

  const maxRevDay = revenueByDay.length > 0 ? Math.max(...revenueByDay.map(d => d.value)) : 1;

  const kpis = [
    { label: 'Gross Sales', value: `${grossSales.toLocaleString()} DT`, icon: <DollarSign size={18} />, color: '#DC3545', bg: '#FFF5F5' },
  ];

  return (
    <div className="animate-fadeIn">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
        <h2 style={{ fontSize: '1.5rem', fontWeight: 700 }}>Sales Reports</h2>
        <div style={{ display: 'flex', gap: '0.5rem' }}>
          <button className="btn btn-primary btn-sm"><Download size={14} /> Export</button>
        </div>
      </div>

      {/* KPIs */}
      <div style={{ display: 'grid', gridTemplateColumns: 'minmax(220px, 320px)', gap: '1rem', marginBottom: '1.5rem' }}>
        {kpis.map((k, i) => (
          <div key={i} className="kpi-card">
            <div>
              <div className="kpi-label">{k.label}</div>
              <div className="kpi-value" style={{ fontSize: '1.5rem' }}>{k.value}</div>
            </div>
            <div className="kpi-icon" style={{ background: k.bg, color: k.color }}>{k.icon}</div>
          </div>
        ))}
      </div>

      {/* Revenue by Day chart */}
      <div className="card" style={{ marginBottom: '1.5rem' }}>
        <h3 style={{ fontSize: '1.125rem', fontWeight: 700, marginBottom: '1.25rem' }}>Revenue by Day</h3>
        <div style={{ display: 'flex', alignItems: 'flex-end', gap: '1rem', height: 200 }}>
          {revenueByDay.map((d, i) => (
            <div key={i} style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '0.5rem' }}>
              <div style={{
                width: '100%',
                height: `${(d.value / maxRevDay) * 180}px`,
                background: `linear-gradient(180deg, #DC3545 0%, ${d.value > maxRevDay * 0.8 ? '#28A745' : '#DC3545'} 100%)`,
                borderRadius: '6px 6px 0 0',
              }} />
              <span style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)' }}>{d.day}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Transactions Table */}
      <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
        <div style={{ padding: '1.25rem 1.5rem' }}>
          <h3 style={{ fontSize: '1.125rem', fontWeight: 700 }}>Detailed Transactions</h3>
        </div>
        <table className="data-table">
          <thead>
            <tr>
              <th>Order ID</th>
              <th>Date & Time</th>
              <th>Table / Type</th>
              <th>Server</th>
              <th>Payment</th>
              <th>Subtotal</th>
              <th>Discount</th>
              <th>Total</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {transactions.length > 0 ? transactions.map((t) => (
              <tr key={t.id}>
                <td style={{ color: 'var(--color-primary)', fontWeight: 600 }}>{t.id}</td>
                <td style={{ whiteSpace: 'pre-line', color: 'var(--color-text-secondary)', fontSize: '0.8125rem' }}>{t.date}</td>
                <td>{t.table}</td>
                <td>{t.server}</td>
                <td>{t.payment}</td>
                <td>{t.subtotal.toFixed(2)} DT</td>
                <td style={{ color: t.discount < 0 ? 'var(--color-success)' : '' }}>{t.discount !== 0 ? t.discount.toFixed(2) + ' DT' : '0.00 DT'}</td>
                <td style={{ fontWeight: 700, color: 'var(--color-primary)' }}>{t.total.toFixed(2)} DT</td>
                <td><span className="badge badge-success">{t.status}</span></td>
              </tr>
            )) : (
              <tr><td colSpan={9} style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-muted)' }}>No recent transactions</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
