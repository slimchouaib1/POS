import { useState, useEffect } from 'react';
import api from '../api';
import { TrendingUp, BarChart3, ShoppingCart } from 'lucide-react';
import { Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Area, AreaChart } from 'recharts';
import CustomSelect from '../components/CustomSelect';

export default function ForecastingPage() {
  const [itemName, setItemName] = useState('');
  const [section, setSection] = useState('');
  const [forecast, setForecast] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [products, setProducts] = useState<any[]>([]);

  useEffect(() => {
    api.get('/api/products').then(res => setProducts(res.data)).catch(console.error);
  }, []);

  const runForecast = async () => {
    setLoading(true);
    try {
      const res = await api.post('/api/ai/forecasting/predict', {
        item_name: itemName || undefined,
        section: section || undefined,
        horizon_weeks: 8,
      });
      setForecast(res.data);
    } catch (e) { console.error(e); }
    setLoading(false);
  };

  return (
    <div className="animate-fadeIn">
      <div className="page-header">
        <h2 style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <TrendingUp size={24} color="var(--success)" /> Demand Forecasting
        </h2>
        <p>Global LightGBM Model — Weekly sales prediction per menu item</p>
      </div>

      {/* Filters */}
      <div className="card" style={{ marginBottom: '1.5rem' }}>
        <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap' }}>
          <CustomSelect 
            options={[{value: '', label: 'All products'}, ...products.map(p => ({ value: p.name, label: p.name }))]}
            value={itemName} 
            onChange={setItemName}
            style={{ flex: 1, minWidth: 200 }}
          />
          <CustomSelect
            options={[{value: '', label: 'All sections'}, ...['American', 'Cafe', 'Healthy_Vegan', 'Italian', 'Japanese', 'Mexican', 'Steakhouse'].map(s => ({ value: s, label: s }))]}
            value={section}
            onChange={setSection}
            style={{ width: 200 }}
          />
          <button className="btn btn-primary" onClick={runForecast} disabled={loading}>
            <BarChart3 size={16} /> {loading ? 'Analyzing...' : 'Forecast Sales'}
          </button>
        </div>
      </div>

      {forecast && !forecast.error && (
        <div>
          {/* KPIs */}
          <div className="grid-3" style={{ marginBottom: '1.5rem' }}>
            <div className="kpi-card">
              <div className="kpi-icon" style={{ background: forecast.trend_direction === 'hausse' ? 'rgba(16,185,129,0.15)' : forecast.trend_direction === 'baisse' ? 'rgba(239,68,68,0.15)' : 'rgba(59,130,246,0.15)' }}>
                <TrendingUp size={24} color={forecast.trend_direction === 'hausse' ? '#34d399' : forecast.trend_direction === 'baisse' ? '#f87171' : '#60a5fa'} />
              </div>
              <div>
                <div className="kpi-value" style={{ color: forecast.trend_direction === 'hausse' ? '#34d399' : forecast.trend_direction === 'baisse' ? '#f87171' : '#60a5fa' }}>
                  {forecast.trend > 0 ? '+' : ''}{forecast.trend}%
                </div>
                <div className="kpi-label">Trend ({forecast.trend_direction === 'hausse' ? 'Up' : forecast.trend_direction === 'baisse' ? 'Down' : forecast.trend_direction})</div>
              </div>
            </div>
            <div className="kpi-card">
              <div className="kpi-icon" style={{ background: 'rgba(99,102,241,0.15)' }}>
                <ShoppingCart size={24} color="#818cf8" />
              </div>
              <div>
                <div className="kpi-value" style={{ color: '#818cf8' }}>{forecast.predicted_sales_next_week}</div>
                <div className="kpi-label">Predicted Sales (next week)</div>
              </div>
            </div>
            <div className="kpi-card">
              <div className="kpi-icon" style={{ background: 'rgba(245,158,11,0.15)' }}>
                <BarChart3 size={24} color="#fbbf24" />
              </div>
              <div>
                <div className="kpi-value" style={{ color: '#fbbf24' }}>{forecast.recent_avg_demand}</div>
                <div className="kpi-label">Recent average / week</div>
              </div>
            </div>
          </div>

          {/* Chart */}
          {forecast.forecast && forecast.forecast.length > 0 && (
            <div className="card" style={{ marginBottom: '1.5rem' }}>
              <h3 style={{ fontSize: '1rem', fontWeight: 600, marginBottom: '1rem' }}>Sales Forecast — {forecast.item}</h3>
              <ResponsiveContainer width="100%" height={300}>
                <AreaChart data={forecast.forecast}>
                  <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                  <XAxis dataKey="week_offset" tick={{ fill: 'var(--text-secondary)', fontSize: 12 }} label={{ value: 'Week', fill: 'var(--text-muted)', fontSize: 12 }} />
                  <YAxis tick={{ fill: 'var(--text-secondary)', fontSize: 12 }} label={{ value: 'Units sold', angle: -90, fill: 'var(--text-muted)', fontSize: 12 }} />
                  <Tooltip contentStyle={{ background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: 8, color: 'var(--text-primary)' }} />
                  <Area type="monotone" dataKey="confidence_upper" stroke="none" fill="rgba(99,102,241,0.1)" name="Upper bound" />
                  <Area type="monotone" dataKey="confidence_lower" stroke="none" fill="var(--bg-main)" name="Lower bound" />
                  <Line type="monotone" dataKey="predicted_demand" stroke="#6366f1" strokeWidth={3} dot={{ fill: '#6366f1', r: 5 }} name="Predicted sales" />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          )}

          {/* Explanation */}
          <div className="card" style={{ background: 'rgba(99,102,241,0.08)', border: '1px solid rgba(99,102,241,0.2)' }}>
            <div style={{ fontSize: '0.8125rem', fontWeight: 600, marginBottom: '0.5rem', color: 'var(--primary-light)' }}>
              💡 Explanation (XAI)
            </div>
            <p style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', lineHeight: 1.6 }}>
              {forecast.explanation}
            </p>
          </div>
        </div>
      )}

      {forecast?.error && (
        <div className="card" style={{ textAlign: 'center', color: 'var(--text-muted)', padding: '3rem' }}>
          {forecast.error}
        </div>
      )}
    </div>
  );
}
