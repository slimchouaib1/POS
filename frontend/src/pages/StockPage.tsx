import { useEffect, useState } from 'react';
import api from '../api';
import {
  Warehouse, Plus, Edit2, Trash2, X, ArrowUpDown,
  Package, Layers, Scale, DollarSign, Archive, AlertTriangle,
  Building2, Tag, Check
} from 'lucide-react';

export default function StockPage() {
  const [stock, setStock] = useState<any[]>([]);
  const [alerts, setAlerts] = useState<any[]>([]);
  const [ingredients, setIngredients] = useState<any[]>([]);
  const [tab, setTab] = useState<'all' | 'alerts' | 'ingredients'>('all');
  
  // Adjust Modal State
  const [adjustItem, setAdjustItem] = useState<any>(null);
  const [adjustQty, setAdjustQty] = useState('');
  const [adjustReason, setAdjustReason] = useState('adjustment');
  const [adjustDetails, setAdjustDetails] = useState('');

  // Ingredient CRUD Modal
  const [showIngModal, setShowIngModal] = useState(false);
  const [editingIng, setEditingIng] = useState<any>(null);
  const [ingFormData, setIngFormData] = useState({
    name: '', unit: '', current_stock: 0, low_stock_threshold: 500, cost_per_unit: 0.01, supplier: '', category: ''
  });

  const loadData = () => {
    api.get('/api/stock').then((r) => setStock(r.data));
    api.get('/api/stock/alerts').then((r) => setAlerts(r.data));
    api.get('/api/stock/ingredients').then((r) => setIngredients(r.data));
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleAdjust = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!adjustItem || !adjustQty) return;
    
    try {
      await api.post('/api/stock/ingredients/adjust', {
        ingredient_id: adjustItem.ingredient_id,
        quantity_change: parseFloat(adjustQty),
        reason: adjustReason,
        details: adjustDetails
      });
      setAdjustItem(null);
      setAdjustQty('');
      setAdjustDetails('');
      loadData();
    } catch (err) {
      alert("Failed to adjust stock");
    }
  };

  const handleSaveIngredient = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      if (editingIng) {
        await api.put(`/api/ingredients/${editingIng.ingredient_id || editingIng.id}`, ingFormData);
      } else {
        await api.post('/api/ingredients', ingFormData);
      }
      setShowIngModal(false);
      loadData();
    } catch (err: any) {
      alert(err.response?.data?.detail || "Failed to save ingredient");
    }
  };

  const handleDeleteIngredient = async (id: number) => {
    if (confirm("Delete this ingredient?")) {
      try {
        await api.delete(`/api/ingredients/${id}`);
        loadData();
      } catch (err: any) {
        alert(err.response?.data?.detail || "Failed to delete ingredient");
      }
    }
  };

  const data = tab === 'alerts' ? alerts : stock;

  return (
    <div className="animate-fadeIn">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div className="page-header">
          <h2>Stock Management</h2>
          <p>{stock.length} products tracked • {ingredients.length} ingredients • {alerts.length} alerts</p>
        </div>
        {tab === 'ingredients' && (
          <button className="btn btn-primary" onClick={() => {
            setEditingIng(null);
            setIngFormData({ name: '', unit: 'g', current_stock: 0, low_stock_threshold: 500, cost_per_unit: 0.01, supplier: '', category: '' });
            setShowIngModal(true);
          }}>
            <Plus size={16} /> Add Ingredient
          </button>
        )}
      </div>

      <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1rem' }}>
        <button className={`btn btn-sm ${tab === 'all' ? 'btn-primary' : 'btn-ghost'}`} onClick={() => setTab('all')}>
          <Warehouse size={14} /> All stock
        </button>
        <button className={`btn btn-sm ${tab === 'ingredients' ? 'btn-primary' : 'btn-ghost'}`} onClick={() => setTab('ingredients')}>
          Ingredients
        </button>
        {alerts.length > 0 && (
          <button className={`btn btn-sm ${tab === 'alerts' ? 'btn-danger' : 'btn-ghost'}`} onClick={() => setTab('alerts')}>
            ⚠️ {alerts.length} Low Stock Alerts
          </button>
        )}
      </div>

      <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
        {tab === 'ingredients' ? (
          <table className="data-table">
            <thead>
              <tr>
                <th>Ingredient</th>
                <th>Category</th>
                <th>Supplier</th>
                <th>Current Stock</th>
                <th>Threshold</th>
                <th>Status</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {ingredients.map((ing: any, i: number) => (
                <tr key={i}>
                  <td style={{ fontWeight: 600 }}>{ing.name}</td>
                  <td>{ing.category}</td>
                  <td>{ing.supplier || '—'}</td>
                  <td style={{ fontWeight: 600 }}>{ing.current_stock.toLocaleString()} {ing.unit}</td>
                  <td>{ing.low_stock_threshold.toLocaleString()} {ing.unit}</td>
                  <td>
                    <span className={ing.is_low_stock ? 'badge badge-danger' : 'badge badge-success'}>
                      {ing.is_low_stock ? '⚠️ Low stock' : '✓ OK'}
                    </span>
                  </td>
                  <td>
                    <div style={{ display: 'flex', gap: '0.25rem' }}>
                      <button className="btn btn-sm btn-ghost" onClick={() => {
                        setAdjustItem(ing);
                        setAdjustQty('');
                        setAdjustReason('adjustment');
                        setAdjustDetails('');
                      }}>
                        <ArrowUpDown size={14} /> Adjust
                      </button>
                      <button className="btn btn-sm btn-ghost" onClick={() => {
                        setEditingIng(ing);
                        setIngFormData({
                          name: ing.name, unit: ing.unit, current_stock: ing.current_stock,
                          low_stock_threshold: ing.low_stock_threshold, cost_per_unit: ing.cost_per_unit,
                          supplier: ing.supplier || '', category: ing.category || ''
                        });
                        setShowIngModal(true);
                      }}>
                        <Edit2 size={14} /> Edit
                      </button>
                      <button className="btn btn-sm btn-ghost" style={{ color: 'var(--color-danger)' }} onClick={() => handleDeleteIngredient(ing.ingredient_id || ing.id)}>
                        <Trash2 size={14} /> Delete
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <table className="data-table">
            <thead>
              <tr>
                <th>Product</th>
                <th>Category</th>
                <th>Section</th>
                <th>Quantity</th>
                <th>Threshold</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {data.map((s: any, i: number) => (
                <tr key={i}>
                  <td style={{ fontWeight: 600 }}>{s.product_name}</td>
                  <td>{s.category_name}</td>
                  <td>{s.section || '—'}</td>
                  <td style={{ fontWeight: 600 }}>{s.stock_quantity}</td>
                  <td>{s.low_stock_threshold}</td>
                  <td>
                    <span className={s.is_low_stock ? 'badge badge-danger' : 'badge badge-success'}>
                      {s.is_low_stock ? '⚠️ Low stock' : '✓ OK'}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* ── Add / Edit Ingredient Modal ── */}
      {showIngModal && (
        <div className="modal-overlay animate-fadeIn" onClick={() => setShowIngModal(false)}>
          <div
            className="modal-content animate-slideUp"
            style={{ maxWidth: 540, padding: '1.75rem' }}
            onClick={e => e.stopPropagation()}
          >
            {/* Modal Header */}
            <div className="modal-header">
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                <div style={{
                  width: 38,
                  height: 38,
                  borderRadius: 10,
                  background: 'rgba(220, 53, 69, 0.1)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: 'var(--color-primary)',
                  flexShrink: 0
                }}>
                  <Package size={20} />
                </div>
                <div>
                  <h3 style={{ fontSize: '1.125rem', fontWeight: 700, margin: 0, color: 'var(--color-text-primary)' }}>
                    {editingIng ? 'Edit Ingredient' : 'Add New Ingredient'}
                  </h3>
                  <p style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)', margin: '0.15rem 0 0 0' }}>
                    {editingIng ? `Update specifications for ${editingIng.name}` : 'Register a new raw material in inventory'}
                  </p>
                </div>
              </div>
              <button
                type="button"
                className="btn-icon"
                onClick={() => setShowIngModal(false)}
                title="Close"
              >
                <X size={18} />
              </button>
            </div>

            {/* Form */}
            <form onSubmit={handleSaveIngredient}>
              {/* Ingredient Name */}
              <div className="form-group">
                <label>
                  <Tag size={13} color="var(--color-primary)" /> Ingredient Name
                </label>
                <input
                  className="form-control"
                  required
                  placeholder="e.g. Tomato, Olive Oil, Ground Beef, Mozzarella"
                  value={ingFormData.name}
                  onChange={e => setIngFormData({ ...ingFormData, name: e.target.value })}
                />
              </div>

              {/* Category & Supplier */}
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.875rem' }}>
                <div className="form-group">
                  <label>
                    <Layers size={13} color="var(--color-primary)" /> Category
                  </label>
                  <input
                    className="form-control"
                    placeholder="e.g. Vegetables, Meat, Dairy"
                    list="ingredient-categories"
                    value={ingFormData.category}
                    onChange={e => setIngFormData({ ...ingFormData, category: e.target.value })}
                  />
                  <datalist id="ingredient-categories">
                    <option value="Vegetables" />
                    <option value="Meat & Poultry" />
                    <option value="Dairy & Cheese" />
                    <option value="Bakery & Dough" />
                    <option value="Sauces & Condiments" />
                    <option value="Spices & Seasoning" />
                    <option value="Beverages & Syrups" />
                    <option value="Dry Goods & Grains" />
                    <option value="Packaging & Disposables" />
                  </datalist>
                </div>

                <div className="form-group">
                  <label>
                    <Building2 size={13} color="var(--color-primary)" /> Supplier
                  </label>
                  <input
                    className="form-control"
                    placeholder="e.g. Fresh Farm Suppliers"
                    value={ingFormData.supplier}
                    onChange={e => setIngFormData({ ...ingFormData, supplier: e.target.value })}
                  />
                </div>
              </div>

              {/* Unit of Measure & Cost per Unit */}
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.875rem' }}>
                <div className="form-group">
                  <label>
                    <Scale size={13} color="var(--color-primary)" /> Unit of Measure
                  </label>
                  <select
                    className="form-control"
                    required
                    value={ingFormData.unit}
                    onChange={e => setIngFormData({ ...ingFormData, unit: e.target.value })}
                  >
                    <option value="g">g (Grams)</option>
                    <option value="ml">ml (Milliliters)</option>
                    <option value="kg">kg (Kilograms)</option>
                    <option value="L">L (Liters)</option>
                    <option value="pcs">pcs (Pieces)</option>
                    <option value="slices">slices</option>
                    <option value="cans">cans</option>
                    <option value="portion">portion</option>
                  </select>
                </div>

                <div className="form-group">
                  <label>
                    <DollarSign size={13} color="var(--color-primary)" /> Cost per Unit (DT)
                  </label>
                  <input
                    type="number"
                    step="0.001"
                    min="0"
                    className="form-control"
                    required
                    placeholder="0.010"
                    value={ingFormData.cost_per_unit}
                    onChange={e => setIngFormData({ ...ingFormData, cost_per_unit: parseFloat(e.target.value) || 0 })}
                  />
                </div>
              </div>

              {/* Current Stock & Low Stock Threshold */}
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.875rem' }}>
                <div className="form-group">
                  <label>
                    <Archive size={13} color="var(--color-primary)" /> Current Stock ({ingFormData.unit || 'units'})
                  </label>
                  <input
                    type="number"
                    step="0.1"
                    min="0"
                    className="form-control"
                    required
                    placeholder="0"
                    value={ingFormData.current_stock}
                    onChange={e => setIngFormData({ ...ingFormData, current_stock: parseFloat(e.target.value) || 0 })}
                  />
                </div>

                <div className="form-group">
                  <label>
                    <AlertTriangle size={13} color="#F59E0B" /> Low Alert Threshold ({ingFormData.unit || 'units'})
                  </label>
                  <input
                    type="number"
                    step="0.1"
                    min="0"
                    className="form-control"
                    required
                    placeholder="500"
                    value={ingFormData.low_stock_threshold}
                    onChange={e => setIngFormData({ ...ingFormData, low_stock_threshold: parseFloat(e.target.value) || 0 })}
                  />
                </div>
              </div>

              {/* Modal Actions */}
              <div className="modal-actions">
                <button
                  type="button"
                  className="btn btn-outline"
                  onClick={() => setShowIngModal(false)}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="btn btn-primary"
                  style={{ display: 'flex', alignItems: 'center', gap: '0.375rem' }}
                >
                  <Check size={16} />
                  {editingIng ? 'Save Changes' : 'Create Ingredient'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ── Adjust Stock Modal ── */}
      {adjustItem && (
        <div className="modal-overlay animate-fadeIn" onClick={() => setAdjustItem(null)}>
          <div
            className="modal-content animate-slideUp"
            style={{ maxWidth: 460, padding: '1.75rem' }}
            onClick={e => e.stopPropagation()}
          >
            {/* Modal Header */}
            <div className="modal-header">
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                <div style={{
                  width: 38,
                  height: 38,
                  borderRadius: 10,
                  background: 'rgba(244, 132, 95, 0.12)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: '#F4845F',
                  flexShrink: 0
                }}>
                  <ArrowUpDown size={20} />
                </div>
                <div>
                  <h3 style={{ fontSize: '1.125rem', fontWeight: 700, margin: 0, color: 'var(--color-text-primary)' }}>
                    Adjust Stock
                  </h3>
                  <p style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)', margin: '0.15rem 0 0 0' }}>
                    {adjustItem.name} ({adjustItem.category || 'Ingredient'})
                  </p>
                </div>
              </div>
              <button
                type="button"
                className="btn-icon"
                onClick={() => setAdjustItem(null)}
                title="Close"
              >
                <X size={18} />
              </button>
            </div>

            {/* Current Stock Banner */}
            <div style={{
              background: 'var(--color-bg-secondary)',
              border: '1px solid var(--color-border)',
              borderRadius: 10,
              padding: '0.875rem 1rem',
              marginBottom: '1.25rem',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center'
            }}>
              <div>
                <span style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)', display: 'block', marginBottom: '0.15rem' }}>
                  Current Inventory
                </span>
                <span style={{ fontSize: '1.125rem', fontWeight: 700, color: 'var(--color-text-primary)' }}>
                  {adjustItem.current_stock?.toLocaleString()} {adjustItem.unit}
                </span>
              </div>
              <span className={adjustItem.is_low_stock ? 'badge badge-danger' : 'badge badge-success'}>
                {adjustItem.is_low_stock ? '⚠️ Low Stock' : '✓ Stock Healthy'}
              </span>
            </div>

            <form onSubmit={handleAdjust}>
              {/* Quick Delta Chips */}
              <div style={{ marginBottom: '1rem' }}>
                <label style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--color-text-muted)', display: 'block', marginBottom: '0.375rem' }}>
                  Quick Presets:
                </label>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.375rem' }}>
                  {['+100', '+500', '+1000', '+2000', '-100', '-500'].map((preset) => (
                    <button
                      key={preset}
                      type="button"
                      onClick={() => setAdjustQty(preset.replace('+', ''))}
                      style={{
                        padding: '0.3rem 0.6rem',
                        fontSize: '0.75rem',
                        fontWeight: 600,
                        borderRadius: 6,
                        border: '1px solid var(--color-border)',
                        background: 'var(--color-bg-card)',
                        color: preset.startsWith('+') ? '#28A745' : 'var(--color-danger)',
                        cursor: 'pointer',
                        transition: 'all 0.15s ease'
                      }}
                    >
                      {preset} {adjustItem.unit}
                    </button>
                  ))}
                </div>
              </div>

              {/* Quantity Change Input */}
              <div className="form-group">
                <label>
                  Quantity Change ({adjustItem.unit})
                </label>
                <input
                  type="number"
                  step="0.1"
                  className="form-control"
                  required
                  placeholder="e.g. +500 to restock, -200 for waste"
                  value={adjustQty}
                  onChange={e => setAdjustQty(e.target.value)}
                  autoFocus
                />
                <span style={{ fontSize: '0.6875rem', color: 'var(--color-text-muted)' }}>
                  Use positive numbers to add stock, negative to deduct.
                </span>
              </div>

              {/* Live Preview if quantity entered */}
              {adjustQty && !isNaN(parseFloat(adjustQty)) && (
                <div style={{
                  padding: '0.625rem 0.875rem',
                  borderRadius: 8,
                  marginBottom: '1rem',
                  background: parseFloat(adjustQty) >= 0 ? 'rgba(40, 167, 69, 0.08)' : 'rgba(220, 53, 69, 0.08)',
                  border: `1px solid ${parseFloat(adjustQty) >= 0 ? 'rgba(40, 167, 69, 0.25)' : 'rgba(220, 53, 69, 0.25)'}`,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  fontSize: '0.8125rem'
                }}>
                  <span style={{ color: 'var(--color-text-secondary)' }}>Calculated New Stock:</span>
                  <span style={{
                    fontWeight: 700,
                    color: parseFloat(adjustQty) >= 0 ? '#28A745' : 'var(--color-danger)'
                  }}>
                    {Math.max(0, (adjustItem.current_stock || 0) + parseFloat(adjustQty)).toLocaleString()} {adjustItem.unit}
                  </span>
                </div>
              )}

              {/* Reason Dropdown */}
              <div className="form-group">
                <label>Reason for Movement</label>
                <select
                  className="form-control"
                  value={adjustReason}
                  onChange={e => setAdjustReason(e.target.value)}
                >
                  <option value="restock">🚚 Restock / Supplier Delivery (+)</option>
                  <option value="waste">🗑️ Waste / Spoilage / Expired (-)</option>
                  <option value="correction">📋 Inventory Physical Audit (±)</option>
                  <option value="adjustment">⚙️ Manual Adjustment (±)</option>
                </select>
              </div>

              {/* Details / Reference */}
              <div className="form-group">
                <label>Details / Reference (Optional)</label>
                <input
                  className="form-control"
                  placeholder="e.g. Invoice #2026-0904, Batch #492"
                  value={adjustDetails}
                  onChange={e => setAdjustDetails(e.target.value)}
                />
              </div>

              {/* Modal Actions */}
              <div className="modal-actions">
                <button
                  type="button"
                  className="btn btn-outline"
                  onClick={() => setAdjustItem(null)}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="btn btn-primary"
                  style={{
                    background: '#28A745',
                    borderColor: '#28A745',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.375rem'
                  }}
                >
                  <Check size={16} /> Apply Adjustment
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
