import { useEffect, useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../api';
import { useAuth } from '../AuthContext';
import type { Product, Category, CartItem, TableItem, Recommendation } from '../types';
import {
  ShoppingCart, Plus, Trash2, Search, Grid3X3, Zap,
  Clock, Users, ChefHat, CreditCard, Save, Sparkles, Image, LogOut
} from 'lucide-react';
import CustomSelect from '../components/CustomSelect';

export default function POSPage() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const [mode, setMode] = useState<'tables' | 'menu'>('tables');
  const [products, setProducts] = useState<Product[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [tables, setTables] = useState<TableItem[]>([]);
  const [cart, setCart] = useState<CartItem[]>([]);
  const [selectedCat, setSelectedCat] = useState<number | null>(null);
  const [search, setSearch] = useState('');
  const [selectedTable, setSelectedTable] = useState<TableItem | null>(null);
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [orderNumber] = useState('ORD-001');
  const [tableFilter, setTableFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [activeOrders, setActiveOrders] = useState<any[]>([]);
  const [tableModalOpen, setTableModalOpen] = useState(false);
  const [tableToReserve, setTableToReserve] = useState<TableItem | null>(null);
  const [reserveCovers, setReserveCovers] = useState(2);
  const [reserveTime, setReserveTime] = useState('');
  const [clearTableConfirmOpen, setClearTableConfirmOpen] = useState(false);

  // Customer State
  const [selectedCustomer, setSelectedCustomer] = useState<any>(null);
  const [customerModalOpen, setCustomerModalOpen] = useState(false);
  const [customerSearch, setCustomerSearch] = useState('');
  const [customersList, setCustomersList] = useState<any[]>([]);
  const [newCustomerName, setNewCustomerName] = useState('');
  const [newCustomerPhone, setNewCustomerPhone] = useState('');
  const [newCustomerEmail, setNewCustomerEmail] = useState('');
  const [isRegistering, setIsRegistering] = useState(false);

  const fetchTables = () => {
    api.get('/api/tables').then((r) => setTables(r.data));
    api.get('/api/orders').then((r) => {
      const active = r.data.filter((o: any) => o.status === 'in_progress' || o.status === 'draft');
      setActiveOrders(active);
    });
  };

  useEffect(() => {
    api.get('/api/products?available_only=true').then((r) => setProducts(r.data));
    api.get('/api/categories').then((r) => setCategories(r.data));
    fetchTables();
  }, []);

  // Fetch AI recommendations when cart or customer changes
  const fetchRecommendations = useCallback(async () => {
    if (cart.length === 0) { setRecommendations([]); return; }
    try {
      const items = cart.map(c => c.product.name);
      const payload: any = { basket_items: items, top_n: 4 };
      if (selectedCustomer) {
        payload.customer_id = selectedCustomer.id;
      }
      const res = await api.post('/api/ai/recommendations', payload);
      setRecommendations(res.data);
    } catch { setRecommendations([]); }
  }, [cart, selectedCustomer]);

  useEffect(() => {
    const timer = setTimeout(fetchRecommendations, 500);
    return () => clearTimeout(timer);
  }, [fetchRecommendations]);

  const filtered = products.filter((p) => {
    if (selectedCat && p.category_id !== selectedCat) return false;
    if (search && !p.name.toLowerCase().includes(search.toLowerCase())) return false;
    return true;
  });

  const addToCart = (product: Product) => {
    setCart((prev) => {
      const existing = prev.find((c) => c.product.id === product.id);
      if (existing) {
        return prev.map((c) => c.product.id === product.id ? { ...c, quantity: c.quantity + 1 } : c);
      }
      return [...prev, { product, quantity: 1, notes: '' }];
    });
  };

  const updateQty = (productId: number, delta: number) => {
    setCart((prev) => prev.map((c) => {
      if (c.product.id === productId) {
        const newQty = c.quantity + delta;
        return newQty > 0 ? { ...c, quantity: newQty } : c;
      }
      return c;
    }).filter(c => c.quantity > 0));
  };

  const removeItem = (productId: number) => {
    setCart((prev) => prev.filter((c) => c.product.id !== productId));
  };

  const subtotal = cart.reduce((sum, c) => sum + c.product.price * c.quantity, 0);
  const tax = subtotal * 0.1;
  const total = subtotal + tax;

  const handleSelectTable = async (table: TableItem) => {
    if (table.status === 'available') {
      setTableToReserve(table);
      setTableModalOpen(true);
    } else {
      const tableOrder = activeOrders.find(o => o.table_id === table.id);
      if (tableOrder && tableOrder.items) {
        const newCart = tableOrder.items.map((item: any) => {
          const product = products.find((p) => p.id === item.product_id) || {
            id: item.product_id,
            name: item.product_name,
            price: item.unit_price,
            category_id: 0,
            stock_quantity: 999,
            is_available: true,
            description: ''
          };
          return { product, quantity: item.quantity, notes: item.notes || '' };
        });
        setCart(newCart);
        if (tableOrder.customer_id) {
          try {
            const cRes = await api.get(`/api/customers/${tableOrder.customer_id}`);
            setSelectedCustomer(cRes.data);
          } catch (e) {
            console.error('Failed to fetch customer', e);
          }
        } else {
          setSelectedCustomer(null);
        }
      } else {
        setCart([]);
        setSelectedCustomer(null);
      }
      setSelectedTable(table);
      setMode('menu');
    }
  };

  const handleReserveOnly = async () => {
    if (!tableToReserve) return;
    try {
      await api.put(`/api/tables/${tableToReserve.id}/status?status=reserved`);
      setTableModalOpen(false);
      fetchTables();
    } catch {
      alert('Error reserving table');
    }
  };

  const handleOpenOrder = () => {
    setSelectedTable(tableToReserve);
    setMode('menu');
    setTableModalOpen(false);
  };

  const handleClearTable = () => {
    setClearTableConfirmOpen(true);
  };

  const confirmClearTable = async () => {
    if (!selectedTable) return;
    try {
      const tableOrder = activeOrders.find(o => o.table_id === selectedTable.id);
      if (tableOrder) {
        await api.patch(`/api/orders/${tableOrder.id}/status?status=cancelled&cancel_reason=Cleared`);
      } else {
        await api.put(`/api/tables/${selectedTable.id}/status?status=available`);
      }
      setCart([]);
      setSelectedTable(null);
      setMode('tables');
      fetchTables();
      setClearTableConfirmOpen(false);
    } catch {
      alert('Failed to clear table');
    }
  };

  const getElapsedMinutes = (dateString: string) => {
    const diff = Date.now() - new Date(dateString).getTime();
    return Math.max(0, Math.floor(diff / 60000));
  };

  const handleProceedToPayment = async () => {
    if (cart.length === 0) return;
    try {
      const existingOrder = activeOrders.find(o => o.table_id === selectedTable?.id);
      const payload = {
        table_id: selectedTable?.id || null,
        customer_id: selectedCustomer?.id || null,
        items: cart.map((c) => ({
          product_id: c.product.id,
          quantity: c.quantity,
          notes: c.notes,
        })),
      };
      let orderData;
      if (existingOrder) {
        const orderRes = await api.put(`/api/orders/${existingOrder.id}`, payload);
        orderData = orderRes.data;
      } else {
        const orderRes = await api.post('/api/orders', payload);
        orderData = orderRes.data;
      }
      navigate(`/pos/payment`, { state: { order: orderData, cart, subtotal, tax, total } });
    } catch (err: any) {
      alert(`Error: ${err.response?.data?.detail || 'Failed to create/update order'}`);
    }
  };

  const handleSaveDraft = async () => {
    if (cart.length === 0) return;
    try {
      const existingOrder = activeOrders.find(o => o.table_id === selectedTable?.id);
      const payload = {
        table_id: selectedTable?.id || null,
        customer_id: selectedCustomer?.id || null,
        items: cart.map((c) => ({
          product_id: c.product.id,
          quantity: c.quantity,
          notes: c.notes,
        })),
      };
      if (existingOrder) {
        await api.put(`/api/orders/${existingOrder.id}`, payload);
      } else {
        await api.post('/api/orders', payload);
      }
      setCart([]);
      setMode('tables');
      fetchTables();
    } catch (err: any) {
      alert(`Error: ${err.response?.data?.detail || 'Failed to save draft'}`);
    }
  };

  const handleSendToKitchen = async () => {
    if (cart.length === 0) return;
    try {
      const existingOrder = activeOrders.find(o => o.table_id === selectedTable?.id);
      const payload = {
        table_id: selectedTable?.id || null,
        customer_id: selectedCustomer?.id || null,
        items: cart.map((c) => ({
          product_id: c.product.id,
          quantity: c.quantity,
          notes: c.notes,
        })),
      };
      let orderId = existingOrder?.id;
      if (existingOrder) {
        await api.put(`/api/orders/${existingOrder.id}`, payload);
      } else {
        const orderRes = await api.post('/api/orders', payload);
        orderId = orderRes.data.id;
      }
      // Mark as in_progress to send to kitchen
      await api.patch(`/api/orders/${orderId}/status?status=in_progress`);
      
      setCart([]);
      setMode('tables');
      fetchTables();
    } catch (err: any) {
      alert(`Error: ${err.response?.data?.detail || 'Failed to send to kitchen'}`);
    }
  };

  const filteredTables = tables.filter(t => {
    if (statusFilter && t.status !== statusFilter) return false;
    return true;
  });

  return (
    <div className="pos-layout">
      {/* ── Category Sidebar ── */}
      <aside className="category-sidebar">
        <div className="sidebar-logo" style={{ padding: '1rem 1.25rem' }}>
          <div className="logo-icon" style={{ width: 32, height: 32, borderRadius: 8 }}>
            <ChefHat size={18} />
          </div>
          <div>
            <h1 style={{ fontSize: '0.875rem' }}>RestaurantPOS</h1>
            <span className="logo-subtitle">Main Terminal</span>
          </div>
        </div>

        <div className="category-search">
          <input placeholder="Search categories..." />
        </div>

        <div style={{ flex: 1, overflow: 'auto' }}>
          <button
            className={`category-item ${!selectedCat ? 'active' : ''}`}
            onClick={() => setSelectedCat(null)}
          >
            All Products
            <span className="category-count">{products.length}</span>
          </button>
          {categories.map((c) => {
            const count = products.filter(p => p.category_id === c.id).length;
            return (
              <button
                key={c.id}
                className={`category-item ${selectedCat === c.id ? 'active' : ''}`}
                onClick={() => { setSelectedCat(c.id); setMode('menu'); }}
              >
                {c.name}
                <span className="category-count">{count}</span>
              </button>
            );
          })}
        </div>

        {/* Sidebar footer - user info */}
        <div style={{ padding: '1rem', borderTop: '1px solid var(--color-border)' }}>
          <div style={{ fontWeight: 600, fontSize: '0.875rem', color: 'var(--color-text-primary)', marginBottom: '0.75rem' }}>{user?.full_name || 'Cashier'}</div>
          <button onClick={logout} className="btn btn-outline btn-sm" style={{ width: '100%', color: 'var(--color-danger)', borderColor: 'var(--color-danger)' }}>
            <LogOut size={14} /> Disconnect
          </button>
        </div>
      </aside>

      {/* ── Main Content ── */}
      <div className="pos-main">
        <div className="pos-topbar">
          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
            <h2 style={{ fontSize: '1.25rem', fontWeight: 700 }}>
              {mode === 'tables' ? 'Tables Overview' : selectedTable ? `Table T${selectedTable.number} Order` : 'Quick Order (To-Go)'}
            </h2>
            {mode === 'menu' && selectedTable && (
              <button className="btn btn-outline btn-sm" style={{ color: 'var(--color-danger)', borderColor: 'var(--color-danger)', padding: '0.25rem 0.5rem', height: 'auto' }} onClick={handleClearTable}>
                <Trash2 size={14} style={{ marginRight: 4 }} /> Clear Table
              </button>
            )}
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
            {mode === 'menu' && (
              <>
                <div style={{ position: 'relative' }}>
                  <Search size={16} style={{ position: 'absolute', left: 10, top: 10, color: 'var(--color-text-muted)' }} />
                  <input className="input" placeholder="Search products..." value={search} onChange={(e) => setSearch(e.target.value)}
                    style={{ paddingLeft: '2rem', width: 280 }} />
                </div>
              </>
            )}

            {mode === 'tables' && (
              <>
                <div style={{ position: 'relative' }}>
                  <Search size={16} style={{ position: 'absolute', left: 10, top: 10, color: 'var(--color-text-muted)' }} />
                  <input className="input" placeholder="Search tables..." value={tableFilter} onChange={(e) => setTableFilter(e.target.value)}
                    style={{ paddingLeft: '2rem', width: 280 }} />
                </div>
                <CustomSelect
                  options={[
                    { value: '', label: 'All Statuses' },
                    { value: 'available', label: 'Available' },
                    { value: 'occupied', label: 'Occupied' },
                    { value: 'reserved', label: 'Reserved' },
                  ]}
                  value={statusFilter}
                  onChange={setStatusFilter}
                  style={{ width: 150 }}
                />
              </>
            )}

            <div className="toggle-group">
              <button className={`toggle-btn ${mode === 'tables' ? 'active' : ''}`} onClick={() => setMode('tables')}>
                <Grid3X3 size={14} /> Tables Mode
              </button>
              <button className={`toggle-btn ${mode === 'menu' && !selectedTable ? 'active' : ''}`} onClick={() => { setSelectedTable(null); setMode('menu'); }}>
                <Zap size={14} /> Quick Order (To-Go)
              </button>
            </div>
          </div>
        </div>

        <div className="pos-content">
          {mode === 'tables' ? (
            /* ── TABLES MODE ── */
            <div className="tables-grid animate-fadeIn">
              {filteredTables.map((t) => {
                const tableOrder = activeOrders.find((o) => o.table_id === t.id);
                return (
                <div
                  key={t.id}
                  className={`table-card ${t.status}`}
                  onClick={() => handleSelectTable(t)}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start' }}>
                    <div>
                      <div className="table-num">T{t.number}</div>
                      <div className={`table-status ${t.status}`}>
                        {t.status === 'available' ? 'Available' :
                         t.status === 'occupied' ? 'Occupied' :
                         t.status === 'reserved' ? 'Reserved' : 'Ready for Payment'}
                      </div>
                    </div>
                    {t.status !== 'available' && (
                      <div className="guest-count">
                        <Users size={12} /> {t.capacity}
                      </div>
                    )}
                  </div>

                  {t.status === 'occupied' && (
                    <>
                      <div style={{ marginTop: 'auto' }}>
                        <div style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)' }}>Current Total</div>
                        <div className="table-total">{tableOrder ? tableOrder.total_amount.toFixed(2) : '0.00'} DT</div>
                      </div>
                      <div className="table-meta">
                        <Clock size={12} /> {tableOrder && tableOrder.created_at ? getElapsedMinutes(tableOrder.created_at) : 0} min
                      </div>
                    </>
                  )}
                </div>
              );
            })}
            </div>
          ) : (
            /* ── MENU / ORDER MODE ── */
            <div className="product-grid animate-fadeIn">
              {filtered.map((p) => (
                <div key={p.id} className="product-card" onClick={() => addToCart(p)}>
                  <div className="product-image" style={{ padding: 0, overflow: 'hidden' }}>
                    <img
                      src={`/images/products/${p.name}.png`}
                      alt={p.name}
                      style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                      onError={(e) => {
                        (e.target as HTMLImageElement).style.display = 'none';
                        const parent = (e.target as HTMLImageElement).parentElement;
                        if (parent) {
                          const icon = parent.querySelector('.fallback-icon') as HTMLElement;
                          if (icon) icon.style.display = 'flex';
                        }
                      }}
                    />
                    <div className="fallback-icon" style={{ display: 'none', position: 'absolute', top: '0', left: '0', width: '100%', height: '100%', alignItems: 'center', justifyContent: 'center' }}>
                      <Image size={32} />
                    </div>
                    {!p.is_available && (
                      <span className="out-of-stock" style={{ zIndex: 10 }}>Out of Stock</span>
                    )}
                  </div>
                  <div className="product-info">
                    <div className="product-name">{p.name}</div>
                    <div className="product-price">{p.price.toFixed(2)} DT</div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* ── Cart / Order Panel ── */}
      <div className="cart-panel">
        <div className="cart-header">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div className="order-id">Order #{orderNumber}</div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              {cart.length > 0 && (
                <button onClick={() => setCart([])} style={{ background: 'none', border: 'none', color: 'var(--color-danger)', fontSize: '0.75rem', cursor: 'pointer', fontWeight: 600 }}>
                  Clear All
                </button>
              )}
              <span className="badge badge-warning" style={{ fontSize: '0.625rem', padding: '0.15rem 0.5rem' }}>DRAFT</span>
            </div>
          </div>
          <div className="order-meta">
            {selectedTable ? `Table: T${selectedTable.number}` : 'Takeaway / To-Go'} &bull; Server: {user?.full_name}
          </div>
        </div>

        <div className="cart-items">
          {cart.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '3rem 1rem', color: 'var(--color-text-muted)' }}>
              <ShoppingCart size={32} style={{ margin: '0 auto 0.75rem', opacity: 0.3 }} />
              <p style={{ fontSize: '0.875rem' }}>No items in order yet.</p>
              <p style={{ fontSize: '0.8125rem' }}>Add products to get started.</p>
            </div>
          ) : (
            cart.map((item) => (
              <div key={item.product.id} className="cart-item">
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start' }}>
                  <div className="item-name">{item.product.name}</div>
                  <button onClick={() => removeItem(item.product.id)} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--color-danger)', padding: 2 }}>
                    <Trash2 size={14} />
                  </button>
                </div>
                <div className="item-controls">
                  <button className="qty-btn" onClick={() => updateQty(item.product.id, -1)}>-</button>
                  <span style={{ width: 28, textAlign: 'center', fontWeight: 600, fontSize: '0.875rem' }}>{item.quantity}</span>
                  <button className="qty-btn" onClick={() => updateQty(item.product.id, 1)}>+</button>
                  <span style={{ marginLeft: 'auto', fontWeight: 700, fontSize: '0.875rem' }}>
                    {(item.product.price * item.quantity).toFixed(2)} DT
                  </span>
                </div>
              </div>
            ))
          )}
        </div>

        {/* AI Recommendations */}
        {recommendations.length > 0 && cart.length > 0 && (
          <div className="ai-recommendations animate-slideIn">
            <div className="ai-rec-header">
              <Sparkles size={14} /> AI Recommendations
            </div>
            {recommendations.slice(0, 3).map((r, i) => (
              <div key={i} className="ai-rec-item" onClick={() => {
                const product = products.find(p => p.name === r.product_name);
                if (product) addToCart(product);
              }}>
                <span>{r.product_name}</span>
                <div className="add-icon"><Plus size={12} /></div>
              </div>
            ))}
          </div>
        )}

        {/* Cart Footer */}
        {cart.length > 0 && (
          <div className="cart-footer">
            <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '0.75rem' }}>
              <button className="btn btn-outline btn-sm" style={{ flex: 1, fontSize: '0.75rem' }}>
                Discount
              </button>
              <button 
                className={`btn btn-sm ${selectedCustomer ? 'btn-primary' : 'btn-outline'}`} 
                style={{ flex: 1, fontSize: '0.75rem', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}
                onClick={() => {
                  setCustomerModalOpen(true);
                  if (!customersList.length) {
                    api.get('/api/customers').then(r => setCustomersList(r.data));
                  }
                }}
              >
                {selectedCustomer ? `Linked: ${selectedCustomer.name}` : 'Customer'}
              </button>
            </div>

            <div className="cart-total-row">
              <span>Subtotal</span>
              <span>{subtotal.toFixed(2)} DT</span>
            </div>
            <div className="cart-total-row">
              <span>Tax (10%)</span>
              <span>{tax.toFixed(2)} DT</span>
            </div>
            <div className="cart-total-row total">
              <span>Total</span>
              <span className="total-amount">{total.toFixed(2)} DT</span>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', marginTop: '1rem' }}>
              <button className="btn btn-outline btn-sm" style={{ width: '100%' }} onClick={handleSaveDraft}>
                <Save size={14} /> Save Draft
              </button>
              <button className="btn btn-outline btn-sm" style={{ width: '100%', color: 'var(--color-primary)', borderColor: 'var(--color-primary)' }} onClick={handleSendToKitchen}>
                <ChefHat size={14} /> Send to Kitchen
              </button>
              <button className="btn btn-primary" style={{ width: '100%' }} onClick={handleProceedToPayment}>
                <CreditCard size={14} /> Proceed to Payment
              </button>
            </div>
          </div>
        )}
      </div>

      {/* ── Table Reservation Modal ── */}
      {tableModalOpen && tableToReserve && (
        <div className="modal-overlay">
          <div className="modal-content animate-slideUp">
            <h3 style={{ fontSize: '1.25rem', fontWeight: 700, marginBottom: '1rem' }}>
              Table T{tableToReserve.number}
            </h3>
            
            <div className="form-group" style={{ marginBottom: '1rem' }}>
              <label style={{ display: 'block', fontSize: '0.875rem', fontWeight: 600, marginBottom: '0.5rem' }}>Number of People (Covers)</label>
              <input 
                type="number" 
                className="input" 
                style={{ width: '100%', padding: '0.5rem', border: '1px solid var(--color-border)', borderRadius: '4px' }} 
                value={reserveCovers} 
                onChange={(e) => setReserveCovers(Number(e.target.value))} 
                min={1} 
              />
            </div>
            
            <div className="form-group" style={{ marginBottom: '1.5rem' }}>
              <label style={{ display: 'block', fontSize: '0.875rem', fontWeight: 600, marginBottom: '0.5rem' }}>Reservation Time (if reserving)</label>
              <input 
                type="time" 
                className="input" 
                style={{ width: '100%', padding: '0.5rem', border: '1px solid var(--color-border)', borderRadius: '4px' }} 
                value={reserveTime} 
                onChange={(e) => setReserveTime(e.target.value)} 
              />
            </div>

            <div style={{ display: 'flex', gap: '0.75rem', justifyContent: 'flex-end' }}>
              <button className="btn btn-outline" onClick={() => setTableModalOpen(false)}>Cancel</button>
              <button className="btn btn-primary" onClick={handleReserveOnly}>Reserve Only</button>
              <button className="btn btn-primary" style={{ background: 'var(--color-success)', borderColor: 'var(--color-success)' }} onClick={handleOpenOrder}>Open Order</button>
            </div>
          </div>
        </div>
      )}

      {/* ── Clear Table Confirmation Modal ── */}
      {clearTableConfirmOpen && (
        <div className="modal-overlay">
          <div className="modal-content animate-slideUp" style={{ maxWidth: 400, textAlign: 'center' }}>
            <h3 style={{ fontSize: '1.25rem', fontWeight: 700, marginBottom: '0.75rem', color: 'var(--color-danger)' }}>
              Clear Table
            </h3>
            <p style={{ marginBottom: '1.5rem', color: 'var(--color-text-secondary)', fontSize: '0.875rem' }}>
              Are you sure you want to clear this table? Any active order will be permanently cancelled.
            </p>
            <div style={{ display: 'flex', gap: '0.75rem', justifyContent: 'center' }}>
              <button className="btn btn-outline" style={{ flex: 1 }} onClick={() => setClearTableConfirmOpen(false)}>Cancel</button>
              <button className="btn btn-primary" style={{ flex: 1, background: 'var(--color-danger)', borderColor: 'var(--color-danger)' }} onClick={confirmClearTable}>Yes, Clear It</button>
            </div>
          </div>
        </div>
      )}

      {/* ── Customer Modal ── */}
      {customerModalOpen && (
        <div className="modal-overlay">
          <div className="modal-content animate-slideUp" style={{ maxWidth: 500, width: '100%' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
              <h3 style={{ fontSize: '1.25rem', fontWeight: 700 }}>
                {isRegistering ? 'Quick Register Customer' : 'Select Customer'}
              </h3>
              {selectedCustomer && !isRegistering && (
                <button 
                  className="btn btn-outline btn-sm" 
                  style={{ color: 'var(--color-danger)', borderColor: 'var(--color-danger)' }}
                  onClick={() => { setSelectedCustomer(null); setCustomerModalOpen(false); }}
                >
                  Unlink
                </button>
              )}
            </div>

            {!isRegistering ? (
              <>
                <div style={{ position: 'relative', marginBottom: '1rem' }}>
                  <Search size={16} style={{ position: 'absolute', left: 10, top: 10, color: 'var(--color-text-muted)' }} />
                  <input 
                    className="input" 
                    placeholder="Search by name or phone..." 
                    value={customerSearch} 
                    onChange={async (e) => {
                      setCustomerSearch(e.target.value);
                      if (e.target.value.length >= 2) {
                        try {
                          const res = await api.get(`/api/customers?search=${e.target.value}`);
                          setCustomersList(res.data);
                        } catch (err) { console.error(err); }
                      } else if (e.target.value === '') {
                        try {
                          const res = await api.get('/api/customers');
                          setCustomersList(res.data);
                        } catch (err) { console.error(err); }
                      }
                    }}
                    style={{ paddingLeft: '2rem', width: '100%' }} 
                  />
                </div>
                
                <div style={{ maxHeight: 300, overflowY: 'auto', marginBottom: '1rem', border: '1px solid var(--color-border)', borderRadius: 8 }}>
                  {customersList.map(c => (
                    <div 
                      key={c.id} 
                      style={{ 
                        padding: '0.75rem 1rem', 
                        borderBottom: '1px solid var(--color-border)', 
                        display: 'flex', 
                        justifyContent: 'space-between',
                        alignItems: 'center',
                        cursor: 'pointer',
                        background: selectedCustomer?.id === c.id ? 'var(--color-bg-page)' : 'transparent'
                      }}
                      onClick={() => {
                        setSelectedCustomer(c);
                        setCustomerModalOpen(false);
                      }}
                    >
                      <div>
                        <div style={{ fontWeight: 600 }}>{c.name}</div>
                        <div style={{ fontSize: '0.8125rem', color: 'var(--color-text-secondary)' }}>{c.phone || 'No phone'}</div>
                      </div>
                      {selectedCustomer?.id === c.id && <div style={{ color: 'var(--color-primary)', fontWeight: 600 }}>Selected</div>}
                    </div>
                  ))}
                  {customersList.length === 0 && (
                    <div style={{ padding: '2rem', textAlign: 'center', color: 'var(--color-text-muted)' }}>
                      No customers found.
                    </div>
                  )}
                </div>

                <div style={{ display: 'flex', gap: '0.75rem', justifyContent: 'space-between' }}>
                  <button className="btn btn-outline" onClick={() => setCustomerModalOpen(false)}>Close</button>
                  <button className="btn btn-primary" onClick={() => {
                    setNewCustomerName(customerSearch);
                    setIsRegistering(true);
                  }}>
                    <Plus size={16} /> New Customer
                  </button>
                </div>
              </>
            ) : (
              <>
                <div className="form-group" style={{ marginBottom: '1rem' }}>
                  <label style={{ display: 'block', fontSize: '0.875rem', fontWeight: 600, marginBottom: '0.5rem' }}>Name *</label>
                  <input 
                    type="text" 
                    className="input" 
                    style={{ width: '100%' }} 
                    value={newCustomerName} 
                    onChange={(e) => setNewCustomerName(e.target.value)} 
                    autoFocus
                  />
                </div>
                <div className="form-group" style={{ marginBottom: '1rem' }}>
                  <label style={{ display: 'block', fontSize: '0.875rem', fontWeight: 600, marginBottom: '0.5rem' }}>Phone *</label>
                  <input 
                    type="tel" 
                    className="input" 
                    style={{ width: '100%' }} 
                    value={newCustomerPhone} 
                    onChange={(e) => setNewCustomerPhone(e.target.value)} 
                    placeholder="Unique phone number"
                  />
                </div>
                <div className="form-group" style={{ marginBottom: '1.5rem' }}>
                  <label style={{ display: 'block', fontSize: '0.875rem', fontWeight: 600, marginBottom: '0.5rem' }}>Email (Optional)</label>
                  <input 
                    type="email" 
                    className="input" 
                    style={{ width: '100%' }} 
                    value={newCustomerEmail} 
                    onChange={(e) => setNewCustomerEmail(e.target.value)} 
                  />
                </div>
                <div style={{ display: 'flex', gap: '0.75rem', justifyContent: 'flex-end' }}>
                  <button className="btn btn-outline" onClick={() => setIsRegistering(false)}>Back to Search</button>
                  <button 
                    className="btn btn-primary" 
                    disabled={!newCustomerName.trim() || !newCustomerPhone.trim()}
                    onClick={async () => {
                      try {
                        const res = await api.post('/api/customers', {
                          name: newCustomerName,
                          phone: newCustomerPhone,
                          email: newCustomerEmail
                        });
                        setSelectedCustomer(res.data);
                        setCustomerModalOpen(false);
                        setIsRegistering(false);
                        // reset form
                        setNewCustomerName('');
                        setNewCustomerPhone('');
                        setNewCustomerEmail('');
                      } catch (err: any) {
                        if (err.response?.status === 409) {
                          const existing = err.response.data.detail.existing_customer;
                          if (window.confirm(`Phone number already exists for: ${existing.name}. Link them to this order instead?`)) {
                            setSelectedCustomer(existing);
                            setCustomerModalOpen(false);
                            setIsRegistering(false);
                          }
                        } else {
                          alert(err.response?.data?.detail || 'Failed to create customer');
                        }
                      }
                    }}
                  >
                    Register & Link
                  </button>
                </div>
              </>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
