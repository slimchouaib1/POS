import React, { useState } from 'react';
import { Plus, Edit, Trash2, X } from 'lucide-react';
import CustomSelect from '../components/CustomSelect';

interface Supplier {
  id: number;
  name: string;
  contact: string;
  phone: string;
  email: string;
  activePO: number | null;
  totalOrders: number;
  status: 'Active' | 'Inactive';
}

const mockSuppliers: Supplier[] = [
  { id: 1, name: 'Mediterranean Imports Co.', contact: 'Marco Rossi', phone: '+1 (555) 234-5678', email: 'marco@medimports.com', activePO: 2, totalOrders: 87, status: 'Active' },
  { id: 2, name: 'Fresh Farm Suppliers', contact: 'Emily Green', phone: '+1 (555) 876-5432', email: 'emily@freshfarm.com', activePO: 1, totalOrders: 124, status: 'Active' },
  { id: 3, name: 'Italian Cheese Imports', contact: 'Giovanni Bianchi', phone: '+1 (555) 345-6789', email: 'giovanni@italiancheese.com', activePO: null, totalOrders: 52, status: 'Active' },
  { id: 4, name: 'Quality Meats Ltd.', contact: 'Robert Brown', phone: '+1 (555) 456-7890', email: 'robert@qualitymeats.com', activePO: 1, totalOrders: 98, status: 'Active' },
  { id: 5, name: 'Ocean Fresh Supplies', contact: 'Lisa Martinez', phone: '+1 (555) 567-8901', email: 'lisa@oceanfresh.com', activePO: null, totalOrders: 64, status: 'Active' },
  { id: 6, name: 'Global Spices Inc.', contact: 'David Chen', phone: '+1 (555) 678-9012', email: 'david@globalspices.com', activePO: null, totalOrders: 45, status: 'Active' },
];

export default function SuppliersPage() {
  const [suppliers, setSuppliers] = useState<Supplier[]>(mockSuppliers);

  const [showModal, setShowModal] = useState(false);
  const [editingSupplier, setEditingSupplier] = useState<Supplier | null>(null);
  const [formData, setFormData] = useState<Omit<Supplier, 'id' | 'activePO' | 'totalOrders'>>({
    name: '', contact: '', phone: '', email: '', status: 'Active'
  });

  const handleSave = (e: React.FormEvent) => {
    e.preventDefault();
    if (editingSupplier) {
      setSuppliers(suppliers.map(s => s.id === editingSupplier.id ? { ...s, ...formData } : s));
    } else {
      const newId = suppliers.length > 0 ? Math.max(...suppliers.map(s => s.id)) + 1 : 1;
      setSuppliers([...suppliers, { ...formData, id: newId, activePO: 0, totalOrders: 0 }]);
    }
    setShowModal(false);
  };

  const handleDelete = (id: number) => {
    if (confirm('Are you sure you want to delete this supplier?')) {
      setSuppliers(suppliers.filter(s => s.id !== id));
    }
  };

  return (
    <div className="animate-fadeIn">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
        <div className="page-header" style={{ marginBottom: 0 }}>
          <h2>Suppliers Management</h2>
          <p>Manage vendor relationships and performance</p>
        </div>
        <button className="btn btn-primary" onClick={() => {
          setEditingSupplier(null);
          setFormData({ name: '', contact: '', phone: '', email: '', status: 'Active' });
          setShowModal(true);
        }}>
          <Plus size={16} /> Add Supplier
        </button>
      </div>

      <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
        <table className="data-table">
          <thead>
            <tr>
              <th>Supplier Name</th>
              <th>Contact Person</th>
              <th>Phone</th>
              <th>Email</th>
              <th>Active PO</th>
              <th>Total Orders</th>
              <th>Status</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {suppliers.map((s) => (
              <tr key={s.id}>
                <td style={{ fontWeight: 600 }}>{s.name}</td>
                <td>{s.contact}</td>
                <td style={{ color: 'var(--color-text-secondary)' }}>{s.phone}</td>
                <td style={{ color: 'var(--color-text-secondary)' }}>{s.email}</td>
                <td style={{ fontWeight: 600, color: s.activePO ? 'var(--color-primary)' : 'var(--color-text-muted)' }}>{s.activePO || '—'}</td>
                <td style={{ fontWeight: 600 }}>{s.totalOrders}</td>
                <td><span className={`badge ${s.status === 'Active' ? 'badge-success' : 'badge-danger'}`}>{s.status}</span></td>
                <td>
                  <div style={{ display: 'flex', gap: '0.25rem' }}>
                    <button className="btn btn-ghost btn-sm" style={{ padding: '0.25rem' }} onClick={() => {
                      setEditingSupplier(s);
                      setFormData({ name: s.name, contact: s.contact, phone: s.phone, email: s.email, status: s.status });
                      setShowModal(true);
                    }}>
                      <Edit size={14} />
                    </button>
                    <button className="btn btn-ghost btn-sm" style={{ padding: '0.25rem', color: 'var(--color-danger)' }} onClick={() => handleDelete(s.id)}>
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
          <div className="card" style={{ width: '100%', maxWidth: 450 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '1rem' }}>
              <h3 style={{ fontSize: '1.25rem', fontWeight: 600 }}>{editingSupplier ? 'Edit Supplier' : 'Add Supplier'}</h3>
              <button className="btn btn-ghost" style={{ padding: 4 }} onClick={() => setShowModal(false)}><X size={20} /></button>
            </div>
            <form onSubmit={handleSave} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              <div>
                <label className="form-label" style={{ fontSize: '0.875rem', display: 'block', marginBottom: '0.25rem', fontWeight: 500 }}>Supplier Name</label>
                <input className="input" required value={formData.name} onChange={e => setFormData({...formData, name: e.target.value})} style={{ width: '100%' }} />
              </div>
              <div>
                <label className="form-label" style={{ fontSize: '0.875rem', display: 'block', marginBottom: '0.25rem', fontWeight: 500 }}>Contact Person</label>
                <input className="input" required value={formData.contact} onChange={e => setFormData({...formData, contact: e.target.value})} style={{ width: '100%' }} />
              </div>
              <div style={{ display: 'flex', gap: '1rem' }}>
                <div style={{ flex: 1 }}>
                  <label className="form-label" style={{ fontSize: '0.875rem', display: 'block', marginBottom: '0.25rem', fontWeight: 500 }}>Phone</label>
                  <input className="input" required value={formData.phone} onChange={e => setFormData({...formData, phone: e.target.value})} style={{ width: '100%' }} />
                </div>
                <div style={{ flex: 1 }}>
                  <label className="form-label" style={{ fontSize: '0.875rem', display: 'block', marginBottom: '0.25rem', fontWeight: 500 }}>Email</label>
                  <input type="email" className="input" required value={formData.email} onChange={e => setFormData({...formData, email: e.target.value})} style={{ width: '100%' }} />
                </div>
              </div>
              <div>
                <label className="form-label" style={{ fontSize: '0.875rem', display: 'block', marginBottom: '0.25rem', fontWeight: 500 }}>Status</label>
                <CustomSelect
                  options={[
                    { value: 'Active', label: 'Active' },
                    { value: 'Inactive', label: 'Inactive' },
                  ]}
                  value={formData.status}
                  onChange={(v) => setFormData({...formData, status: v as 'Active' | 'Inactive'})}
                  style={{ width: '100%' }}
                />
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.5rem', marginTop: '1rem' }}>
                <button type="button" className="btn btn-ghost" onClick={() => setShowModal(false)}>Cancel</button>
                <button type="submit" className="btn btn-primary">{editingSupplier ? 'Save Changes' : 'Create Supplier'}</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
