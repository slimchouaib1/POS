import { useCallback, useEffect, useState } from 'react';
import api from '../api';
import {
  DollarSign, AlertTriangle, AlertOctagon, FileText,
  TrendingUp, Sparkles, Package, ArrowUp, ArrowDown, ShoppingCart, CheckCircle2
} from 'lucide-react';

interface TopConsumed {
  name: string;
  amount: string;
}

interface IngredientForecast {
  ingredient_id: number;
  ingredient_name: string;
  unit: string;
  current_stock: number;
  predicted_consumption: number;
  shortage: number;
  status: string;
  top_consumers: string[];
}

interface PurchaseOrder {
  id: number;
  ingredient_id: number;
  ingredient_name: string;
  unit: string;
  quantity_ordered: number;
  status: 'pending' | 'received' | 'cancelled';
  created_at: string | null;
  received_at: string | null;
  created_by_name: string;
}

export default function StockDashboardPage() {
  const [ingredientForecasts, setIngredientForecasts] = useState<IngredientForecast[]>([]);
  const [pendingPurchaseOrders, setPendingPurchaseOrders] = useState<PurchaseOrder[]>([]);
  const [loading, setLoading] = useState(true);
  const [poProcessing, setPoProcessing] = useState(false);
  const [receivingPoId, setReceivingPoId] = useState<number | null>(null);
  const [poMessage, setPoMessage] = useState('');

  const fetchForecasts = useCallback(() => {
    setLoading(true);
    api.get('/api/ai/forecasting/ingredient-forecast')
      .then(res => setIngredientForecasts(res.data))
      .catch(err => console.error(err))
      .finally(() => setLoading(false));
  }, []);

  const fetchPendingPurchaseOrders = useCallback(() => {
    api.get('/api/stock/purchase-orders?status=pending')
      .then(res => setPendingPurchaseOrders(res.data))
      .catch(err => console.error(err));
  }, []);

  const refreshDashboard = useCallback(() => {
    fetchForecasts();
    fetchPendingPurchaseOrders();
  }, [fetchForecasts, fetchPendingPurchaseOrders]);

  useEffect(() => {
    refreshDashboard();
  }, [refreshDashboard]);

  const handleCreatePO = async () => {
    const shortages = ingredientForecasts.filter(f => f.shortage > 0);
    if (shortages.length === 0) {
      setPoMessage('All ingredients are optimally stocked. No purchase order is needed.');
      return;
    }

    const pendingIngredientIds = new Set(pendingPurchaseOrders.map(po => po.ingredient_id));
    const shortagesWithoutPendingPo = shortages.filter(f => !pendingIngredientIds.has(f.ingredient_id));
    if (shortagesWithoutPendingPo.length === 0) {
      setPoMessage('Every current shortage already has a pending purchase order.');
      return;
    }
    
    setPoProcessing(true);
    setPoMessage('');
    try {
      await Promise.all(shortagesWithoutPendingPo.map(f => api.post('/api/stock/purchase-orders', {
        ingredient_id: f.ingredient_id,
        quantity_ordered: f.shortage,
      })));
      setPoMessage(`Created ${shortagesWithoutPendingPo.length} pending purchase order${shortagesWithoutPendingPo.length === 1 ? '' : 's'}.`);
      refreshDashboard();
    } catch (e: any) {
      console.error(e);
      setPoMessage(e.response?.data?.detail || 'Error creating purchase order.');
    } finally {
      setPoProcessing(false);
    }
  };

  const handleReceivePO = async (purchaseOrderId: number) => {
    setReceivingPoId(purchaseOrderId);
    setPoMessage('');
    try {
      await api.post(`/api/stock/purchase-orders/${purchaseOrderId}/receive`);
      setPoMessage(`Purchase order #${purchaseOrderId} received and stock updated.`);
      refreshDashboard();
    } catch (e: any) {
      console.error(e);
      setPoMessage(e.response?.data?.detail || 'Error receiving purchase order.');
    } finally {
      setReceivingPoId(null);
    }
  };

  const [topConsumed] = useState<TopConsumed[]>([
    { name: 'Organic Tomatoes', amount: '45 kg' },
    { name: 'Fresh Basil', amount: '38 bunches' },
    { name: 'Mozzarella Cheese', amount: '22 kg' },
  ]);

  const usageTrend = [
    { day: 'Mon', value: 42 }, { day: 'Tue', value: 48 }, { day: 'Wed', value: 45 },
    { day: 'Thu', value: 65 }, { day: 'Fri', value: 78 }, { day: 'Sat', value: 92 },
    { day: 'Sun', value: 58 },
  ];
  const maxUsage = Math.max(...usageTrend.map(u => u.value));

  const kpis = [
    { label: 'Total Inventory Value', value: '14,455.75 DT', change: '+5.2%', up: true, icon: <DollarSign size={18} />, bg: '#E8F5E9', color: '#28A745' },
    { label: 'Low Stock Ingredients', value: ingredientForecasts.filter(f => f.status === 'LOW').length.toString(), change: null, up: false, icon: <AlertTriangle size={18} />, bg: '#FFF8E1', color: '#FFC107' },
    { label: 'Critical Ingredients', value: ingredientForecasts.filter(f => f.status === 'CRITICAL').length.toString(), change: null, up: false, icon: <AlertOctagon size={18} />, bg: '#FFEBEE', color: '#DC3545' },
    { label: 'Pending Purchase Orders', value: pendingPurchaseOrders.length.toString(), change: null, up: false, icon: <FileText size={18} />, bg: '#E8F5E9', color: '#28A745' },
  ];

  return (
    <div className="animate-fadeIn">
      <div className="page-header">
        <h2>Stock Dashboard</h2>
        <p>Monitor raw ingredient health and supplier activity driven by AI Sales Forecasts</p>
      </div>

      {/* KPI Grid */}
      <div className="grid-4" style={{ marginBottom: '1.5rem' }}>
        {kpis.map((k, i) => (
          <div key={i} className="kpi-card">
            <div>
              <div className="kpi-value">{k.value}</div>
              <div className="kpi-label" style={{ marginTop: '0.25rem' }}>{k.label}</div>
              {k.change && (
                <div className={`kpi-change ${k.up ? 'up' : 'down'}`}>
                  {k.up ? <ArrowUp size={12} /> : <ArrowDown size={12} />}
                  {k.change}
                </div>
              )}
            </div>
            <div className="kpi-icon" style={{ background: k.bg, color: k.color }}>{k.icon}</div>
          </div>
        ))}
      </div>

      {/* Stock Alerts + Top Consumed */}
      <div className="grid-2" style={{ gridTemplateColumns: '2fr 1fr', marginBottom: '1.5rem' }}>
        <div className="card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
            <div>
              <h3 style={{ fontSize: '1.125rem', fontWeight: 700 }}>AI Ingredient Forecast (Next Week)</h3>
              <p style={{ fontSize: '0.8125rem', color: 'var(--color-text-secondary)' }}>Bridging LightGBM Menu Sales to Raw Ingredients</p>
            </div>
            <button 
              className="btn btn-primary btn-sm" 
              onClick={handleCreatePO} 
              disabled={poProcessing || loading}
            >
              <ShoppingCart size={16} style={{ marginRight: '0.5rem' }} />
              {poProcessing ? 'Processing...' : 'Create Purchase Order'}
            </button>
          </div>

          {loading ? (
            <p>Loading ingredient predictions...</p>
          ) : ingredientForecasts.slice(0, 8).map((f, i) => (
            <div key={i} className="stock-alert-item" style={{ borderLeft: f.shortage > 0 ? (f.status === 'CRITICAL' ? '4px solid var(--color-danger)' : '4px solid var(--color-warning)') : '4px solid var(--color-success)' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                <Package size={18} style={{ color: 'var(--color-text-muted)' }} />
                <div>
                  <div className="alert-name">{f.ingredient_name}</div>
                  <div className="alert-detail">Current Stock: {f.current_stock}{f.unit} &bull; Predicted Usage: {f.predicted_consumption}{f.unit}</div>
                  <div style={{ fontSize: '0.7rem', color: 'var(--color-text-muted)', marginTop: '0.2rem' }}>
                    Top Consumers: {f.top_consumers.slice(0, 2).join(', ')}
                  </div>
                </div>
              </div>
              <span className={`badge ${f.shortage > 0 ? (f.status === 'CRITICAL' ? 'badge-danger' : 'badge-warning') : 'badge-success'}`}>
                {f.shortage > 0 ? `${f.status}: Short ${f.shortage}${f.unit}` : 'Optimal'}
              </span>
            </div>
          ))}

          {poMessage && (
            <div style={{ marginTop: '1rem', fontSize: '0.8125rem', color: 'var(--color-text-secondary)' }}>
              {poMessage}
            </div>
          )}
        </div>

        <div className="card">
          <h3 style={{ fontSize: '1.125rem', fontWeight: 700, marginBottom: '1rem' }}>Top Consumed Items</h3>
          {topConsumed.map((item, i) => (
            <div key={i} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '0.75rem 0', borderBottom: i < topConsumed.length - 1 ? '1px solid var(--color-border-light)' : 'none' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <span style={{ color: 'var(--color-success)', fontWeight: 700, fontSize: '0.875rem' }}>{i + 1}</span>
                <span style={{ fontWeight: 500, fontSize: '0.875rem' }}>{item.name}</span>
              </div>
              <span style={{ fontWeight: 600, fontSize: '0.875rem' }}>{item.amount}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Pending Purchase Orders */}
      <div className="card" style={{ marginBottom: '1.5rem', padding: 0, overflow: 'hidden' }}>
        <div style={{ padding: '1.25rem 1.5rem', borderBottom: '1px solid var(--color-border)' }}>
          <h3 style={{ fontSize: '1.125rem', fontWeight: 700 }}>Pending Purchase Orders</h3>
          <p style={{ fontSize: '0.8125rem', color: 'var(--color-text-secondary)' }}>Receive deliveries to increase ingredient stock.</p>
        </div>
        <table className="data-table">
          <thead>
            <tr>
              <th>#</th>
              <th>Ingredient</th>
              <th>Quantity</th>
              <th>Created By</th>
              <th>Created</th>
              <th>Status</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            {pendingPurchaseOrders.length > 0 ? pendingPurchaseOrders.map((po) => (
              <tr key={po.id}>
                <td style={{ fontWeight: 700 }}>PO-{po.id.toString().padStart(3, '0')}</td>
                <td style={{ fontWeight: 600 }}>{po.ingredient_name}</td>
                <td>{po.quantity_ordered.toLocaleString()} {po.unit}</td>
                <td>{po.created_by_name || 'System'}</td>
                <td>{po.created_at ? new Date(po.created_at).toLocaleString() : ''}</td>
                <td><span className="badge badge-warning">Pending</span></td>
                <td>
                  <button
                    className="btn btn-sm btn-primary"
                    onClick={() => handleReceivePO(po.id)}
                    disabled={receivingPoId === po.id}
                  >
                    <CheckCircle2 size={14} />
                    {receivingPoId === po.id ? 'Receiving...' : 'Mark Received'}
                  </button>
                </td>
              </tr>
            )) : (
              <tr>
                <td colSpan={7} style={{ textAlign: 'center', padding: '2rem', color: 'var(--color-text-muted)' }}>
                  No pending purchase orders.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {/* Stock Usage Trend */}
      <div className="card" style={{ marginBottom: '1.5rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
          <div>
            <h3 style={{ fontSize: '1.125rem', fontWeight: 700 }}>Stock Usage Trend</h3>
            <p style={{ fontSize: '0.8125rem', color: 'var(--color-text-secondary)' }}>Last 7 days consumption pattern</p>
          </div>
          <div className="kpi-change up" style={{ fontSize: '0.8125rem' }}>
            <TrendingUp size={14} /> +12.5% vs last week
          </div>
        </div>
        <div style={{ display: 'flex', alignItems: 'flex-end', gap: '0.75rem', height: 200, paddingTop: '1rem' }}>
          {usageTrend.map((d, i) => (
            <div key={i} style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '0.5rem' }}>
              <div style={{
                width: '100%',
                height: `${(d.value / maxUsage) * 170}px`,
                background: d.value > maxUsage * 0.75 ? '#DC3545' : '#F4845F',
                borderRadius: '6px 6px 0 0',
                transition: 'height 0.3s ease',
              }} />
              <span style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)' }}>{d.day}</span>
            </div>
          ))}
        </div>
      </div>

      {/* AI Recommendation Banner */}
      <div className="ai-insight-banner">
        <Sparkles size={22} />
        <div>
          <span className="ai-badge">AI Recommendation</span> <span style={{ fontSize: '0.625rem', background: 'rgba(255,255,255,0.3)', padding: '0.1rem 0.4rem', borderRadius: 3 }}>LightGBM + Recipe Engine</span>
          <p style={{ marginTop: '0.25rem' }}>
            {ingredientForecasts.filter(f => f.shortage > 0).length > 0 
              ? `Based on next week's menu sales predictions, ${ingredientForecasts.filter(f => f.shortage > 0).length} ingredients will run out. Reorder ${ingredientForecasts.filter(f => f.shortage > 0).map(f => `**${f.ingredient_name}**`).slice(0, 3).join(', ')} immediately.`
              : `All ingredients are optimally stocked for the predicted sales of the upcoming week.`}
          </p>
        </div>
      </div>
    </div>
  );
}
