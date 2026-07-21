import { useEffect, useState } from 'react';
import api from '../api';
import { Warehouse, Plus, Edit2, Trash2, X, ArrowUpDown } from 'lucide-react';

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

      {showIngModal && (
        <div className="modal-overlay animate-fadeIn">
          <div className="modal-content animate-slideUp" style={{ maxWidth: 500 }}>
            <div className="modal-header">
              <h3>{editingIng ? 'Edit Ingredient' : 'Add Ingredient'}</h3>
              <button className="btn-icon" onClick={() => setShowIngModal(false)}><X size={20} /></button>
            </div>
            <form onSubmit={handleSaveIngredient}>
              <div className="form-group">
                <label>Name</label>
                <input className="form-control" required value={ingFormData.name} onChange={e => setIngFormData({...ingFormData, name: e.target.value})} />
              </div>
              <div style={{ display: 'flex', gap: '1rem' }}>
                <div className="form-group" style={{ flex: 1 }}>
                  <label>Unit (e.g., g, ml)</label>
                  <input className="form-control" required value={ingFormData.unit} onChange={e => setIngFormData({...ingFormData, unit: e.target.value})} />
                </div>
                <div className="form-group" style={{ flex: 1 }}>
                  <label>Cost per unit (DT)</label>
                  <input type="number" step="0.001" className="form-control" required value={ingFormData.cost_per_unit} onChange={e => setIngFormData({...ingFormData, cost_per_unit: parseFloat(e.target.value) || 0})} />
                </div>
              </div>
              <div style={{ display: 'flex', gap: '1rem' }}>
                <div className="form-group" style={{ flex: 1 }}>
                  <label>Current Stock</label>
                  <input type="number" step="0.1" className="form-control" required value={ingFormData.current_stock} onChange={e => setIngFormData({...ingFormData, current_stock: parseFloat(e.target.value) || 0})} />
                </div>
                <div className="form-group" style={{ flex: 1 }}>
                  <label>Low Stock Threshold</label>
                  <input type="number" step="0.1" className="form-control" required value={ingFormData.low_stock_threshold} onChange={e => setIngFormData({...ingFormData, low_stock_threshold: parseFloat(e.target.value) || 0})} />
                </div>
              </div>
              <div style={{ display: 'flex', gap: '1rem' }}>
                <div className="form-group" style={{ flex: 1 }}>
                  <label>Supplier</label>
                  <input className="form-control" value={ingFormData.supplier} onChange={e => setIngFormData({...ingFormData, supplier: e.target.value})} />
                </div>
                <div className="form-group" style={{ flex: 1 }}>
                  <label>Category</label>
                  <input className="form-control" value={ingFormData.category} onChange={e => setIngFormData({...ingFormData, category: e.target.value})} />
                </div>
              </div>
              <div className="modal-actions">
                <button type="button" className="btn btn-ghost" onClick={() => setShowIngModal(false)}>Cancel</button>
                <button type="submit" className="btn btn-primary">Save Ingredient</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {adjustItem && (
        <div className="modal-overlay animate-fadeIn">
          <div className="modal-content animate-slideUp" style={{ maxWidth: 420 }}>
            <div className="modal-header">
              <h3>Adjust Stock: {adjustItem.name}</h3>
              <button className="btn-icon" onClick={() => setAdjustItem(null)}><X size={20} /></button>
            </div>
            <p style={{ fontSize: '0.8125rem', color: 'var(--color-text-muted)', marginBottom: '1rem' }}>
              Current stock: <strong>{adjustItem.current_stock?.toLocaleString()} {adjustItem.unit}</strong>
            </p>
            <form onSubmit={handleAdjust}>
              <div className="form-group">
                <label>Quantity Change (positive to add, negative to remove)</label>
                <input type="number" step="0.1" className="form-control" required value={adjustQty} onChange={e => setAdjustQty(e.target.value)} placeholder="e.g. 500 or -200" />
              </div>
              <div className="form-group">
                <label>Reason</label>
                <select className="form-control" value={adjustReason} onChange={e => setAdjustReason(e.target.value)}>
                  <option value="adjustment">Manual Adjustment</option>
                  <option value="restock">Restock / Delivery</option>
                  <option value="waste">Waste / Spoilage</option>
                  <option value="correction">Inventory Correction</option>
                </select>
              </div>
              <div className="form-group">
                <label>Details (optional)</label>
                <input className="form-control" value={adjustDetails} onChange={e => setAdjustDetails(e.target.value)} placeholder="e.g. Supplier delivery #1234" />
              </div>
              <div className="modal-actions">
                <button type="button" className="btn btn-ghost" onClick={() => setAdjustItem(null)}>Cancel</button>
                <button type="submit" className="btn btn-primary">Apply Adjustment</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
