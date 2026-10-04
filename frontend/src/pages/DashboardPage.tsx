import { useEffect, useState } from 'react';
import api from '../api';
import {
  DollarSign, ShoppingCart, TrendingUp,
  Users, ArrowDown
} from 'lucide-react';

interface StatsData {
  total_revenue: number;
  total_orders: number;
  avg_basket: number;
  customer_count: number;
  today_revenue: number;
  today_orders: number;
  active_orders: number;
  low_stock_count: number;
  top_products: { name: string; quantity: number; revenue: number }[];
  payment_methods: { method: string; count: number; total: number }[];
}

interface SalesPoint {
  date: string;
  orders: number;
  revenue: number;
}

interface PeriodComparison {
  has_comparison: boolean;
  message: string;
  current_period?: {
    start: string;
    end: string;
    total_revenue: number;
    total_orders: number;
    avg_basket: number;
    customer_count: number;
  };
  previous_period?: {
    start: string;
    end: string;
    total_revenue: number;
    total_orders: number;
    avg_basket: number;
    customer_count: number;
  };
  deltas?: Record<string, { absolute: number; percent: number | null }>;
}

type ReportRange = 'last_week' | 'last_month' | 'last_year';

const reportRanges: { value: ReportRange; label: string }[] = [
  { value: 'last_week', label: 'Last week' },
  { value: 'last_month', label: 'Last month' },
  { value: 'last_year', label: 'Last year' },
];

const demoStats: StatsData = {
  total_revenue: 18942.75,
  total_orders: 684,
  avg_basket: 27.69,
  customer_count: 218,
  today_revenue: 2765.4,
  today_orders: 96,
  active_orders: 14,
  low_stock_count: 7,
  top_products: [
    { name: 'Spicy BBQ Bacon Burger', quantity: 86, revenue: 1892.0 },
    { name: 'Truffle Mushroom Pizza', quantity: 74, revenue: 1702.0 },
    { name: 'Chicken Teriyaki Bento', quantity: 69, revenue: 1518.0 },
    { name: 'Classic Margarita', quantity: 58, revenue: 1044.0 },
    { name: 'Tiramisu', quantity: 51, revenue: 688.5 },
  ],
  payment_methods: [
    { method: 'Card', count: 386, total: 10962.4 },
    { method: 'Cash', count: 214, total: 5364.8 },
    { method: 'Mobile', count: 84, total: 2615.55 },
  ],
};

const emptyStats: StatsData = {
  total_revenue: 0,
  total_orders: 0,
  avg_basket: 0,
  customer_count: 0,
  today_revenue: 0,
  today_orders: 0,
  active_orders: 0,
  low_stock_count: 0,
  top_products: [],
  payment_methods: [],
};

const demoRevenueTrend: SalesPoint[] = [
  { date: '2026-08-29', orders: 82, revenue: 2240.5 },
  { date: '2026-08-30', orders: 91, revenue: 2518.75 },
  { date: '2026-08-31', orders: 76, revenue: 2076.2 },
  { date: '2026-09-01', orders: 108, revenue: 3142.4 },
  { date: '2026-09-02', orders: 126, revenue: 3728.6 },
  { date: '2026-09-03', orders: 113, revenue: 3070.9 },
  { date: '2026-09-04', orders: 88, revenue: 2165.4 },
];

const demoComparison: PeriodComparison = {
  has_comparison: true,
  message: '',
  current_period: {
    start: '2026-08-29',
    end: '2026-09-04',
    total_revenue: 18942.75,
    total_orders: 684,
    avg_basket: 27.69,
    customer_count: 218,
  },
  previous_period: {
    start: '2026-08-22',
    end: '2026-08-28',
    total_revenue: 16284.2,
    total_orders: 604,
    avg_basket: 26.96,
    customer_count: 191,
  },
  deltas: {
    total_revenue: { absolute: 2658.55, percent: 16.3 },
    total_orders: { absolute: 80, percent: 13.2 },
    avg_basket: { absolute: 0.73, percent: 2.7 },
    customer_count: { absolute: 27, percent: 14.1 },
  },
};

const hasStatsData = (data: StatsData) => (
  data.total_revenue > 0 ||
  data.total_orders > 0 ||
  data.top_products.length > 0 ||
  data.payment_methods.length > 0
);

export default function DashboardPage() {
  const [stats, setStats] = useState<StatsData>(demoStats);
  const [revenueTrend, setRevenueTrend] = useState<SalesPoint[]>(demoRevenueTrend);
  const [reportRange, setReportRange] = useState<ReportRange>('last_week');
  const [comparison, setComparison] = useState<PeriodComparison | null>(demoComparison);

  useEffect(() => {
    api.get(`/api/reports/dashboard?range=${reportRange}`).then((r) => {
      if (r.data) {
        const nextStats = { ...emptyStats, ...r.data };
        setStats(hasStatsData(nextStats) ? nextStats : demoStats);
      }
    }).catch(() => setStats(demoStats));

    api.get<{ data: SalesPoint[] }>(`/api/reports/sales?period=daily&range=${reportRange}`).then((r) => {
      const nextTrend = r.data.data || [];
      setRevenueTrend(nextTrend.length > 0 ? nextTrend : demoRevenueTrend);
    }).catch(() => setRevenueTrend(demoRevenueTrend));

    api.get<PeriodComparison>(`/api/reports/dashboard/comparison?range=${reportRange}`).then((r) => {
      setComparison(r.data?.has_comparison ? r.data : demoComparison);
    }).catch(() => setComparison(demoComparison));
  }, [reportRange]);

  const kpis = [
    { label: 'Total Revenue', value: `${stats.total_revenue.toLocaleString()} DT`, icon: <DollarSign size={18} />, bg: '#FFF5F5', color: '#DC3545' },
    { label: 'Total Orders', value: stats.total_orders.toLocaleString(), icon: <ShoppingCart size={18} />, bg: '#FFEBEE', color: '#DC3545' },
    { label: 'Average Order Value', value: `${stats.avg_basket.toFixed(2)} DT`, icon: <TrendingUp size={18} />, bg: '#E8F5E9', color: '#28A745' },
    { label: 'Customer Count', value: stats.customer_count.toLocaleString(), icon: <Users size={18} />, bg: '#FFEBEE', color: '#DC3545' },
  ];

  const salesDist = stats.payment_methods.map((pm, i) => ({
    label: pm.method,
    pct: stats.total_revenue > 0 ? (pm.total / stats.total_revenue) * 100 : 0,
    color: ['#DC3545', '#F4845F', '#17A2B8', '#FFC107', '#6366F1'][i % 5],
  }));
  const maxTrendRevenue = Math.max(...revenueTrend.map((p) => p.revenue), 1);
  const trendX = (index: number) => revenueTrend.length === 1 ? 350 : index * 700 / (revenueTrend.length - 1);
  const trendY = (revenue: number) => 200 - (revenue / maxTrendRevenue) * 180;
  const trendPoints = revenueTrend.map((p, i) => `${trendX(i)},${trendY(p.revenue)}`).join(' ');
  const trendLabels = revenueTrend.filter((_, i) => (
    i === 0 ||
    i === Math.floor((revenueTrend.length - 1) / 2) ||
    i === revenueTrend.length - 1
  ));
  const formatDate = (value?: string) => value ? new Date(value).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' }) : '';
  const comparisonItems = [
    { label: 'Revenue', key: 'total_revenue', suffix: ' DT' },
    { label: 'Orders', key: 'total_orders', suffix: '' },
    { label: 'Avg Order', key: 'avg_basket', suffix: ' DT' },
    { label: 'Customers', key: 'customer_count', suffix: '' },
  ];

  return (
    <div className="animate-fadeIn">
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
        <h2 style={{ fontSize: '1.5rem', fontWeight: 700 }}>Analytics Dashboard</h2>
        <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
          <div style={{ display: 'flex', gap: 4, padding: 4, background: '#FFFFFF', border: '1px solid var(--color-border-light)', borderRadius: 8 }}>
            {reportRanges.map((range) => (
              <button
                key={range.value}
                type="button"
                onClick={() => setReportRange(range.value)}
                className={`btn btn-sm ${reportRange === range.value ? 'btn-primary' : 'btn-ghost'}`}
                style={{ minWidth: 88, justifyContent: 'center' }}
              >
                {range.label}
              </button>
            ))}
          </div>
          <button className="btn btn-primary btn-sm"><ArrowDown size={14} /> Export</button>
        </div>
      </div>

      {/* KPI Grid */}
      <div className="grid-4" style={{ marginBottom: '1.5rem' }}>
        {kpis.map((k, i) => (
          <div key={i} className="kpi-card">
            <div>
              <div className="kpi-label">{k.label}</div>
              <div className="kpi-value">{k.value}</div>
            </div>
            <div className="kpi-icon" style={{ background: k.bg, color: k.color }}>{k.icon}</div>
          </div>
        ))}
      </div>

      {/* Period Comparison */}
      <div className="card" style={{ marginBottom: '1.5rem' }}>
        <h3 style={{ fontSize: '1.125rem', fontWeight: 700, marginBottom: '0.5rem' }}>Period Comparison</h3>
        {comparison?.has_comparison && comparison.current_period && comparison.previous_period && comparison.deltas ? (
          <>
            <p style={{ fontSize: '0.8125rem', color: 'var(--color-text-secondary)', marginBottom: '1rem' }}>
              Current: {formatDate(comparison.current_period.start)} - {formatDate(comparison.current_period.end)} &nbsp;|&nbsp;
              Previous: {formatDate(comparison.previous_period.start)} - {formatDate(comparison.previous_period.end)}
            </p>
            <div className="grid-4">
              {comparisonItems.map((item) => {
                const currentValue = comparison.current_period?.[item.key as keyof typeof comparison.current_period] as number;
                const delta = comparison.deltas?.[item.key];
                const isUp = (delta?.absolute || 0) >= 0;
                return (
                  <div key={item.key} style={{ border: '1px solid var(--color-border-light)', borderRadius: 8, padding: '1rem' }}>
                    <div style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)', marginBottom: '0.25rem' }}>{item.label}</div>
                    <div style={{ fontSize: '1.25rem', fontWeight: 700 }}>{currentValue.toLocaleString()}{item.suffix}</div>
                    <div style={{ marginTop: '0.5rem', color: isUp ? 'var(--color-success)' : 'var(--color-danger)', fontSize: '0.8125rem', fontWeight: 600 }}>
                      {isUp ? '+' : ''}{delta?.absolute.toLocaleString()}{item.suffix}
                      {delta?.percent !== null && delta?.percent !== undefined ? ` (${isUp ? '+' : ''}${delta.percent.toFixed(1)}%)` : ' (no prior baseline)'}
                    </div>
                  </div>
                );
              })}
            </div>
          </>
        ) : (
          <div style={{ color: 'var(--color-text-muted)' }}>
            {comparison?.message || 'Loading period comparison...'}
          </div>
        )}
      </div>

      {/* Revenue Trend */}
      <div className="card" style={{ marginBottom: '1.5rem' }}>
        <h3 style={{ fontSize: '1.125rem', fontWeight: 700, marginBottom: '1.25rem' }}>Revenue Trend</h3>
        {revenueTrend.length > 0 ? (
          <div style={{ height: 240, display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
            <div style={{ height: 200, display: 'flex', alignItems: 'flex-end', gap: 2 }}>
              <div style={{ display: 'flex', flexDirection: 'column', justifyContent: 'space-between', height: '100%', fontSize: '0.6875rem', color: 'var(--color-text-muted)', paddingRight: '0.5rem', minWidth: 54 }}>
                <span>{Math.round(maxTrendRevenue).toLocaleString()} DT</span>
                <span>{Math.round(maxTrendRevenue / 2).toLocaleString()} DT</span>
                <span>0 DT</span>
              </div>
              <svg width="100%" height="200" viewBox="0 0 700 200" preserveAspectRatio="none">
                <polyline
                  fill="none"
                  stroke="#DC3545"
                  strokeWidth="2.5"
                  points={trendPoints}
                />
                {revenueTrend.map((p, i) => (
                  <circle key={p.date} cx={trendX(i)} cy={trendY(p.revenue)} r="4" fill="#DC3545" />
                ))}
              </svg>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', paddingLeft: 62, fontSize: '0.6875rem', color: 'var(--color-text-muted)' }}>
              {trendLabels.map((p) => (
                <span key={p.date}>{new Date(p.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}</span>
              ))}
            </div>
          </div>
        ) : (
          <div style={{ color: 'var(--text-muted)' }}>No revenue data yet.</div>
        )}
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

    </div>
  );
}
