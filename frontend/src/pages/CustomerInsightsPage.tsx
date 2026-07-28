import { useEffect, useMemo, useState } from 'react';
import { Crown, Search, TrendingUp, Users, WalletCards } from 'lucide-react';
import api from '../api';
import type { Customer } from '../types';

interface SegmentSummary {
  segment: string;
  customers: number;
  total_revenue?: number;
  avg_monetary?: number;
  recommended_action?: string;
}

interface SegmentationOverview {
  total_customers: number;
  hybrid_segments: SegmentSummary[];
  rfm_segments: SegmentSummary[];
  kmeans_segments: SegmentSummary[];
}

export default function CustomerInsightsPage() {
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [segments, setSegments] = useState<SegmentationOverview | null>(null);
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      api.get('/api/customers?limit=200'),
      api.get('/api/ai/segmentation/overview'),
    ])
      .then(([customerRes, segmentRes]) => {
        setCustomers(customerRes.data);
        setSegments(segmentRes.data);
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  const filteredCustomers = useMemo(() => {
    const term = search.trim().toLowerCase();
    if (!term) return customers;
    return customers.filter((customer) =>
      [customer.name, customer.phone, customer.email, customer.archetype, customer.price_tier]
        .some((value) => value?.toLowerCase().includes(term))
    );
  }, [customers, search]);

  const totalSpent = customers.reduce((sum, customer) => sum + (customer.total_spent || 0), 0);
  const activeCustomers = customers.filter((customer) => customer.visit_count > 0).length;
  const topCustomer = customers.reduce<Customer | null>(
    (best, customer) => (!best || customer.total_spent > best.total_spent ? customer : best),
    null
  );
  const topSegments = [...(segments?.hybrid_segments || [])]
    .sort((a, b) => b.customers - a.customers)
    .slice(0, 5);
  const maxSegmentCustomers = Math.max(1, ...topSegments.map((segment) => segment.customers));

  const kpis = [
    {
      label: 'Loaded Customers',
      value: customers.length.toLocaleString(),
      hint: segments ? `${segments.total_customers.toLocaleString()} modeled in AI segments` : 'From CRM records',
      icon: <Users size={20} />,
      color: '#DC3545',
      bg: '#FFF5F5',
    },
    {
      label: 'Known Active',
      value: activeCustomers.toLocaleString(),
      hint: 'Customers with recorded visits',
      icon: <TrendingUp size={20} />,
      color: '#28A745',
      bg: '#E8F5E9',
    },
    {
      label: 'Tracked Spend',
      value: `${totalSpent.toLocaleString(undefined, { maximumFractionDigits: 0 })} DT`,
      hint: 'Across loaded customer records',
      icon: <WalletCards size={20} />,
      color: '#17A2B8',
      bg: '#E8F6F8',
    },
    {
      label: 'Top Customer',
      value: topCustomer ? `#${topCustomer.id}` : 'N/A',
      hint: topCustomer ? `${topCustomer.total_spent.toFixed(2)} DT lifetime spend` : 'No customer spend yet',
      icon: <Crown size={20} />,
      color: '#F59E0B',
      bg: '#FFF8E1',
    },
  ];

  return (
    <div className="animate-fadeIn">
      <div className="page-header">
        <h2>Customer Insights</h2>
        <p>Customer value, preferences, and AI segment signals in one CRM view</p>
      </div>

      <div className="grid-4" style={{ marginBottom: '1.5rem' }}>
        {kpis.map((kpi) => (
          <div key={kpi.label} className="kpi-card">
            <div>
              <div className="kpi-label">{kpi.label}</div>
              <div className="kpi-value" style={{ fontSize: '1.5rem' }}>{kpi.value}</div>
              <div style={{ fontSize: '0.75rem', color: 'var(--color-text-secondary)', marginTop: '0.25rem' }}>
                {kpi.hint}
              </div>
            </div>
            <div className="kpi-icon" style={{ background: kpi.bg, color: kpi.color }}>{kpi.icon}</div>
          </div>
        ))}
      </div>

      <div className="grid-2" style={{ gridTemplateColumns: '1.15fr 0.85fr', marginBottom: '1.5rem' }}>
        <div className="card">
          <h3 style={{ fontSize: '1.125rem', fontWeight: 700, marginBottom: '1rem' }}>Top Hybrid Segments</h3>
          {topSegments.length > 0 ? topSegments.map((segment) => (
            <div key={segment.segment} style={{ marginBottom: '1rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', gap: '1rem', marginBottom: '0.375rem' }}>
                <span style={{ fontWeight: 600 }}>{segment.segment}</span>
                <span style={{ color: 'var(--color-text-secondary)', fontSize: '0.875rem' }}>
                  {segment.customers.toLocaleString()} customers
                </span>
              </div>
              <div className="product-bar">
                <div className="fill" style={{ width: `${(segment.customers / maxSegmentCustomers) * 100}%` }} />
              </div>
              {segment.recommended_action && (
                <div style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)', marginTop: '0.35rem' }}>
                  {segment.recommended_action}
                </div>
              )}
            </div>
          )) : (
            <div style={{ color: 'var(--color-text-muted)' }}>No segment data available.</div>
          )}
        </div>

        <div className="card">
          <h3 style={{ fontSize: '1.125rem', fontWeight: 700, marginBottom: '1rem' }}>Customer Mix</h3>
          {['price_tier', 'day_preference', 'time_preference'].map((field) => {
            const values = customers.reduce<Record<string, number>>((acc, customer) => {
              const key = String(customer[field as keyof Customer] || 'Unknown');
              acc[key] = (acc[key] || 0) + 1;
              return acc;
            }, {});
            const top = Object.entries(values).sort((a, b) => b[1] - a[1]).slice(0, 3);
            return (
              <div key={field} style={{ marginBottom: '1rem' }}>
                <div className="kpi-label" style={{ marginBottom: '0.4rem', textTransform: 'capitalize' }}>
                  {field.replace('_', ' ')}
                </div>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
                  {top.map(([label, count]) => (
                    <span key={label} className="badge badge-info">{label}: {count}</span>
                  ))}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
        <div style={{ padding: '1.25rem 1.5rem', display: 'flex', justifyContent: 'space-between', gap: '1rem', alignItems: 'center' }}>
          <h3 style={{ fontSize: '1.125rem', fontWeight: 700 }}>Customer Records</h3>
          <div style={{ position: 'relative', width: 320, maxWidth: '100%' }}>
            <Search size={16} style={{ position: 'absolute', left: '0.75rem', top: '50%', transform: 'translateY(-50%)', color: 'var(--color-text-muted)' }} />
            <input
              className="input"
              placeholder="Search customers..."
              value={search}
              onChange={(event) => setSearch(event.target.value)}
              style={{ width: '100%', paddingLeft: '2.25rem' }}
            />
          </div>
        </div>

        <table className="data-table">
          <thead>
            <tr>
              <th>Customer</th>
              <th>Contact</th>
              <th>Archetype</th>
              <th>Tier</th>
              <th>Preferences</th>
              <th>Visits</th>
              <th>Total Spent</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td colSpan={7} style={{ textAlign: 'center', padding: '2rem' }}>Loading customers...</td></tr>
            ) : filteredCustomers.length > 0 ? filteredCustomers.map((customer) => (
              <tr key={customer.id}>
                <td style={{ fontWeight: 600 }}>{customer.name}</td>
                <td style={{ color: 'var(--color-text-secondary)', fontSize: '0.8125rem' }}>
                  <div>{customer.phone || 'No phone'}</div>
                  <div>{customer.email || 'No email'}</div>
                </td>
                <td>{customer.archetype || 'N/A'}</td>
                <td><span className="badge badge-primary">{customer.price_tier || 'Unknown'}</span></td>
                <td style={{ color: 'var(--color-text-secondary)' }}>
                  {[customer.day_preference, customer.time_preference].filter(Boolean).join(' / ') || 'N/A'}
                </td>
                <td>{customer.visit_count}</td>
                <td style={{ fontWeight: 700, color: 'var(--color-primary)' }}>{customer.total_spent.toFixed(2)} DT</td>
              </tr>
            )) : (
              <tr><td colSpan={7} style={{ textAlign: 'center', padding: '2rem', color: 'var(--color-text-muted)' }}>No customers match your search.</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
