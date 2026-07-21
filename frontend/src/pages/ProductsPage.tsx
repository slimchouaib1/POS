import React, { useEffect, useState } from 'react';
import api from '../api';
import { Search, Plus, Edit, Trash2, Image, X } from 'lucide-react';
import CustomSelect from '../components/CustomSelect';

interface Product {
  id: number;
  name: string;
  category_id: number;
  category_name?: string;
  price: number;
  stock_quantity: number;
  is_available: boolean;
}

interface Category {
  id: number;
  name: string;
}

export default function ProductsPage() {
  const [products, setProducts] = useState<Product[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [search, setSearch] = useState('');
  const [catFilter, setCatFilter] = useState('');
  const [stockFilter, setStockFilter] = useState('');


  const [showModal, setShowModal] = useState(false);
  const [editingProduct, setEditingProduct] = useState<Product | null>(null);
  const [formData, setFormData] = useState({ name: '', category_id: 1, price: 0, stock_quantity: 0, is_available: true });
  const [loading, setLoading] = useState(false);
  const [modalTab, setModalTab] = useState<'details' | 'recipe'>('details');

  // Recipe State
  const [ingredients, setIngredients] = useState<any[]>([]);
  const [recipeLines, setRecipeLines] = useState<any[]>([]);
  const [newRecipeLine, setNewRecipeLine] = useState({ ingredient_id: '', quantity_needed: '' });
  const [editingQty, setEditingQty] = useState<{ ingredientId: number; value: string } | null>(null);



  const loadProducts = () => {
    api.get('/api/products').then(r => setProducts(r.data)).catch(console.error);
  };

  const handleRegenerateRules = async () => {
    if (confirm("Regenerate AI Recommendation rules? This may take a moment.")) {
      setLoading(true);
      try {
        const res = await api.post('/api/ai/recommendations/reload');
        alert(res.data.message || "Rules regenerated successfully.");
      } catch (err: any) {
        alert(err.response?.data?.detail || "Failed to regenerate rules");
      }
      setLoading(false);
    }
  };

  const loadIngredients = () => {
    api.get('/api/ingredients').then(r => setIngredients(r.data)).catch(console.error);
  };

  const loadRecipeLines = (productId: number) => {
    api.get(`/api/products/${productId}/recipe`).then(r => setRecipeLines(r.data)).catch(console.error);
  };

  useEffect(() => {
    loadProducts();
    loadIngredients();
    api.get('/api/categories').then(r => setCategories(r.data)).catch(console.error);
  }, []);

  useEffect(() => {
    if (editingProduct) {
      loadRecipeLines(editingProduct.id);
    } else {
      setRecipeLines([]);
    }
  }, [editingProduct]);

  const handleAddRecipeLine = async () => {
    if (!editingProduct) return;
    if (!newRecipeLine.ingredient_id || !newRecipeLine.quantity_needed) return;
    try {
      await api.post(`/api/products/${editingProduct.id}/recipe`, {
        ingredient_id: Number(newRecipeLine.ingredient_id),
        quantity_needed: parseFloat(newRecipeLine.quantity_needed)
      });
      setNewRecipeLine({ ingredient_id: '', quantity_needed: '' });
      loadRecipeLines(editingProduct.id);
    } catch (err: any) {
      alert(err.response?.data?.detail || "Failed to add recipe line");
    }
  };

  const handleDeleteRecipeLine = async (ingredientId: number) => {
    if (!editingProduct) return;
    try {
      await api.delete(`/api/products/${editingProduct.id}/recipe/${ingredientId}`);
      loadRecipeLines(editingProduct.id);
    } catch (err: any) {
      alert(err.response?.data?.detail || "Failed to remove recipe line");
    }
  };

  const handleUpdateRecipeLine = async (ingredientId: number, newQty: string) => {
    if (!editingProduct) return;
    const qty = parseFloat(newQty);
    if (isNaN(qty) || qty <= 0) { alert('Please enter a valid quantity'); return; }
    try {
      await api.put(`/api/products/${editingProduct.id}/recipe/${ingredientId}`, { quantity_needed: qty });
      setEditingQty(null);
      loadRecipeLines(editingProduct.id);
    } catch (err: any) {
      alert(err.response?.data?.detail || "Failed to update recipe line");
    }
  };


  const getCategory = (id: number) => categories.find(c => c.id === id)?.name || '—';

  const getStockStatus = (qty: number) => {
    if (qty <= 0) return { label: 'Out of Stock', badge: 'badge-danger' };
    if (qty <= 10) return { label: 'Low Stock', badge: 'badge-warning' };
    return { label: 'In Stock', badge: 'badge-success' };
  };

  const filtered = products.filter(p => {
    if (search && !p.name.toLowerCase().includes(search.toLowerCase())) return false;
    if (catFilter && p.category_id !== Number(catFilter)) return false;
    if (stockFilter) {
      if (stockFilter === 'out' && p.stock_quantity > 0) return false;
      if (stockFilter === 'low' && (p.stock_quantity <= 0 || p.stock_quantity > 10)) return false;
      if (stockFilter === 'in' && p.stock_quantity <= 10) return false;
    }
    return true;
  });

  const toggleAvailability = async (id: number, current: boolean) => {
    try {
      await api.patch(`/api/products/${id}/toggle`);
      setProducts(prev => prev.map(p => p.id === id ? { ...p, is_available: !current } : p));
    } catch (err) {
      console.error(err);
    }
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      if (editingProduct) {
        await api.put(`/api/products/${editingProduct.id}`, formData);
        setShowModal(false);
      } else {
        // Create new product, then transition to edit mode so recipe builder is immediately available
        const res = await api.post('/api/products', formData);
        const created = res.data;
        setEditingProduct({ id: created.id, name: created.name, category_id: created.category_id, price: created.price, stock_quantity: created.stock_quantity, is_available: created.is_available });
        setFormData({ name: created.name, category_id: created.category_id, price: created.price, stock_quantity: created.stock_quantity, is_available: created.is_available });
      }
      loadProducts();
    } catch (err) {
      alert("Error saving product");
    }
    setLoading(false);
  };

  const handleDelete = async (id: number) => {
    if (confirm("Are you sure you want to delete this product?")) {
      try {
        await api.delete(`/api/products/${id}`);
        loadProducts();
      } catch (err) {
        alert("Error deleting product");
      }
    }
  };

  return (
    <div className="animate-fadeIn">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
        <div className="page-header" style={{ marginBottom: 0 }}>
          <h2>Products</h2>
          <p>Manage your restaurant items and pricing</p>
          <div style={{ fontSize: '0.75rem', color: 'var(--color-primary)', marginTop: '0.25rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <span style={{ display: 'inline-block', width: 6, height: 6, borderRadius: '50%', background: 'var(--color-primary)' }} />
            New products won't appear in AI recommendations until you regenerate rules.
          </div>
        </div>
        <div style={{ display: 'flex', gap: '0.75rem' }}>
          <button className="btn btn-outline" onClick={handleRegenerateRules} disabled={loading}>
            Regenerate AI Rules
          </button>
          <button className="btn btn-primary" onClick={() => {
            setEditingProduct(null);
            setFormData({ name: '', category_id: categories[0]?.id || 1, price: 0, stock_quantity: 0, is_available: true });
            setModalTab('details');
            setShowModal(true);
          }}>
            <Plus size={16} /> Add Product
          </button>
        </div>
      </div>

      {/* Filters */}
      <div className="card" style={{ marginBottom: '1.5rem', padding: '1rem 1.5rem' }}>
        <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
          <div style={{ position: 'relative', flex: 1 }}>
            <Search size={16} style={{ position: 'absolute', left: 12, top: 12, color: 'var(--color-text-muted)' }} />
            <input className="input" placeholder="Search by name, SKU, barcode..." value={search} onChange={(e) => setSearch(e.target.value)} style={{ paddingLeft: '2.25rem' }} />
          </div>
          <CustomSelect
            options={[
              { value: '', label: 'All Categories' },
              ...categories.map(c => ({ value: String(c.id), label: c.name }))
            ]}
            value={catFilter}
            onChange={setCatFilter}
            style={{ width: 180 }}
          />
          <CustomSelect
            options={[
              { value: '', label: 'All Stock Status' },
              { value: 'in', label: 'In Stock' },
              { value: 'low', label: 'Low Stock' },
              { value: 'out', label: 'Out of Stock' },
            ]}
            value={stockFilter}
            onChange={setStockFilter}
            style={{ width: 160 }}
          />
        </div>
      </div>

      {/* Products Table */}
      <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
        <table className="data-table">
          <thead>
            <tr>
              <th style={{ width: 40 }}><input type="checkbox" /></th>
              <th>Product</th>
              <th>Category</th>
              <th>Base Price</th>
              <th>Stock</th>
              <th>Stock Status</th>
              <th>Availability</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {filtered.slice(0, 20).map((p) => {
              const stock = getStockStatus(p.stock_quantity);
              return (
                <tr key={p.id}>
                  <td><input type="checkbox" /></td>
                  <td>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                      <div style={{ width: 40, height: 40, borderRadius: 8, background: '#F5F0EB', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                        <Image size={16} style={{ color: 'var(--color-text-muted)' }} />
                      </div>
                      <div>
                        <div style={{ fontWeight: 600 }}>{p.name}</div>
                        <div style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)' }}>SKU: {`PRD-${String(p.id).padStart(3, '0')}`}</div>
                      </div>
                    </div>
                  </td>
                  <td>{getCategory(p.category_id)}</td>
                  <td style={{ fontWeight: 600 }}>{p.price.toFixed(2)} DT</td>
                  <td>{p.stock_quantity}</td>
                  <td><span className={`badge ${stock.badge}`}>{stock.label}</span></td>
                  <td>
                    <label className="toggle-switch">
                      <input type="checkbox" checked={p.is_available} onChange={() => toggleAvailability(p.id, p.is_available)} />
                      <span className="slider" />
                    </label>
                  </td>
                  <td>
                    <div style={{ display: 'flex', gap: '0.25rem' }}>
                      <button className="btn btn-ghost btn-sm" style={{ padding: '0.25rem' }} onClick={() => {
                        setEditingProduct(p);
                        setFormData({ name: p.name, category_id: p.category_id, price: p.price, stock_quantity: p.stock_quantity, is_available: p.is_available });
                        setModalTab('details');
                        setShowModal(true);
                      }}>
                        <Edit size={14} />
                      </button>
                      <button className="btn btn-ghost btn-sm" style={{ padding: '0.25rem', color: 'var(--color-danger)' }} onClick={() => handleDelete(p.id)}>
                        <Trash2 size={14} />
                      </button>
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
        <div style={{ padding: '0.75rem 1.5rem', fontSize: '0.8125rem', color: 'var(--color-text-muted)', borderTop: '1px solid var(--color-border)' }}>
          Showing 1 to {Math.min(20, filtered.length)} of {filtered.length} products
        </div>
      </div>

      {/* Add / Edit Modal */}
      {showModal && (
        <div style={{ position: 'fixed', inset: 0, zIndex: 1000, background: 'rgba(0,0,0,0.5)', backdropFilter: 'blur(4px)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <div className="card animate-slideUp" style={{ width: '100%', maxWidth: 680, maxHeight: '90vh', overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
            {/* Header */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '1.25rem 1.5rem', borderBottom: '1px solid var(--color-border)' }}>
              <h3 style={{ fontSize: '1.25rem', fontWeight: 700 }}>{editingProduct ? 'Edit Product' : 'Add Product'}</h3>
              <button className="btn btn-ghost" style={{ padding: 4 }} onClick={() => setShowModal(false)}><X size={20} /></button>
            </div>

            {/* Tabs */}
            <div style={{ display: 'flex', borderBottom: '2px solid var(--color-border)', padding: '0 1.5rem' }}>
              <button
                type="button"
                onClick={() => setModalTab('details')}
                style={{
                  padding: '0.75rem 1.5rem', border: 'none', background: 'none', cursor: 'pointer',
                  fontWeight: 600, fontSize: '0.875rem',
                  color: modalTab === 'details' ? 'var(--color-primary)' : 'var(--color-text-muted)',
                  borderBottom: modalTab === 'details' ? '2px solid var(--color-primary)' : '2px solid transparent',
                  marginBottom: '-2px', transition: 'all 0.2s ease',
                }}
              >
                📋 Product Details
              </button>
              <button
                type="button"
                onClick={() => setModalTab('recipe')}
                style={{
                  padding: '0.75rem 1.5rem', border: 'none', background: 'none', cursor: 'pointer',
                  fontWeight: 600, fontSize: '0.875rem',
                  color: modalTab === 'recipe' ? 'var(--color-primary)' : 'var(--color-text-muted)',
                  borderBottom: modalTab === 'recipe' ? '2px solid var(--color-primary)' : '2px solid transparent',
                  marginBottom: '-2px', transition: 'all 0.2s ease',
                  display: 'flex', alignItems: 'center', gap: '0.375rem',
                }}
              >
                🧑‍🍳 Recipe
                {recipeLines.length > 0 && (
                  <span style={{ background: 'var(--color-primary)', color: 'white', borderRadius: 9999, padding: '0.1rem 0.5rem', fontSize: '0.6875rem', fontWeight: 700 }}>{recipeLines.length}</span>
                )}
              </button>
            </div>

            {/* Body */}
            <div style={{ flex: 1, overflow: 'auto', padding: '1.5rem' }}>
              {/* ── DETAILS TAB ── */}
              {modalTab === 'details' && (
                <form id="product-form" onSubmit={handleSave} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                  <div>
                    <label className="form-label" style={{ fontSize: '0.875rem', display: 'block', marginBottom: '0.25rem', fontWeight: 500 }}>Product Name</label>
                    <input className="input" required value={formData.name} onChange={e => setFormData({...formData, name: e.target.value})} style={{ width: '100%' }} />
                  </div>
                  
                  <div>
                    <label className="form-label" style={{ fontSize: '0.875rem', display: 'block', marginBottom: '0.25rem', fontWeight: 500 }}>Category</label>
                    <select className="input" style={{ width: '100%' }} value={formData.category_id} onChange={e => setFormData({...formData, category_id: Number(e.target.value)})}>
                      {categories.map(c => (
                        <option key={c.id} value={c.id}>{c.name}</option>
                      ))}
                    </select>
                  </div>

                  <div style={{ display: 'flex', gap: '1rem' }}>
                    <div style={{ flex: 1 }}>
                      <label className="form-label" style={{ fontSize: '0.875rem', display: 'block', marginBottom: '0.25rem', fontWeight: 500 }}>Price (DT)</label>
                      <input type="number" step="0.01" className="input" required value={formData.price} onChange={e => setFormData({...formData, price: parseFloat(e.target.value) || 0})} style={{ width: '100%' }} />
                    </div>
                    <div style={{ flex: 1 }}>
                      <label className="form-label" style={{ fontSize: '0.875rem', display: 'block', marginBottom: '0.25rem', fontWeight: 500 }}>Initial Stock</label>
                      <input type="number" className="input" required value={formData.stock_quantity} onChange={e => setFormData({...formData, stock_quantity: parseInt(e.target.value) || 0})} style={{ width: '100%' }} />
                    </div>
                  </div>

                  <div>
                    <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer', marginTop: '0.5rem' }}>
                      <input type="checkbox" checked={formData.is_available} onChange={e => setFormData({...formData, is_available: e.target.checked})} />
                      <span style={{ fontSize: '0.875rem', fontWeight: 500 }}>Product is available for sale</span>
                    </label>
                  </div>
                </form>
              )}

              {/* ── RECIPE TAB ── */}
              {modalTab === 'recipe' && (
                <div>
                  {!editingProduct ? (
                    <div style={{ padding: '3rem 2rem', textAlign: 'center', background: 'var(--color-bg-page)', borderRadius: '12px' }}>
                      <div style={{ fontSize: '2rem', marginBottom: '0.75rem' }}>📦</div>
                      <p style={{ fontWeight: 600, marginBottom: '0.25rem' }}>Save the product first</p>
                      <p style={{ fontSize: '0.8125rem', color: 'var(--color-text-muted)' }}>Create the product on the Details tab, then come back here to build its recipe.</p>
                    </div>
                  ) : (
                    <div>
                      {/* Recipe header info */}
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                        <div>
                          <h4 style={{ fontSize: '1rem', fontWeight: 700 }}>Ingredients for "{formData.name}"</h4>
                          <p style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)' }}>
                            {recipeLines.length} ingredient{recipeLines.length !== 1 ? 's' : ''} linked • Quantities per 1 serving
                          </p>
                        </div>
                      </div>

                      {/* Current recipe lines */}
                      {recipeLines.length > 0 ? (
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', marginBottom: '1.5rem' }}>
                          {recipeLines.map((line: any, idx: number) => (
                            <div key={line.ingredient_id} style={{
                              display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                              background: idx % 2 === 0 ? 'var(--color-bg-page)' : 'var(--color-bg-card)',
                              padding: '0.625rem 0.875rem', borderRadius: '8px',
                              border: '1px solid var(--color-border-light)',
                            }}>
                              <div style={{ display: 'flex', alignItems: 'center', gap: '0.625rem' }}>
                                <span style={{
                                  width: 28, height: 28, borderRadius: '50%',
                                  background: 'rgba(220,53,69,0.1)', color: 'var(--color-primary)',
                                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                                  fontSize: '0.6875rem', fontWeight: 700, flexShrink: 0,
                                }}>{idx + 1}</span>
                                <span style={{ fontSize: '0.875rem', fontWeight: 600 }}>{line.ingredient_name}</span>
                              </div>
                              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                                {editingQty && editingQty.ingredientId === line.ingredient_id ? (
                                  <>
                                    <input type="number" step="0.1" className="input"
                                      style={{ width: 80, padding: '0.25rem 0.4rem', fontSize: '0.8125rem', textAlign: 'center' }}
                                      value={editingQty.value}
                                      onChange={e => setEditingQty({ ...editingQty, value: e.target.value })}
                                      onKeyDown={e => {
                                        if (e.key === 'Enter') { e.preventDefault(); handleUpdateRecipeLine(line.ingredient_id, editingQty.value); }
                                        if (e.key === 'Escape') setEditingQty(null);
                                      }}
                                      autoFocus
                                    />
                                    <span style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)', minWidth: 20 }}>{line.unit}</span>
                                    <button type="button" style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--color-success)', fontSize: '1rem', padding: 2 }}
                                      onClick={() => handleUpdateRecipeLine(line.ingredient_id, editingQty.value)}>✓</button>
                                    <button type="button" style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--color-text-muted)', fontSize: '1rem', padding: 2 }}
                                      onClick={() => setEditingQty(null)}>✕</button>
                                  </>
                                ) : (
                                  <>
                                    <span
                                      style={{
                                        fontSize: '0.875rem', fontWeight: 600, cursor: 'pointer',
                                        padding: '0.2rem 0.5rem', borderRadius: '4px',
                                        background: 'rgba(220,53,69,0.08)', color: 'var(--color-primary)',
                                      }}
                                      onClick={() => setEditingQty({ ingredientId: line.ingredient_id, value: String(line.quantity_needed) })}
                                      title="Click to edit quantity"
                                    >
                                      {line.quantity_needed} {line.unit}
                                    </span>
                                    <button type="button" style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--color-danger)', padding: 2 }}
                                      onClick={() => handleDeleteRecipeLine(line.ingredient_id)}>
                                      <Trash2 size={14} />
                                    </button>
                                  </>
                                )}
                              </div>
                            </div>
                          ))}
                        </div>
                      ) : (
                        <div style={{
                          padding: '2rem', textAlign: 'center', marginBottom: '1.5rem',
                          background: 'var(--color-bg-page)', borderRadius: '10px', border: '1px dashed var(--color-border)',
                        }}>
                          <p style={{ fontSize: '0.875rem', color: 'var(--color-text-muted)', fontWeight: 500 }}>No ingredients linked yet.</p>
                          <p style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)' }}>Add ingredients below to build this dish's recipe.</p>
                        </div>
                      )}

                      {/* Add new ingredient */}
                      <div style={{
                        padding: '1rem', background: 'var(--color-bg-page)', borderRadius: '10px',
                        border: '1px solid var(--color-border)',
                      }}>
                        <div style={{ fontSize: '0.8125rem', fontWeight: 600, marginBottom: '0.75rem', color: 'var(--color-text-secondary)' }}>Add Ingredient</div>
                        <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'flex-end' }}>
                          <div style={{ flex: 3 }}>
                            <label className="form-label" style={{ fontSize: '0.6875rem', textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--color-text-muted)', marginBottom: '0.25rem', display: 'block' }}>Ingredient</label>
                            <select className="input" style={{ width: '100%', padding: '0.5rem' }} value={newRecipeLine.ingredient_id} onChange={e => setNewRecipeLine({...newRecipeLine, ingredient_id: e.target.value})}>
                              <option value="">Select ingredient...</option>
                              {ingredients
                                .filter((ing: any) => !recipeLines.some((rl: any) => rl.ingredient_id === ing.id))
                                .map((ing: any) => (
                                  <option key={ing.id} value={ing.id}>{ing.name} ({ing.unit})</option>
                                ))
                              }
                            </select>
                          </div>
                          <div style={{ flex: 1 }}>
                            <label className="form-label" style={{ fontSize: '0.6875rem', textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--color-text-muted)', marginBottom: '0.25rem', display: 'block' }}>Qty</label>
                            <input type="number" step="0.1" className="input" placeholder="e.g. 150"
                              style={{ width: '100%', padding: '0.5rem' }}
                              value={newRecipeLine.quantity_needed}
                              onChange={e => setNewRecipeLine({...newRecipeLine, quantity_needed: e.target.value})}
                              onKeyDown={e => { if (e.key === 'Enter') { e.preventDefault(); handleAddRecipeLine(); } }}
                            />
                          </div>
                          <button type="button" className="btn btn-primary" style={{ padding: '0.5rem 1rem', whiteSpace: 'nowrap' }}
                            onClick={handleAddRecipeLine}
                            disabled={!newRecipeLine.ingredient_id || !newRecipeLine.quantity_needed}
                          >
                            <Plus size={14} /> Add
                          </button>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* Footer */}
            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.5rem', padding: '1rem 1.5rem', borderTop: '1px solid var(--color-border)' }}>
              <button type="button" className="btn btn-ghost" onClick={() => setShowModal(false)}>Cancel</button>
              {modalTab === 'details' && (
                <button type="submit" form="product-form" className="btn btn-primary" disabled={loading}>{editingProduct ? 'Save Changes' : 'Create Product'}</button>
              )}
              {modalTab === 'recipe' && editingProduct && (
                <button type="button" className="btn btn-primary" onClick={() => setShowModal(false)}>Done</button>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
