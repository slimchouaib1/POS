import { useEffect, useState } from 'react';
import api from '../api';
import {
  DollarSign, ShoppingCart, TrendingUp,
  Users, Lightbulb, ArrowUp, ArrowDown
} from 'lucide-react';

interface StatsData {
  total_revenue: number;
  total_orders: number;
  avg_basket: number;
  gross_profit: number;
  net_profit: number;
  customer_count: number;
  today_revenue: number;
  today_orders: number;
  active_orders: number;
  low_stock_count: number;
  top_products: { name: string; quantity: number; revenue: number }[];
  payment_methods: { method: string; count: number; total: number }[];
}

const mockStats: StatsData = {
  total_revenue: 0,
  total_orders: 0,
  avg_basket: 0,
  gross_profit: 0,
  net_profit: 0,
  customer_count: 0,
  today_revenue: 0,
  today_orders: 0,
  active_orders: 0,
  low_stock_count: 0,
  top_products: [],
  payment_methods: [],
};

export default function DashboardPage() {
  const [stats, setStats] = useState<StatsData>(mockStats);
  const [period, setPeriod] = useState('30d');

  useEffect(() => {
    api.get('/api/reports/dashboard').then((r) => {
      if (r.data) {
        setStats({
          ...mockStats,
          ...r.data,
        });
      }
    }).catch(console.error);
  }, []);

  const kpis = [
    { label: 'Total Revenue', value: `${stats.total_revenue.toLocaleString()} DT`, change: '+12.5%', up: true, icon: <DollarSign size={18} />, bg: '#FFF5F5', color: '#DC3545' },
    { label: 'Total Orders', value: stats.total_orders.toLocaleString(), change: '+8.3%', up: true, icon: <ShoppingCart size={18} />, bg: '#FFEBEE', color: '#DC3545' },
    { label: 'Average Order Value', value: `${stats.avg_basket.toFixed(2)} DT`, change: '+4.2%', up: true, icon: <TrendingUp size={18} />, bg: '#E8F5E9', color: '#28A745' },
    { label: 'Gross Profit', value: `${stats.gross_profit.toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 0 })} DT`, change: '+15.8%', up: true, icon: <DollarSign size={18} />, bg: '#FFF5F5', color: '#DC3545' },
    { label: 'Net Profit', value: `${stats.net_profit.toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 0 })} DT`, change: '-2.1%', up: false, icon: <DollarSign size={18} />, bg: '#FFF5F5', color: '#DC3545' },
    { label: 'Customer Count', value: stats.customer_count.toLocaleString(), change: '-9.7%', up: false, icon: <Users size={18} />, bg: '#FFEBEE', color: '#DC3545' },
  ];

  const revenueTrend = [11200, 13500, 10800, 12200, 15600, 14200, 11800, 13000, 17800, 19200, 18600, 15400, 17200, 21500];
  const peakHours = [
    { hour: '8AM', value: 1200 }, { hour: '9AM', value: 2300 }, { hour: '10AM', value: 1800 },
    { hour: '11AM', value: 2600 }, { hour: '12PM', value: 4500 }, { hour: '1PM', value: 4800 },
    { hour: '2PM', value: 3500 }, { hour: '3PM', value: 1500 }, { hour: '4PM', value: 2200 },
    { hour: '5PM', value: 2800 }, { hour: '6PM', value: 4200 }, { hour: '7PM', value: 4600 },
    { hour: '8PM', value: 4100 }, { hour: '9PM', value: 3200 },
  ];
  const maxPeak = Math.max(...peakHours.map(p => p.value));
  const maxRev = Math.max(...revenueTrend);

  const salesDist = stats.payment_methods.map((pm, i) => ({
    label: pm.method,
    pct: stats.total_revenue > 0 ? (pm.total / stats.total_revenue) * 100 : 0,
    color: ['#DC3545', '#F4845F', '#17A2B8', '#FFC107', '#6366F1'][i % 5],
  }));

  return (
    <div className="animate-fadeIn">
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
        <h2 style={{ fontSize: '1.5rem', fontWeight: 700 }}>Analytics Dashboard</h2>
        <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
          <button className={`btn btn-sm ${period === '30d' ? 'btn-outline' : 'btn-ghost'}`} onClick={() => setPeriod('30d')}>
            Last 30 Days
          </button>
          <button className="btn btn-ghost btn-sm">Compare Period</button>
          <button className="btn btn-ghost btn-sm">All Branches</button>
          <button className="btn btn-primary btn-sm"><ArrowDown size={14} /> Export</button>
        </div>
      </div>

      {/* KPI Grid */}
      <div className="grid-3" style={{ marginBottom: '1.5rem' }}>
        {kpis.map((k, i) => (
          <div key={i} className="kpi-card">
            <div>
              <div className="kpi-label">{k.label}</div>
              <div className="kpi-value">{k.value}</div>
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

      {/* AI Insight Banner */}
      <div className="ai-insight-banner" style={{ marginBottom: '1.5rem' }}>
        <Lightbulb size={22} />
        <div>
          <span className="ai-badge">AI INSIGHT</span>
          <p style={{ marginTop: '0.25rem' }}>
            Revenue increased 12.5% due to higher average order value during weekends.
            Peak performance detected on Saturday evenings (7-9 PM) with 23% above average sales.
          </p>
        </div>
      </div>

      {/* Revenue Trend */}
      <div className="card" style={{ marginBottom: '1.5rem' }}>
        <h3 style={{ fontSize: '1.125rem', fontWeight: 700, marginBottom: '1.25rem' }}>Revenue Trend</h3>
        <div style={{ height: 200, display: 'flex', alignItems: 'flex-end', gap: 2 }}>
          <div style={{ display: 'flex', flexDirection: 'column', justifyContent: 'space-between', height: '100%', fontSize: '0.6875rem', color: 'var(--color-text-muted)', paddingRight: '0.5rem', minWidth: 40 }}>
            <span>${Math.round(maxRev / 1000)}k</span>
            <span>${Math.round(maxRev / 2000)}k</span>
            <span>$0k</span>
          </div>
          <svg width="100%" height="200" viewBox="0 0 700 200" preserveAspectRatio="none">
            <polyline
              fill="none"
              stroke="#DC3545"
              strokeWidth="2.5"
              points={revenueTrend.map((v, i) => `${i * 700 / (revenueTrend.length - 1)},${200 - (v / maxRev) * 180}`).join(' ')}
            />
            {revenueTrend.map((v, i) => (
              <circle key={i} cx={i * 700 / (revenueTrend.length - 1)} cy={200 - (v / maxRev) * 180} r="4" fill="#DC3545" />
            ))}
          </svg>
        </div>
      </div>

      {/* Bottom Row: Sales Distribution + Top Products */}
      <div className="grid-2" style={{ marginBottom: '1.5rem' }}>
        {/* Payment Methods */}
        <div className="card">
          <h3 style={{ fontSize: '1.125rem', fontWeight: 700, marginBottom: '1.25rem' }}>Payment Methods</h3>
          <div style={{ display: 'flex', justifyContent: 'center', marginBottom: '1rem' }}>
            <svg width="200" height="200" viewBox="0 0 200 200">
              {(() => {
                let cum = 0;
                return salesDist.map((s, i) => {
                  const startAngle = cum * 3.6 * Math.PI / 180;
                  cum += s.pct;
                  const endAngle = cum * 3.6 * Math.PI / 180;
                  const largeArc = s.pct > 50 ? 1 : 0;
                  const x1 = 100 + 70 * Math.cos(startAngle - Math.PI / 2);
                  const y1 = 100 + 70 * Math.sin(startAngle - Math.PI / 2);
                  const x2 = 100 + 70 * Math.cos(endAngle - Math.PI / 2);
                  const y2 = 100 + 70 * Math.sin(endAngle - Math.PI / 2);
                  const x3 = 100 + 50 * Math.cos(endAngle - Math.PI / 2);
                  const y3 = 100 + 50 * Math.sin(endAngle - Math.PI / 2);
                  const x4 = 100 + 50 * Math.cos(startAngle - Math.PI / 2);
                  const y4 = 100 + 50 * Math.sin(startAngle - Math.PI / 2);
                  return (
                    <path key={i}
                      d={`M${x1},${y1} A70,70 0 ${largeArc},1 ${x2},${y2} L${x3},${y3} A50,50 0 ${largeArc},0 ${x4},${y4} Z`}
                      fill={s.color} />
                  );
                });
              })()}
            </svg>
          </div>
          <div style={{ display: 'flex', gap: '1.5rem', flexWrap: 'wrap', justifyContent: 'center' }}>
            {salesDist.map((s) => (
              <div key={s.label} style={{ display: 'flex', alignItems: 'center', gap: '0.375rem', fontSize: '0.8125rem' }}>
                <span style={{ width: 10, height: 10, borderRadius: '50%', background: s.color, flexShrink: 0 }} />
                {s.label} <span style={{ fontWeight: 700, color: 'var(--color-text-primary)' }}>{s.pct.toFixed(1)}%</span>
              </div>
            ))}
          </div>
        </div>

        {/* Top Performing Products */}
        <div className="card">
          <h3 style={{ fontSize: '1.125rem', fontWeight: 700, marginBottom: '1.25rem' }}>Top Performing Products</h3>
          {stats.top_products.length > 0 ? stats.top_products.map((p, i) => (
            <div key={i} className="top-product-item" style={{ borderBottom: i < stats.top_products.length - 1 ? '1px solid var(--color-border-light)' : 'none', paddingBottom: '0.875rem' }}>
              <span className="rank">#{i + 1}</span>
              <div style={{ flex: 1 }}>
                <div style={{ fontWeight: 600, fontSize: '0.875rem' }}>{p.name}</div>
                <div style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)' }}>{p.quantity} units sold</div>
                <div className="product-bar" style={{ marginTop: '0.375rem' }}>
                  <div className="fill" style={{ width: `${(p.revenue / stats.top_products[0].revenue) * 100}%` }} />
                </div>
              </div>
              <div style={{ textAlign: 'right' }}>
                <div style={{ fontWeight: 700, color: 'var(--color-primary)' }}>{p.revenue.toLocaleString()} DT</div>
              </div>
            </div>
          )) : (
            <div style={{ color: 'var(--text-muted)' }}>No products sold yet.</div>
          )}
        </div>
      </div>

      {/* Peak Hours */}
      <div className="card">
        <h3 style={{ fontSize: '1.125rem', fontWeight: 700, marginBottom: '1.25rem' }}>Peak Hours Analysis</h3>
        <div style={{ display: 'flex', alignItems: 'flex-end', gap: '0.375rem', height: 180 }}>
          {peakHours.map((h, i) => (
            <div key={i} style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '0.375rem' }}>
              <div style={{
                width: '100%',
                height: `${(h.value / maxPeak) * 160}px`,
                background: h.value > maxPeak * 0.7 ? '#DC3545' : '#F4845F',
                borderRadius: '4px 4px 0 0',
                transition: 'height 0.3s ease',
              }} />
              <span style={{ fontSize: '0.625rem', color: 'var(--color-text-muted)' }}>{h.hour}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
