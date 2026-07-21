import React, { useState } from 'react';
import { Search, Plus, Edit, Trash2, X } from 'lucide-react';
import CustomSelect from '../components/CustomSelect';

interface InventoryItem {
  id: number;
  name: string;
  sku: string;
  category: string;
  supplier: string;
  current_stock: string;
  min_threshold: string;
  last_updated: string;
  status: 'healthy' | 'low' | 'critical';
}

const mockItems: InventoryItem[] = [
  { id: 1, name: 'Extra Virgin Olive Oil', sku: 'OIL-001', category: 'Oils & Fats', supplier: 'Mediterranean Imports Co.', current_stock: '45 liters', min_threshold: '50 liters', last_updated: '2/15/2026', status: 'low' },
  { id: 2, name: 'Organic Tomatoes', sku: 'VEG-102', category: 'Vegetables', supplier: 'Fresh Farm Suppliers', current_stock: '180 kg', min_threshold: '100 kg', last_updated: '2/17/2026', status: 'healthy' },
  { id: 3, name: 'Mozzarella Cheese', sku: 'DAI-305', category: 'Dairy', supplier: 'Italian Cheese Imports', current_stock: '25 kg', min_threshold: '30 kg', last_updated: '2/16/2026', status: 'low' },
  { id: 4, name: 'Premium Ground Beef', sku: 'MEA-401', category: 'Meat', supplier: 'Quality Meats Ltd.', current_stock: '8 kg', min_threshold: '25 kg', last_updated: '2/17/2026', status: 'critical' },
  { id: 5, name: 'Fresh Basil', sku: 'HRB-501', category: 'Herbs & Spices', supplier: 'Fresh Farm Suppliers', current_stock: '95 bunches', min_threshold: '50 bunches', last_updated: '2/17/2026', status: 'healthy' },
  { id: 6, name: 'Arborio Rice', sku: 'GRA-601', category: 'Grains', supplier: 'Mediterranean Imports Co.', current_stock: '120 kg', min_threshold: '80 kg', last_updated: '2/14/2026', status: 'healthy' },
  { id: 7, name: 'Sea Salt', sku: 'SPN-701', category: 'Herbs & Spices', supplier: 'Global Spices Inc.', current_stock: '60 kg', min_threshold: '40 kg', last_updated: '2/10/2026', status: 'healthy' },
];

export default function InventoryPage() {
  const [items, setItems] = useState<InventoryItem[]>(mockItems);
  const [search, setSearch] = useState('');
  const [catFilter, setCatFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');

  const [showModal, setShowModal] = useState(false);
  const [editingItem, setEditingItem] = useState<InventoryItem | null>(null);
  const [formData, setFormData] = useState<Omit<InventoryItem, 'id' | 'last_updated'>>({
    name: '', sku: '', category: '', supplier: '', current_stock: '', min_threshold: '', status: 'healthy'
  });

  const filtered = items.filter(i => {
    if (search && !i.name.toLowerCase().includes(search.toLowerCase()) && !i.sku.toLowerCase().includes(search.toLowerCase())) return false;
    if (catFilter && i.category !== catFilter) return false;
    if (statusFilter && i.status !== statusFilter) return false;
    return true;
  });

  const categories = [...new Set(items.map(i => i.category))];

  const handleSave = (e: React.FormEvent) => {
    e.preventDefault();
    const today = new Date().toLocaleDateString('en-US');
    if (editingItem) {
      setItems(items.map(i => i.id === editingItem.id ? { ...formData, id: editingItem.id, last_updated: today } : i));
    } else {
      const newId = items.length > 0 ? Math.max(...items.map(i => i.id)) + 1 : 1;
      setItems([...items, { ...formData, id: newId, last_updated: today }]);
    }
    setShowModal(false);
  };

  const handleDelete = (id: number) => {
    if (confirm('Are you sure you want to delete this inventory item?')) {
      setItems(items.filter(i => i.id !== id));
    }
  };

  return (
    <div className="animate-fadeIn">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
        <div className="page-header" style={{ marginBottom: 0 }}>
          <h2>Inventory Management</h2>
          <p>Manage raw materials and stock items</p>
        </div>
        <button className="btn btn-primary" onClick={() => {
          setEditingItem(null);
          setFormData({ name: '', sku: '', category: '', supplier: '', current_stock: '', min_threshold: '', status: 'healthy' });
          setShowModal(true);
        }}>
          <Plus size={16} /> Add Inventory Item
        </button>
      </div>

      {/* Filters */}
      <div className="card" style={{ marginBottom: '1.5rem', padding: '1rem 1.5rem' }}>
        <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
          <div style={{ position: 'relative', flex: 1 }}>
            <Search size={16} style={{ position: 'absolute', left: 12, top: 12, color: 'var(--color-text-muted)' }} />
            <input className="input" placeholder="Search by name or SKU..." value={search} onChange={(e) => setSearch(e.target.value)} style={{ paddingLeft: '2.25rem' }} />
          </div>
          <CustomSelect
            options={[
              { value: '', label: 'All Categories' },
              ...categories.map(c => ({ value: c, label: c }))
            ]}
            value={catFilter}
            onChange={setCatFilter}
            style={{ width: 180 }}
          />
          <CustomSelect
            options={[
              { value: '', label: 'All Status' },
              { value: 'healthy', label: 'Healthy' },
              { value: 'low', label: 'Low Stock' },
              { value: 'critical', label: 'Critical' },
            ]}
            value={statusFilter}
            onChange={setStatusFilter}
            style={{ width: 150 }}
          />
        </div>
      </div>

      {/* Table */}
      <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
        <table className="data-table">
          <thead>
            <tr>
              <th>Item Name</th>
              <th>SKU</th>
              <th>Category</th>
              <th>Supplier</th>
              <th>Current Stock</th>
              <th>Min. Threshold</th>
              <th>Last Updated</th>
              <th>Status</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((item) => (
              <tr key={item.id}>
                <td style={{ fontWeight: 600 }}>{item.name}</td>
                <td style={{ color: 'var(--color-text-muted)' }}>{item.sku}</td>
                <td>{item.category}</td>
                <td>{item.supplier}</td>
                <td style={{ fontWeight: 600 }}>{item.current_stock}</td>
                <td>{item.min_threshold}</td>
                <td>{item.last_updated}</td>
                <td>
                  <span className={`badge ${item.status === 'healthy' ? 'badge-success' : item.status === 'low' ? 'badge-warning' : 'badge-danger'}`}>
                    {item.status === 'healthy' ? 'Healthy' : item.status === 'low' ? 'Low Stock' : 'Critical'}
                  </span>
                </td>
                <td>
                  <div style={{ display: 'flex', gap: '0.25rem' }}>
                    <button className="btn btn-ghost btn-sm" style={{ padding: '0.25rem' }} onClick={() => {
                      setEditingItem(item);
                      setFormData({
                        name: item.name, sku: item.sku, category: item.category, supplier: item.supplier, 
                        current_stock: item.current_stock, min_threshold: item.min_threshold, status: item.status
                      });
                      setShowModal(true);
                    }}>
                      <Edit size={14} />
                    </button>
                    <button className="btn btn-ghost btn-sm" style={{ padding: '0.25rem', color: 'var(--color-danger)' }} onClick={() => handleDelete(item.id)}>
                      <Trash2 size={14} />
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Modal */}
      {showModal && (
        <div style={{ position: 'fixed', inset: 0, zIndex: 1000, background: 'rgba(0,0,0,0.5)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <div className="card" style={{ width: '100%', maxWidth: 500 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '1rem' }}>
              <h3 style={{ fontSize: '1.25rem', fontWeight: 600 }}>{editingItem ? 'Edit Inventory Item' : 'Add Inventory Item'}</h3>
              <button className="btn btn-ghost" style={{ padding: 4 }} onClick={() => setShowModal(false)}><X size={20} /></button>
            </div>
            <form onSubmit={handleSave} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              <div style={{ display: 'flex', gap: '1rem' }}>
                <div style={{ flex: 1 }}>
                  <label className="form-label" style={{ fontSize: '0.875rem', display: 'block', marginBottom: '0.25rem', fontWeight: 500 }}>Item Name</label>
                  <input className="input" required value={formData.name} onChange={e => setFormData({...formData, name: e.target.value})} style={{ width: '100%' }} />
                </div>
                <div style={{ flex: 1 }}>
                  <label className="form-label" style={{ fontSize: '0.875rem', display: 'block', marginBottom: '0.25rem', fontWeight: 500 }}>SKU</label>
                  <input className="input" required value={formData.sku} onChange={e => setFormData({...formData, sku: e.target.value})} style={{ width: '100%' }} />
                </div>
              </div>
              
              <div style={{ display: 'flex', gap: '1rem' }}>
                <div style={{ flex: 1 }}>
                  <label className="form-label" style={{ fontSize: '0.875rem', display: 'block', marginBottom: '0.25rem', fontWeight: 500 }}>Category</label>
                  <input className="input" required value={formData.category} onChange={e => setFormData({...formData, category: e.target.value})} style={{ width: '100%' }} />
                </div>
                <div style={{ flex: 1 }}>
                  <label className="form-label" style={{ fontSize: '0.875rem', display: 'block', marginBottom: '0.25rem', fontWeight: 500 }}>Supplier</label>
                  <input className="input" required value={formData.supplier} onChange={e => setFormData({...formData, supplier: e.target.value})} style={{ width: '100%' }} />
                </div>
              </div>

              <div style={{ display: 'flex', gap: '1rem' }}>
                <div style={{ flex: 1 }}>
                  <label className="form-label" style={{ fontSize: '0.875rem', display: 'block', marginBottom: '0.25rem', fontWeight: 500 }}>Current Stock (e.g. "45 liters")</label>
                  <input className="input" required value={formData.current_stock} onChange={e => setFormData({...formData, current_stock: e.target.value})} style={{ width: '100%' }} />
                </div>
                <div style={{ flex: 1 }}>
                  <label className="form-label" style={{ fontSize: '0.875rem', display: 'block', marginBottom: '0.25rem', fontWeight: 500 }}>Min Threshold</label>
                  <input className="input" required value={formData.min_threshold} onChange={e => setFormData({...formData, min_threshold: e.target.value})} style={{ width: '100%' }} />
                </div>
              </div>

              <div>
                <label className="form-label" style={{ fontSize: '0.875rem', display: 'block', marginBottom: '0.25rem', fontWeight: 500 }}>Status</label>
                <CustomSelect
                  options={[
                    { value: 'healthy', label: 'Healthy' },
                    { value: 'low', label: 'Low Stock' },
                    { value: 'critical', label: 'Critical' },
                  ]}
                  value={formData.status}
                  onChange={(v) => setFormData({...formData, status: v as 'healthy' | 'low' | 'critical'})}
                  style={{ width: '100%' }}
                />
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.5rem', marginTop: '1rem' }}>
                <button type="button" className="btn btn-ghost" onClick={() => setShowModal(false)}>Cancel</button>
                <button type="submit" className="btn btn-primary">{editingItem ? 'Save Changes' : 'Create Item'}</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
