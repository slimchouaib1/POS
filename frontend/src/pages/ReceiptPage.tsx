import { useLocation, useNavigate } from 'react-router-dom';
import { ArrowLeft, Printer, Download, Mail, CheckCircle, ChefHat } from 'lucide-react';

export default function ReceiptPage() {
  const location = useLocation();
  const navigate = useNavigate();
  const { order, cart, subtotal, tax, total, method } = location.state || {};

  if (!order) {
    return (
      <div style={{ padding: '3rem', textAlign: 'center', color: 'var(--color-text-muted)' }}>
        No receipt data. <a href="/pos" style={{ color: 'var(--color-primary)' }}>Go back to POS</a>
      </div>
    );
  }

  const methodLabels: Record<string, string> = {
    cash: 'Cash', card: 'Credit Card', split: 'Split Bill', refund: 'Refund',
  };

  return (
    <div className="animate-fadeIn" style={{ maxWidth: 700, margin: '0 auto', padding: '2rem' }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <CheckCircle size={28} color="var(--color-success)" />
          <div>
            <h2 style={{ fontSize: '1.5rem', fontWeight: 700 }}>Payment Successful</h2>
            <p style={{ fontSize: '0.875rem', color: 'var(--color-text-secondary)' }}>
              Order #{order.id} has been paid and completed
            </p>
          </div>
        </div>
        <div style={{ display: 'flex', gap: '0.5rem' }}>
          <button className="btn btn-outline btn-sm"><Printer size={14} /> Print</button>
          <button className="btn btn-outline btn-sm"><Download size={14} /> Download PDF</button>
          <button className="btn btn-primary btn-sm"><Mail size={14} /> Email Receipt</button>
        </div>
      </div>

      {/* Receipt */}
      <div className="receipt-container">
        <div style={{ textAlign: 'center', marginBottom: '1.5rem' }}>
          <div style={{ width: 48, height: 48, borderRadius: 12, background: 'var(--color-primary)', display: 'inline-flex', alignItems: 'center', justifyContent: 'center', marginBottom: '0.75rem' }}>
            <ChefHat size={24} color="white" />
          </div>
          <h3 style={{ fontSize: '1.25rem', fontWeight: 700 }}>RestaurantPOS</h3>
          <p style={{ fontSize: '0.8125rem', color: 'var(--color-text-muted)', lineHeight: 1.6 }}>
            123 Main Street, Suite 100<br />
            Tunis, Tunisia<br />
            Tel: +216 71 234 567<br />
            www.restaurantpos.tn
          </p>
        </div>

        <hr className="receipt-divider" />

        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.375rem', fontSize: '0.875rem', marginBottom: '1rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            <span style={{ color: 'var(--color-text-secondary)' }}>Order Number:</span>
            <span style={{ fontWeight: 600 }}>#{order.id}</span>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            <span style={{ color: 'var(--color-text-secondary)' }}>Date & Time:</span>
            <span style={{ fontWeight: 600 }}>{new Date().toLocaleString('en-US')}</span>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            <span style={{ color: 'var(--color-text-secondary)' }}>Table:</span>
            <span style={{ fontWeight: 600 }}>T{order.table_number || '—'}</span>
          </div>
        </div>

        <hr className="receipt-divider" />

        <div style={{ marginBottom: '1rem' }}>
          <h4 style={{ fontWeight: 700, marginBottom: '0.75rem' }}>Order Items</h4>
          {cart?.map((item: any, i: number) => (
            <div key={i} style={{ display: 'flex', justifyContent: 'space-between', padding: '0.375rem 0', fontSize: '0.875rem' }}>
              <div>
                <div style={{ fontWeight: 600 }}>{item.product.name}</div>
                <div style={{ color: 'var(--color-text-muted)', fontSize: '0.8125rem' }}>{item.quantity} x {item.product.price.toFixed(2)} DT</div>
              </div>
              <div style={{ fontWeight: 600 }}>{(item.product.price * item.quantity).toFixed(2)} DT</div>
            </div>
          ))}
        </div>

        <hr className="receipt-divider" />

        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.375rem', fontSize: '0.875rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            <span style={{ color: 'var(--color-text-secondary)' }}>Subtotal</span>
            <span>{subtotal?.toFixed(2)} DT</span>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            <span style={{ color: 'var(--color-text-secondary)' }}>Tax (10%)</span>
            <span>{tax?.toFixed(2)} DT</span>
          </div>
        </div>

        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '1.25rem', fontWeight: 700, marginTop: '0.75rem', paddingTop: '0.75rem', borderTop: '2px solid var(--color-text-primary)' }}>
          <span>TOTAL</span>
          <span style={{ color: 'var(--color-primary)' }}>{total?.toFixed(2)} DT</span>
        </div>

        <div style={{ marginTop: '0.75rem', padding: '0.5rem 0.75rem', border: '1px solid var(--color-border)', borderRadius: 'var(--radius-sm)', display: 'flex', justifyContent: 'space-between', fontSize: '0.875rem' }}>
          <span style={{ color: 'var(--color-text-secondary)' }}>Payment Method</span>
          <span style={{ fontWeight: 600 }}>{methodLabels[method] || method}</span>
        </div>

        <div style={{ textAlign: 'center', marginTop: '1.5rem', fontSize: '0.875rem', color: 'var(--color-text-secondary)' }}>
          <p style={{ fontWeight: 600 }}>Thank you for dining with us!</p>
          <p>Please visit us again soon.</p>
        </div>
      </div>

      <button className="btn btn-primary btn-lg" style={{ width: '100%', marginTop: '1.5rem' }} onClick={() => navigate('/pos')}>
        <ArrowLeft size={16} /> Back to Dashboard
      </button>
    </div>
  );
}
