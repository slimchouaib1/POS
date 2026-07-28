import React, { useEffect, useState } from 'react';
import { Plus, Edit, Trash2, X, RefreshCw } from 'lucide-react';
import api from '../api';

interface Supplier {
  id: number;
  name: string;
  contact_name: string;
  phone: string;
  email: string;
  notes: string;
  created_at: string | null;
  is_active: boolean;
}

interface SupplierForm {
  name: string;
  contact_name: string;
  phone: string;
  email: string;
  notes: string;
}

const emptyForm: SupplierForm = {
  name: '',
  contact_name: '',
  phone: '',
  email: '',
  notes: '',
};

export default function SuppliersPage() {
  const [suppliers, setSuppliers] = useState<Supplier[]>([]);
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState('');
  const [showModal, setShowModal] = useState(false);
  const [editingSupplier, setEditingSupplier] = useState<Supplier | null>(null);
  const [formData, setFormData] = useState<SupplierForm>(emptyForm);

  const loadSuppliers = () => {
    setLoading(true);
    api.get('/api/suppliers')
      .then((res) => setSuppliers(res.data))
      .catch((err) => setMessage(err.response?.data?.detail || 'Failed to load suppliers.'))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    loadSuppliers();
  }, []);

  const openCreate = () => {
    setEditingSupplier(null);
    setFormData(emptyForm);
    setShowModal(true);
    setMessage('');
  };

  const openEdit = (supplier: Supplier) => {
    setEditingSupplier(supplier);
    setFormData({
      name: supplier.name,
      contact_name: supplier.contact_name || '',
      phone: supplier.phone || '',
      email: supplier.email || '',
      notes: supplier.notes || '',
    });
    setShowModal(true);
    setMessage('');
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      if (editingSupplier) {
        await api.put(`/api/suppliers/${editingSupplier.id}`, formData);
        setMessage(`Updated supplier ${formData.name}.`);
      } else {
        await api.post('/api/suppliers', formData);
        setMessage(`Created supplier ${formData.name}.`);
      }
      setShowModal(false);
      loadSuppliers();
    } catch (err: any) {
      setMessage(err.response?.data?.detail || 'Failed to save supplier.');
    }
  };

  const handleDelete = async (supplier: Supplier) => {
    if (!confirm(`Deactivate supplier ${supplier.name}?`)) return;
    try {
      await api.delete(`/api/suppliers/${supplier.id}`);
      setMessage(`Deactivated supplier ${supplier.name}.`);
      loadSuppliers();
    } catch (err: any) {
      setMessage(err.response?.data?.detail || 'Failed to deactivate supplier.');
    }
  };

  return (
    <div className="animate-fadeIn">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
        <div className="page-header" style={{ marginBottom: 0 }}>
          <h2>Suppliers Management</h2>
          <p>{suppliers.length} active suppliers persisted in the live database</p>
        </div>
        <div style={{ display: 'flex', gap: '0.5rem' }}>
          <button className="btn btn-outline" onClick={loadSuppliers}>
            <RefreshCw size={16} /> Refresh
          </button>
          <button className="btn btn-primary" onClick={openCreate}>
            <Plus size={16} /> Add Supplier
          </button>
        </div>
      </div>

      {message && (
        <div className="card" style={{ padding: '0.75rem 1rem', marginBottom: '1rem', color: 'var(--color-text-secondary)' }}>
          {message}
        </div>
      )}

      <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
        <table className="data-table">
          <thead>
            <tr>
              <th>Supplier Name</th>
              <th>Contact Person</th>
              <th>Phone</th>
              <th>Email</th>
              <th>Notes</th>
              <th>Status</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td colSpan={7} style={{ textAlign: 'center', padding: '2rem', color: 'var(--color-text-muted)' }}>Loading suppliers...</td></tr>
            ) : suppliers.length > 0 ? suppliers.map((supplier) => (
              <tr key={supplier.id}>
                <td style={{ fontWeight: 600 }}>{supplier.name}</td>
                <td>{supplier.contact_name || '-'}</td>
                <td style={{ color: 'var(--color-text-secondary)' }}>{supplier.phone || '-'}</td>
                <td style={{ color: 'var(--color-text-secondary)' }}>{supplier.email || '-'}</td>
                <td style={{ color: 'var(--color-text-secondary)', maxWidth: 260, whiteSpace: 'normal' }}>{supplier.notes || '-'}</td>
                <td><span className="badge badge-success">Active</span></td>
                <td>
                  <div style={{ display: 'flex', gap: '0.25rem' }}>
                    <button className="btn btn-ghost btn-sm" style={{ padding: '0.25rem' }} onClick={() => openEdit(supplier)}>
                      <Edit size={14} />
                    </button>
                    <button className="btn btn-ghost btn-sm" style={{ padding: '0.25rem', color: 'var(--color-danger)' }} onClick={() => handleDelete(supplier)}>
                      <Trash2 size={14} />
                    </button>
                  </div>
                </td>
              </tr>
            )) : (
              <tr><td colSpan={7} style={{ textAlign: 'center', padding: '2rem', color: 'var(--color-text-muted)' }}>No active suppliers found.</td></tr>
            )}
          </tbody>
        </table>
      </div>

      {showModal && (
        <div style={{ position: 'fixed', inset: 0, zIndex: 1000, background: 'rgba(0,0,0,0.5)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <div className="card" style={{ width: '100%', maxWidth: 520 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '1rem' }}>
              <h3 style={{ fontSize: '1.25rem', fontWeight: 600 }}>{editingSupplier ? 'Edit Supplier' : 'Add Supplier'}</h3>
              <button className="btn btn-ghost" style={{ padding: 4 }} onClick={() => setShowModal(false)}><X size={20} /></button>
            </div>
            <form onSubmit={handleSave} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              <div>
                <label className="form-label" style={{ fontSize: '0.875rem', display: 'block', marginBottom: '0.25rem', fontWeight: 500 }}>Supplier Name</label>
                <input className="input" required value={formData.name} onChange={e => setFormData({ ...formData, name: e.target.value })} style={{ width: '100%' }} />
              </div>
              <div>
                <label className="form-label" style={{ fontSize: '0.875rem', display: 'block', marginBottom: '0.25rem', fontWeight: 500 }}>Contact Person</label>
                <input className="input" value={formData.contact_name} onChange={e => setFormData({ ...formData, contact_name: e.target.value })} style={{ width: '100%' }} />
              </div>
              <div style={{ display: 'flex', gap: '1rem' }}>
                <div style={{ flex: 1 }}>
                  <label className="form-label" style={{ fontSize: '0.875rem', display: 'block', marginBottom: '0.25rem', fontWeight: 500 }}>Phone</label>
                  <input className="input" value={formData.phone} onChange={e => setFormData({ ...formData, phone: e.target.value })} style={{ width: '100%' }} />
                </div>
                <div style={{ flex: 1 }}>
                  <label className="form-label" style={{ fontSize: '0.875rem', display: 'block', marginBottom: '0.25rem', fontWeight: 500 }}>Email</label>
                  <input type="email" className="input" value={formData.email} onChange={e => setFormData({ ...formData, email: e.target.value })} style={{ width: '100%' }} />
                </div>
              </div>
              <div>
                <label className="form-label" style={{ fontSize: '0.875rem', display: 'block', marginBottom: '0.25rem', fontWeight: 500 }}>Notes</label>
                <textarea className="input" value={formData.notes} onChange={e => setFormData({ ...formData, notes: e.target.value })} style={{ width: '100%', minHeight: 90 }} />
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
