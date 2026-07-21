import { useEffect, useState } from 'react';
import api from '../api';
import type { AnomalyAlert } from '../types';
import { ShieldAlert, AlertTriangle, Shield, ChevronRight, X, FileText, Clock, User, CreditCard, ShoppingBag, Hash, TrendingDown, Percent, AlertCircle } from 'lucide-react';

export default function AnomaliesPage() {
  const [alerts, setAlerts] = useState<AnomalyAlert[]>([]);
  const [selected, setSelected] = useState<any>(null);
  const [metadata, setMetadata] = useState<any>(null);
  const [orderDetails, setOrderDetails] = useState<any>(null);
  const [orderLoading, setOrderLoading] = useState(false);
  const [showOrderModal, setShowOrderModal] = useState(false);

  useEffect(() => {
    loadAlerts();
    api.get('/api/ai/anomaly/metadata').then((r) => setMetadata(r.data));
  }, []);

  const loadAlerts = (riskLevel?: string) => {
    const params = riskLevel ? `?risk_level=${riskLevel}&limit=200` : '?limit=200';
    api.get(`/api/ai/anomaly/alerts${params}`).then((r) => setAlerts(r.data));
  };

  const loadDetail = async (id: number) => {
    const res = await api.get(`/api/ai/anomaly/alerts/${id}`);
    setSelected(res.data);
    setOrderDetails(null);
    setShowOrderModal(false);
  };

  const loadOrderDetails = async (orderId: string) => {
    setOrderLoading(true);
    try {
      const res = await api.get(`/api/ai/anomaly/order-details/${orderId}`);
      setOrderDetails(res.data);
      setShowOrderModal(true);
    } catch (e) {
      console.error(e);
      setOrderDetails(null);
    }
    setOrderLoading(false);
  };

  const updateStatus = async (id: number, status: string) => {
    await api.patch(`/api/ai/anomaly/alerts/${id}/status?status=${status}`);
    loadDetail(id);
    loadAlerts();
  };

  const riskColor = (level: string) => level === 'CRITIQUE' ? '#ef4444' : level === 'ALERTE' ? '#f59e0b' : '#10b981';
  const riskBg = (level: string) => level === 'CRITIQUE' ? 'rgba(239,68,68,0.15)' : level === 'ALERTE' ? 'rgba(245,158,11,0.15)' : 'rgba(16,185,129,0.15)';
  const fmt = (v: any, decimals = 2) => v != null ? Number(v).toFixed(decimals) : '—';
  const fmtPct = (v: any) => v != null ? (Number(v) * 100).toFixed(1) + '%' : '—';

  const critiques = alerts.filter((a) => a.risk_level === 'CRITIQUE').length;
  const alertes = alerts.filter((a) => a.risk_level === 'ALERTE').length;

  const DetailRow = ({ label, value, icon }: { label: string; value: any; icon?: any }) => (
    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '0.5rem 0', borderBottom: '1px solid var(--color-border-light)' }}>
      <span style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)', display: 'flex', alignItems: 'center', gap: '0.375rem' }}>
        {icon} {label}
      </span>
      <span style={{ fontSize: '0.8125rem', fontWeight: 600, color: 'var(--color-text-primary)' }}>{value ?? '—'}</span>
    </div>
  );

  return (
    <div className="animate-fadeIn">
      <div className="page-header">
        <h2 style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <ShieldAlert size={24} color="#f87171" /> Anomaly Detection
        </h2>
        <p>Random Forest — {metadata?.total_alerts || alerts.length} alerts • Threshold: {metadata?.thresholds?.decision_threshold?.toFixed(4) || '0.2545'}</p>
      </div>

      {/* KPIs */}
      <div className="grid-4" style={{ marginBottom: '1.5rem' }}>
        <div className="kpi-card" onClick={() => { loadAlerts(); }} style={{ cursor: 'pointer' }}>
          <div className="kpi-icon" style={{ background: 'rgba(99,102,241,0.15)' }}><Shield size={24} color="#818cf8" /></div>
          <div><div className="kpi-value" style={{ color: '#818cf8' }}>{alerts.length}</div><div className="kpi-label">Total alerts</div></div>
        </div>
        <div className="kpi-card" onClick={() => { loadAlerts('CRITIQUE'); }} style={{ cursor: 'pointer' }}>
          <div className="kpi-icon" style={{ background: 'rgba(239,68,68,0.15)' }}><AlertTriangle size={24} color="#f87171" /></div>
          <div><div className="kpi-value" style={{ color: '#f87171' }}>{critiques}</div><div className="kpi-label">Critical</div></div>
        </div>
        <div className="kpi-card" onClick={() => { loadAlerts('ALERTE'); }} style={{ cursor: 'pointer' }}>
          <div className="kpi-icon" style={{ background: 'rgba(245,158,11,0.15)' }}><AlertTriangle size={24} color="#fbbf24" /></div>
          <div><div className="kpi-value" style={{ color: '#fbbf24' }}>{alertes}</div><div className="kpi-label">Alerts</div></div>
        </div>
        <div className="kpi-card">
          <div className="kpi-icon" style={{ background: 'rgba(16,185,129,0.15)' }}><Shield size={24} color="#34d399" /></div>
          <div><div className="kpi-value" style={{ color: '#34d399' }}>{metadata?.f1_score ? (metadata.f1_score * 100).toFixed(1) + '%' : 'N/A'}</div><div className="kpi-label">F1-Score</div></div>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: selected ? '1fr 400px' : '1fr', gap: '1.5rem' }}>
        {/* Alert List */}
        <div className="card" style={{ padding: 0, overflow: 'auto', maxHeight: 'calc(100vh - 340px)' }}>
          <table className="data-table">
            <thead>
              <tr>
                <th>Order</th>
                <th>Risk</th>
                <th>Score</th>
                <th>Type</th>
                <th>Status</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {alerts.map((a) => (
                <tr key={a.id} onClick={() => loadDetail(a.id)} style={{ cursor: 'pointer' }}>
                  <td style={{ fontWeight: 600 }}>#{a.order_id}</td>
                  <td>
                    <span style={{ padding: '0.25rem 0.625rem', borderRadius: 9999, fontSize: '0.75rem', fontWeight: 600, background: riskBg(a.risk_level), color: riskColor(a.risk_level) }}>
                      {a.risk_level}
                    </span>
                  </td>
                  <td style={{ fontWeight: 600 }}>{(a.risk_score * 100).toFixed(1)}%</td>
                  <td style={{ fontSize: '0.8125rem', color: 'var(--color-text-secondary)' }}>{a.anomaly_type || '—'}</td>
                  <td><span className="badge badge-info">{a.status}</span></td>
                  <td><ChevronRight size={14} color="var(--color-text-muted)" /></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Detail Panel */}
        {selected && (
          <div className="card animate-slideIn" style={{ maxHeight: 'calc(100vh - 340px)', overflow: 'auto' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
              <h3 style={{ fontSize: '1rem', fontWeight: 700 }}>Alert #{selected.order_id}</h3>
              <span style={{ padding: '0.25rem 0.625rem', borderRadius: 9999, fontSize: '0.75rem', fontWeight: 700, background: riskBg(selected.risk_level), color: riskColor(selected.risk_level) }}>
                {selected.risk_level}
              </span>
            </div>

            {/* Risk gauge */}
            <div style={{ marginBottom: '1rem', padding: '1rem', background: 'var(--color-bg-page)', borderRadius: 'var(--radius-sm)' }}>
              <div style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)', marginBottom: '0.5rem' }}>Risk score</div>
              <div style={{ width: '100%', height: 8, background: 'var(--color-border)', borderRadius: 4, overflow: 'hidden' }}>
                <div style={{ width: `${selected.risk_score * 100}%`, height: '100%', background: `linear-gradient(90deg, #10b981, #f59e0b, #ef4444)`, borderRadius: 4, transition: 'width 0.5s' }} />
              </div>
              <div style={{ fontSize: '1.25rem', fontWeight: 700, marginTop: '0.5rem', color: riskColor(selected.risk_level) }}>
                {(selected.risk_score * 100).toFixed(2)}%
              </div>
            </div>

            {/* Explanation */}
            <div style={{ marginBottom: '1rem', padding: '0.75rem', background: 'rgba(99,102,241,0.08)', borderRadius: 'var(--radius-sm)', border: '1px solid rgba(99,102,241,0.2)' }}>
              <div style={{ fontSize: '0.75rem', fontWeight: 600, marginBottom: '0.25rem', color: '#6366f1' }}>💡 Explanation</div>
              <p style={{ fontSize: '0.8125rem', color: 'var(--color-text-secondary)', lineHeight: 1.5 }}>{selected.alert_explanation}</p>
            </div>

            {/* View Order Details button */}
            <button
              className="btn btn-primary"
              onClick={() => loadOrderDetails(selected.order_id)}
              disabled={orderLoading}
              style={{ width: '100%', marginBottom: '1rem', gap: '0.5rem' }}
            >
              <FileText size={16} />
              {orderLoading ? 'Chargement...' : 'Voir détails de la commande'}
            </button>

            {/* Status actions */}
            <div style={{ marginBottom: '1rem' }}>
              <div style={{ fontSize: '0.75rem', fontWeight: 600, marginBottom: '0.5rem', color: 'var(--color-text-muted)' }}>Change status:</div>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.375rem' }}>
                {['assigned', 'under_review', 'confirmed_fraud', 'false_positive', 'closed'].map((s) => (
                  <button key={s} className="btn btn-ghost btn-sm" onClick={() => updateStatus(selected.id, s)}
                    style={{ fontSize: '0.6875rem' }}>
                    {s.replace('_', ' ')}
                  </button>
                ))}
              </div>
            </div>

            {/* Comments */}
            {selected.comments?.length > 0 && (
              <div>
                <div style={{ fontSize: '0.75rem', fontWeight: 600, marginBottom: '0.5rem', color: 'var(--color-text-muted)' }}>History:</div>
                {selected.comments.map((c: any) => (
                  <div key={c.id} style={{ padding: '0.5rem', marginBottom: '0.375rem', background: 'var(--color-bg-page)', borderRadius: 'var(--radius-sm)', fontSize: '0.75rem' }}>
                    <span style={{ fontWeight: 600 }}>{c.user_name}</span>
                    <span style={{ color: 'var(--color-text-muted)', marginLeft: '0.5rem' }}>{c.action}</span>
                    <p style={{ color: 'var(--color-text-secondary)', marginTop: '0.25rem' }}>{c.comment}</p>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>

      {/* ── Order Details Modal ── */}
      {showOrderModal && orderDetails && (
        <div
          style={{
            position: 'fixed', inset: 0, zIndex: 1000,
            background: 'rgba(0,0,0,0.5)', backdropFilter: 'blur(4px)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            animation: 'fadeIn 0.2s ease',
          }}
          onClick={() => setShowOrderModal(false)}
        >
          <div
            style={{
              background: 'var(--color-bg-card)', borderRadius: '16px',
              width: '95%', maxWidth: 720, maxHeight: '90vh', overflow: 'auto',
              boxShadow: '0 25px 60px -12px rgba(0,0,0,0.25)',
              animation: 'slideUp 0.25s ease',
            }}
            onClick={(e) => e.stopPropagation()}
          >
            {/* Modal Header */}
            <div style={{
              display: 'flex', justifyContent: 'space-between', alignItems: 'center',
              padding: '1.25rem 1.5rem', borderBottom: '1px solid var(--color-border)',
              position: 'sticky', top: 0, background: 'var(--color-bg-card)', zIndex: 2, borderRadius: '16px 16px 0 0',
            }}>
              <div>
                <h3 style={{ fontSize: '1.125rem', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <FileText size={20} color="var(--color-primary)" />
                  Order #{orderDetails.order_id}
                </h3>
                <p style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)', marginTop: '0.125rem' }}>
                  Historical data from analytical database
                </p>
              </div>
              <button onClick={() => setShowOrderModal(false)} style={{ background: 'none', border: 'none', cursor: 'pointer', padding: '0.5rem', borderRadius: '8px', color: 'var(--color-text-muted)' }}>
                <X size={20} />
              </button>
            </div>

            {/* Modal Body */}
            <div style={{ padding: '1.5rem' }}>

              {/* Risk banner */}
              <div style={{
                padding: '0.875rem 1rem', marginBottom: '1.25rem', borderRadius: '10px',
                background: riskBg(orderDetails.risk_level),
                border: `1px solid ${riskColor(orderDetails.risk_level)}22`,
                display: 'flex', justifyContent: 'space-between', alignItems: 'center',
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <AlertCircle size={18} color={riskColor(orderDetails.risk_level)} />
                  <span style={{ fontSize: '0.8125rem', fontWeight: 600, color: riskColor(orderDetails.risk_level) }}>
                    {orderDetails.anomaly_type?.replace(/_/g, ' ')}
                  </span>
                </div>
                <span style={{ fontSize: '0.8125rem', fontWeight: 700, color: riskColor(orderDetails.risk_level) }}>
                  Score: {(orderDetails.anomaly_score * 100).toFixed(1)}%
                </span>
              </div>

              {/* Sections grid */}
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.25rem' }}>

                {/* ── Transaction Info ── */}
                <div>
                  <div style={{ fontSize: '0.6875rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--color-text-muted)', marginBottom: '0.5rem' }}>
                    📋 Order Information
                  </div>
                  <div style={{ background: 'var(--color-bg-page)', borderRadius: '10px', padding: '0.75rem' }}>
                    <DetailRow icon={<Hash size={12} />} label="Order No." value={`#${orderDetails.order_id}`} />
                    <DetailRow icon={<Clock size={12} />} label="Date & Time" value={orderDetails.order_datetime} />
                    <DetailRow icon={<CreditCard size={12} />} label="Payment" value={orderDetails.payment_method} />
                    <DetailRow label="Table" value={orderDetails.table_number != null ? `Table ${Math.round(orderDetails.table_number)}` : 'Takeaway'} />
                    <DetailRow label="Section" value={orderDetails.restaurant_type} />
                    <DetailRow label="Main category" value={orderDetails.main_category} />
                    <DetailRow label="Weekend" value={orderDetails.is_weekend ? 'Oui' : 'No'} />
                    <DetailRow label="Shift" value={orderDetails.cashier_shift} />
                  </div>
                </div>

                {/* ── Financial ── */}
                <div>
                  <div style={{ fontSize: '0.6875rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--color-text-muted)', marginBottom: '0.5rem' }}>
                    💰 Amounts & Prices
                  </div>
                  <div style={{ background: 'var(--color-bg-page)', borderRadius: '10px', padding: '0.75rem' }}>
                    <DetailRow label="Total amount" value={<span style={{ color: 'var(--color-primary)', fontWeight: 700, fontSize: '0.9375rem' }}>{fmt(orderDetails.total_amount)} DT</span>} />
                    <DetailRow label="Avg price / item" value={`${fmt(orderDetails.avg_item_price)} DT`} />
                    <DetailRow label="Max price" value={`${fmt(orderDetails.max_item_price)} DT`} />
                    <DetailRow label="Min price" value={`${fmt(orderDetails.min_item_price)} DT`} />
                    <DetailRow label="Max line total" value={`${fmt(orderDetails.max_line_total)} DT`} />
                    <DetailRow label="Min line total" value={`${fmt(orderDetails.min_line_total)} DT`} />
                    <DetailRow label="Avg price deviation" value={`${fmt(orderDetails.mean_price_deviation_pct)}%`} />
                  </div>
                </div>

                {/* ── Basket ── */}
                <div>
                  <div style={{ fontSize: '0.6875rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--color-text-muted)', marginBottom: '0.5rem' }}>
                    🛒 Basket
                  </div>
                  <div style={{ background: 'var(--color-bg-page)', borderRadius: '10px', padding: '0.75rem' }}>
                    <DetailRow icon={<ShoppingBag size={12} />} label="Basket size" value={<span style={{ fontWeight: 700, color: '#6366f1' }}>{orderDetails.basket_size} items</span>} />
                    <DetailRow label="Unique items" value={orderDetails.n_unique_items} />
                    <DetailRow label="Unique categories" value={orderDetails.n_unique_categories} />
                    <DetailRow label="Unique items ratio" value={fmtPct(orderDetails.unique_item_ratio)} />
                    <DetailRow label="Avg amount / item" value={`${fmt(orderDetails.avg_amount_per_item)} DT`} />
                  </div>
                </div>

                {/* ── Discount & Voids ── */}
                <div>
                  <div style={{ fontSize: '0.6875rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--color-text-muted)', marginBottom: '0.5rem' }}>
                    🏷️ Discounts & Voids
                  </div>
                  <div style={{ background: 'var(--color-bg-page)', borderRadius: '10px', padding: '0.75rem' }}>
                    <DetailRow icon={<Percent size={12} />} label="Discount applied" value={orderDetails.has_discount ? 'Oui' : 'No'} />
                    <DetailRow label="Avg discount rate" value={fmtPct(orderDetails.mean_discount_rate)} />
                    <DetailRow label="Max discount rate" value={fmtPct(orderDetails.max_discount_rate)} />
                    <DetailRow label="Discounted lines" value={orderDetails.discount_line_count} />
                    <DetailRow label="Est. discount amount" value={`${fmt(orderDetails.estimated_discount_amount)} DT`} />
                    <DetailRow icon={<TrendingDown size={12} />} label="Voided order" value={orderDetails.is_voided_order ? '⚠️ Oui' : 'No'} />
                    <DetailRow label="Voided lines" value={orderDetails.void_line_count} />
                  </div>
                </div>

                {/* ── Cashier Stats ── */}
                <div>
                  <div style={{ fontSize: '0.6875rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--color-text-muted)', marginBottom: '0.5rem' }}>
                    👤 Cashier Profile ({orderDetails.cashier_id})
                  </div>
                  <div style={{ background: 'var(--color-bg-page)', borderRadius: '10px', padding: '0.75rem' }}>
                    <DetailRow icon={<User size={12} />} label="Total orders" value={orderDetails.cashier_total_orders?.toLocaleString()} />
                    <DetailRow label="Avg amount" value={`${fmt(orderDetails.cashier_avg_order_amount)} DT`} />
                    <DetailRow label="Void rate" value={fmtPct(orderDetails.cashier_void_rate)} />
                    <DetailRow label="Discount rate" value={fmtPct(orderDetails.cashier_discount_order_rate)} />
                    <DetailRow label="Amount Z-Score" value={
                      <span style={{ color: Math.abs(orderDetails.cashier_amount_zscore || 0) > 3 ? '#ef4444' : 'var(--color-text-primary)', fontWeight: Math.abs(orderDetails.cashier_amount_zscore || 0) > 3 ? 700 : 600 }}>
                        {fmt(orderDetails.cashier_amount_zscore)} {Math.abs(orderDetails.cashier_amount_zscore || 0) > 3 ? '⚠️' : ''}
                      </span>
                    } />
                    <DetailRow label="Flagged" value={orderDetails.cashier_flagged ? '🚩 Oui' : 'No'} />
                  </div>
                </div>

                {/* ── Customer Stats ── */}
                <div>
                  <div style={{ fontSize: '0.6875rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--color-text-muted)', marginBottom: '0.5rem' }}>
                    🧑 Customer Profile ({orderDetails.customer_id || 'Anonymous'})
                  </div>
                  <div style={{ background: 'var(--color-bg-page)', borderRadius: '10px', padding: '0.75rem' }}>
                    <DetailRow label="Total orders" value={orderDetails.customer_total_orders?.toLocaleString()} />
                    <DetailRow label="Avg amount" value={`${fmt(orderDetails.customer_avg_order_amount)} DT`} />
                    <DetailRow label="Avg basket size" value={`${fmt(orderDetails.customer_avg_basket_size)} items`} />
                    <DetailRow label="Amount Z-Score" value={fmt(orderDetails.customer_amount_zscore)} />
                    <DetailRow label="Archetype" value={orderDetails.archetype || '—'} />
                    <DetailRow label="Price tier" value={orderDetails.price_tier || '—'} />
                  </div>
                </div>

              </div>

              {/* Description */}
              {orderDetails.anomaly_description && (
                <div style={{ marginTop: '1.25rem', padding: '0.875rem', background: 'rgba(239,68,68,0.06)', borderRadius: '10px', border: '1px solid rgba(239,68,68,0.15)' }}>
                  <div style={{ fontSize: '0.6875rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.05em', color: '#ef4444', marginBottom: '0.25rem' }}>
                    🔍 Anomaly description
                  </div>
                  <p style={{ fontSize: '0.8125rem', color: 'var(--color-text-secondary)', lineHeight: 1.6 }}>
                    {orderDetails.anomaly_description}
                  </p>
                </div>
              )}

            </div>
          </div>
        </div>
      )}

      <style>{`
        @keyframes fadeIn { from { opacity: 0 } to { opacity: 1 } }
        @keyframes slideUp { from { opacity: 0; transform: translateY(20px) } to { opacity: 1; transform: translateY(0) } }
      `}</style>
    </div>
  );
}
