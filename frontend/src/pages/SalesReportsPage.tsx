import { useState, useEffect } from 'react';
import { Download, DollarSign, ArrowUp, ArrowDown } from 'lucide-react';
import CustomSelect from '../components/CustomSelect';
import api from '../api';

interface Transaction {
  id: string;
  date: string;
  table: string;
  server: string;
  payment: string;
  subtotal: number;
  tax: number;
  discount: number;
  total: number;
  status: string;
}

export default function SalesReportsPage() {
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [revenueByDay, setRevenueByDay] = useState<{ day: string; value: number }[]>([]);
  const [kpisData, setKpisData] = useState({ gross: 0, net: 0, tax: 0 });

  useEffect(() => {
    // Fetch KPIs
    api.get('/api/reports/dashboard').then((r) => {
      if (r.data) {
        setKpisData({
          gross: r.data.total_revenue,
          net: r.data.total_revenue * 0.81, // approximate net for demo
          tax: r.data.total_revenue * 0.19, // approximate tax for demo
        });
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
            tax: subtotal * 0.1,
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
    { label: 'Gross Sales', value: `${kpisData.gross.toLocaleString()} DT`, change: '', up: true, icon: <DollarSign size={18} />, color: '#DC3545', bg: '#FFF5F5' },
    { label: 'Net Sales', value: `${kpisData.net.toLocaleString()} DT`, change: '', up: true, icon: <DollarSign size={18} />, color: '#28A745', bg: '#E8F5E9' },
    { label: 'Taxes', value: `${kpisData.tax.toLocaleString()} DT`, change: '', up: true, icon: <DollarSign size={18} />, color: '#DC3545', bg: '#FFEBEE' },
  ];

  return (
    <div className="animate-fadeIn">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
        <h2 style={{ fontSize: '1.5rem', fontWeight: 700 }}>Sales Reports</h2>
        <div style={{ display: 'flex', gap: '0.5rem' }}>
          <button className="btn btn-outline btn-sm">Last 30 Days</button>
          <CustomSelect options={[{ value: '', label: 'All Payment Methods' }]} value="" onChange={() => {}} style={{ width: 160 }} />
          <CustomSelect options={[{ value: '', label: 'All Order Types' }]} value="" onChange={() => {}} style={{ width: 140 }} />
          <CustomSelect options={[{ value: '', label: 'All Servers' }]} value="" onChange={() => {}} style={{ width: 130 }} />
          <button className="btn btn-primary btn-sm"><Download size={14} /> Export</button>
        </div>
      </div>

      {/* KPIs */}
      <div className="grid-5" style={{ marginBottom: '1.5rem' }}>
        {kpis.map((k, i) => (
          <div key={i} className="kpi-card">
            <div>
              <div className="kpi-label">{k.label}</div>
              <div className="kpi-value" style={{ fontSize: '1.5rem' }}>{k.value}</div>
              {k.change && (
                <div className={`kpi-change ${k.up ? 'up' : 'down'}`}>
                  {k.up ? <ArrowUp size={12} /> : <ArrowDown size={12} />}
                  {k.change} vs last period
                </div>
              )}
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
              <th>Tax</th>
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
                <td>{t.tax.toFixed(2)} DT</td>
                <td style={{ color: t.discount < 0 ? 'var(--color-success)' : '' }}>{t.discount !== 0 ? t.discount.toFixed(2) + ' DT' : '0.00 DT'}</td>
                <td style={{ fontWeight: 700, color: 'var(--color-primary)' }}>{t.total.toFixed(2)} DT</td>
                <td><span className="badge badge-success">{t.status}</span></td>
              </tr>
            )) : (
              <tr><td colSpan={10} style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-muted)' }}>No recent transactions</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
