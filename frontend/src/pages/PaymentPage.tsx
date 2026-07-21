import { useState, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import api from '../api';
import { ArrowLeft, Banknote, CreditCard, GitBranch, RotateCcw, Check } from 'lucide-react';

export default function PaymentPage() {
  const location = useLocation();
  const navigate = useNavigate();
  const { order, cart, subtotal, tax, total } = location.state || {};
  const [method, setMethod] = useState('cash');
  const [processing, setProcessing] = useState(false);
  const [payments, setPayments] = useState<any[]>([]);
  const [splitWays, setSplitWays] = useState(2);

  useEffect(() => {
    if (order?.id) {
      api.get(`/api/payments/${order.id}`).then((r) => setPayments(r.data));
    }
  }, [order?.id]);

  const paidAmount = payments.filter(p => p.status === 'completed').reduce((sum, p) => sum + p.amount, 0);
  const remainingAmount = Math.max(0, total - paidAmount);

  if (!order) {
    return (
      <div style={{ padding: '3rem', textAlign: 'center', color: 'var(--color-text-muted)' }}>
        No order data. <a href="/pos" style={{ color: 'var(--color-primary)' }}>Go back to POS</a>
      </div>
    );
  }

  const handleConfirm = async () => {
    if (remainingAmount <= 0) return;
    setProcessing(true);
    const amountToPay = method === 'split' ? (remainingAmount / splitWays) : remainingAmount;
    try {
      await api.post('/api/payments', {
        order_id: order.id,
        amount: amountToPay,
        method: method === 'split' ? 'cash' : method,
      });
      
      const newPaid = paidAmount + amountToPay;
      if (total - newPaid <= 0.01) {
        navigate('/pos/receipt', { state: { order, cart, subtotal, tax, total, method } });
      } else {
        const r = await api.get(`/api/payments/${order.id}`);
        setPayments(r.data);
        if (method === 'split') setSplitWays(Math.max(2, splitWays - 1));
      }
    } catch (err: any) {
      alert(`Payment failed: ${err.response?.data?.detail || 'Error'}`);
    }
    setProcessing(false);
  };

  const methods = [
    { id: 'cash', name: 'Cash', desc: 'Accept cash payment', icon: <Banknote size={24} />, bg: '#F5F0EB' },
    { id: 'card', name: 'Card', desc: 'Credit or Debit Card', icon: <CreditCard size={24} />, bg: '#FFF3E0' },
    { id: 'split', name: 'Split Bill', desc: 'Split payment', icon: <GitBranch size={24} />, bg: '#F5F0EB' },
    { id: 'refund', name: 'Refund', desc: 'Process refund', icon: <RotateCcw size={24} />, bg: '#FFEBEE' },
  ];

  return (
    <div className="animate-fadeIn" style={{ maxWidth: 1100, margin: '0 auto', padding: '2rem' }}>
      {/* Header */}
      <div style={{ marginBottom: '1.5rem' }}>
        <button onClick={() => navigate('/pos')} className="btn btn-ghost btn-sm" style={{ marginBottom: '0.5rem' }}>
          <ArrowLeft size={14} /> Back to Order
        </button>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <h2 style={{ fontSize: '1.5rem', fontWeight: 700 }}>Payment Processing</h2>
            <p style={{ color: 'var(--color-text-secondary)', fontSize: '0.875rem' }}>
              Order #{order.id} &bull; Table T{order.table_number || '—'}
            </p>
          </div>
          <div style={{ textAlign: 'right' }}>
            <div style={{ fontSize: '0.875rem', color: 'var(--color-text-secondary)' }}>Remaining Balance</div>
            <div style={{ fontSize: '1.75rem', fontWeight: 700, color: 'var(--color-primary)' }}>{remainingAmount.toFixed(2)} DT</div>
          </div>
        </div>
      </div>

      {/* Blue divider */}
      <div style={{ height: 3, background: 'var(--color-primary)', borderRadius: 2, marginBottom: '2rem' }} />

      <div className="grid-2" style={{ gap: '2rem' }}>
        {/* Left: Order Summary */}
        <div className="card">
          <h3 style={{ fontSize: '1.125rem', fontWeight: 700, marginBottom: '1.25rem' }}>Order Summary</h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
            {cart?.map((item: any, i: number) => (
              <div key={i} style={{ display: 'flex', justifyContent: 'space-between' }}>
                <div>
                  <div style={{ fontWeight: 600 }}>{item.product.name}</div>
                  <div style={{ fontSize: '0.8125rem', color: 'var(--color-text-muted)' }}>
                    {item.quantity} x {item.product.price.toFixed(2)} DT
                  </div>
                </div>
                <div style={{ fontWeight: 600 }}>{(item.product.price * item.quantity).toFixed(2)} DT</div>
              </div>
            ))}
          </div>

          <hr style={{ border: 'none', borderTop: '1px solid var(--color-border)', margin: '1.25rem 0' }} />

          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.375rem', fontSize: '0.875rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: 'var(--color-text-secondary)' }}>Subtotal</span>
              <span>{subtotal?.toFixed(2)} DT</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: 'var(--color-text-secondary)' }}>Tax (10%)</span>
              <span>{tax?.toFixed(2)} DT</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '1.125rem', fontWeight: 700, marginTop: '0.5rem' }}>
              <span>Total</span>
              <span>{total?.toFixed(2)} DT</span>
            </div>
            {paidAmount > 0 && (
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '1rem', fontWeight: 600, marginTop: '0.5rem', color: 'var(--color-success)' }}>
                <span>Paid</span>
                <span>-{paidAmount.toFixed(2)} DT</span>
              </div>
            )}
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '1.25rem', fontWeight: 700, marginTop: '0.5rem', color: 'var(--color-primary)' }}>
              <span>Remaining</span>
              <span>{remainingAmount.toFixed(2)} DT</span>
            </div>
          </div>
        </div>

        {/* Right: Payment Methods */}
        <div>
          <div className="card" style={{ marginBottom: '1.5rem' }}>
            <h3 style={{ fontSize: '1.125rem', fontWeight: 700, marginBottom: '1.25rem' }}>Select Payment Method</h3>
            <div className="payment-method-grid">
              {methods.map((m) => (
                <div
                  key={m.id}
                  className={`payment-method-card ${method === m.id ? 'active' : ''}`}
                  onClick={() => setMethod(m.id)}
                >
                  <div className="method-icon" style={{ background: method === m.id ? 'var(--color-primary)' : m.bg, color: method === m.id ? 'white' : 'var(--color-text-primary)' }}>
                    {m.icon}
                  </div>
                  <div className="method-name">{m.name}</div>
                  <div className="method-desc">{m.desc}</div>
                </div>
              ))}
            </div>
          </div>

          {method === 'card' && (
            <div className="card" style={{ textAlign: 'center', padding: '2rem', marginBottom: '1.5rem' }}>
              <h3 style={{ fontSize: '1.125rem', fontWeight: 700, marginBottom: '1rem' }}>Card Payment</h3>
              <CreditCard size={48} style={{ color: 'var(--color-primary)', margin: '0 auto 1rem' }} />
              <p style={{ color: 'var(--color-text-secondary)', fontSize: '0.875rem' }}>
                Swipe, insert, or tap card when ready
              </p>
            </div>
          )}
          
          {method === 'split' && (
            <div className="card" style={{ textAlign: 'center', padding: '2rem', marginBottom: '1.5rem' }}>
              <h3 style={{ fontSize: '1.125rem', fontWeight: 700, marginBottom: '1rem' }}>Split Bill</h3>
              <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', gap: '1.5rem', marginBottom: '1rem' }}>
                <button className="btn btn-outline" style={{ width: 40, height: 40, padding: 0 }} onClick={() => setSplitWays(Math.max(2, splitWays - 1))}>-</button>
                <span style={{ fontSize: '1.25rem', fontWeight: 600 }}>{splitWays} ways</span>
                <button className="btn btn-outline" style={{ width: 40, height: 40, padding: 0 }} onClick={() => setSplitWays(splitWays + 1)}>+</button>
              </div>
              <p style={{ color: 'var(--color-primary)', fontSize: '1.5rem', fontWeight: 700 }}>
                {(remainingAmount / splitWays).toFixed(2)} DT <span style={{ fontSize: '1rem', fontWeight: 500, color: 'var(--color-text-secondary)' }}>per person</span>
              </p>
            </div>
          )}

          <button
            className="btn btn-primary btn-lg"
            style={{ width: '100%', marginTop: '1.5rem', padding: '1rem' }}
            onClick={handleConfirm}
            disabled={processing || remainingAmount <= 0}
          >
            <Check size={18} /> {processing ? 'Processing...' : method === 'split' ? `Pay ${(remainingAmount / splitWays).toFixed(2)} DT` : `Pay ${remainingAmount.toFixed(2)} DT`}
          </button>
        </div>
      </div>
    </div>
  );
}
