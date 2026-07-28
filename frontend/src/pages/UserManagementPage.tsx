import React, { useEffect, useState } from 'react';
import api from '../api';
import { Search, Plus, Edit, Trash2, X } from 'lucide-react';
import CustomSelect from '../components/CustomSelect';

interface UserRow {
  id: number;
  username: string;
  full_name: string;
  email: string;
  role: string;
  is_active: boolean;
}

export default function UserManagementPage() {
  const [users, setUsers] = useState<UserRow[]>([]);
  const [search, setSearch] = useState('');
  const [roleFilter, setRoleFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');

  const [showModal, setShowModal] = useState(false);
  const [editingUser, setEditingUser] = useState<UserRow | null>(null);
  const [formData, setFormData] = useState({ username: '', full_name: '', email: '', role: 'cashier', password: '' });
  const [loading, setLoading] = useState(false);

  const loadUsers = () => {
    api.get('/api/users').then(r => setUsers(r.data)).catch(console.error);
  };

  useEffect(() => {
    loadUsers();
  }, []);

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      if (editingUser) {
        await api.put(`/api/users/${editingUser.id}`, {
          full_name: formData.full_name,
          email: formData.email,
          role: formData.role
        });
      } else {
        await api.post('/api/auth/register', formData);
      }
      setShowModal(false);
      loadUsers();
    } catch (err) {
      alert("An error occurred while saving the user.");
    }
    setLoading(false);
  };

  const handleDelete = async (id: number) => {
    if (confirm("Are you sure you want to deactivate this user?")) {
      try {
        await api.delete(`/api/users/${id}`);
        loadUsers();
      } catch (err) {
        alert("Error deactivating user.");
      }
    }
  };

  const roleColors: Record<string, string> = {
    admin: '#DC3545', manager: '#F4845F', cashier: '#17A2B8', stock_manager: '#28A745',
  };
  const roleLabels: Record<string, string> = {
    admin: 'Admin', manager: 'Manager', cashier: 'Cashier', stock_manager: 'Stock Manager',
  };

  const getInitials = (name: string) => name.split(' ').map(n => n[0]).join('').slice(0, 2);
  const avatarColors = ['#DC3545', '#F4845F', '#28A745', '#17A2B8', '#6366F1', '#EC4899'];

  const filtered = users.filter(u => {
    if (search && !u.full_name.toLowerCase().includes(search.toLowerCase()) && !u.email.toLowerCase().includes(search.toLowerCase())) return false;
    if (roleFilter && u.role !== roleFilter) return false;
    if (statusFilter === 'active' && !u.is_active) return false;
    if (statusFilter === 'inactive' && u.is_active) return false;
    return true;
  });

  return (
    <div className="animate-fadeIn">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
        <div className="page-header" style={{ marginBottom: 0 }}>
          <h2>Users</h2>
          <p>Manage staff access and permissions</p>
        </div>
        <button className="btn btn-primary" onClick={() => {
          setEditingUser(null);
          setFormData({ username: '', full_name: '', email: '', role: 'cashier', password: '' });
          setShowModal(true);
        }}>
          <Plus size={16} /> Add User
        </button>
      </div>

      {/* Search & Filters */}
      <div className="card" style={{ marginBottom: '1.5rem', padding: '1rem 1.5rem' }}>
        <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
          <div style={{ position: 'relative', flex: 1 }}>
            <Search size={16} style={{ position: 'absolute', left: 12, top: 12, color: 'var(--color-text-muted)' }} />
            <input className="input" placeholder="Search by name, email, or role..." value={search} onChange={(e) => setSearch(e.target.value)} style={{ paddingLeft: '2.25rem' }} />
          </div>
          <CustomSelect
            options={[
              { value: '', label: 'All Roles' },
              { value: 'admin', label: 'Admin' },
              { value: 'manager', label: 'Manager' },
              { value: 'cashier', label: 'Cashier' },
              { value: 'stock_manager', label: 'Stock Manager' },
            ]}
            value={roleFilter}
            onChange={setRoleFilter}
            style={{ width: 140 }}
          />
          <CustomSelect
            options={[
              { value: '', label: 'All Status' },
              { value: 'active', label: 'Active' },
              { value: 'inactive', label: 'Inactive' },
            ]}
            value={statusFilter}
            onChange={setStatusFilter}
            style={{ width: 140 }}
          />
        </div>
      </div>

      {/* Users Table */}
      <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
        <table className="data-table">
          <thead>
            <tr>
              <th>User</th>
              <th>Role</th>
              <th>Status</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((u, i) => (
              <tr key={u.id}>
                <td>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                    <div className="user-avatar" style={{ background: avatarColors[i % avatarColors.length] }}>
                      {getInitials(u.full_name)}
                    </div>
                    <div>
                      <div style={{ fontWeight: 600 }}>{u.full_name}</div>
                      <div style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)' }}>{u.email}</div>
                    </div>
                  </div>
                </td>
                <td>
                  <span style={{ display: 'inline-flex', alignItems: 'center', gap: '0.375rem', padding: '0.2rem 0.625rem', borderRadius: 9999, fontSize: '0.75rem', fontWeight: 600, border: `1px solid ${roleColors[u.role] || '#999'}`, color: roleColors[u.role] || '#999' }}>
                    <span style={{ width: 6, height: 6, borderRadius: '50%', background: roleColors[u.role] }} />
                    {roleLabels[u.role] || u.role}
                  </span>
                </td>
                <td>
                  <span className={`badge ${u.is_active ? 'badge-success' : 'badge-danger'}`}>
                    {u.is_active ? 'Active' : 'Suspended'}
                  </span>
                </td>
                <td>
                  <div style={{ display: 'flex', gap: '0.25rem' }}>
                    <button className="btn btn-ghost btn-sm" style={{ padding: '0.25rem' }} onClick={() => {
                      setEditingUser(u);
                      setFormData({ username: u.username, full_name: u.full_name, email: u.email, role: u.role, password: '' });
                      setShowModal(true);
                    }}>
                      <Edit size={14} />
                    </button>
                    <button className="btn btn-ghost btn-sm" style={{ padding: '0.25rem', color: 'var(--color-danger)' }} onClick={() => handleDelete(u.id)}>
                      <Trash2 size={14} />
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        <div style={{ padding: '0.75rem 1.5rem', fontSize: '0.8125rem', color: 'var(--color-text-muted)', borderTop: '1px solid var(--color-border)', display: 'flex', justifyContent: 'space-between' }}>
          <span>Showing 1-{filtered.length} of {filtered.length} users</span>
          <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
            <button className="btn btn-ghost btn-sm" disabled>Previous</button>
            <span style={{ width: 28, height: 28, borderRadius: '50%', background: 'var(--color-primary)', color: 'white', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '0.75rem', fontWeight: 700 }}>1</span>
            <button className="btn btn-ghost btn-sm" disabled>Next</button>
          </div>
        </div>
      </div>

      {showModal && (
        <div style={{ position: 'fixed', inset: 0, zIndex: 1000, background: 'rgba(0,0,0,0.5)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <div className="card" style={{ width: '100%', maxWidth: 400 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '1rem' }}>
              <h3 style={{ fontSize: '1.25rem', fontWeight: 600 }}>{editingUser ? 'Edit User' : 'Add User'}</h3>
              <button className="btn btn-ghost" style={{ padding: 4 }} onClick={() => setShowModal(false)}><X size={20} /></button>
            </div>
            <form onSubmit={handleSave} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              {!editingUser && (
                <div>
                  <label className="form-label" style={{ fontSize: '0.875rem', display: 'block', marginBottom: '0.25rem', fontWeight: 500 }}>Username</label>
                  <input className="input" required value={formData.username} onChange={e => setFormData({...formData, username: e.target.value})} style={{ width: '100%' }} />
                </div>
              )}
              <div>
                <label className="form-label" style={{ fontSize: '0.875rem', display: 'block', marginBottom: '0.25rem', fontWeight: 500 }}>Full Name</label>
                <input className="input" required value={formData.full_name} onChange={e => setFormData({...formData, full_name: e.target.value})} style={{ width: '100%' }} />
              </div>
              <div>
                <label className="form-label" style={{ fontSize: '0.875rem', display: 'block', marginBottom: '0.25rem', fontWeight: 500 }}>Email</label>
                <input type="email" className="input" required value={formData.email} onChange={e => setFormData({...formData, email: e.target.value})} style={{ width: '100%' }} />
              </div>
              {!editingUser && (
                <div>
                  <label className="form-label" style={{ fontSize: '0.875rem', display: 'block', marginBottom: '0.25rem', fontWeight: 500 }}>Password</label>
                  <input type="password" className="input" required value={formData.password} onChange={e => setFormData({...formData, password: e.target.value})} style={{ width: '100%' }} />
                </div>
              )}
              <div>
                <label className="form-label" style={{ fontSize: '0.875rem', display: 'block', marginBottom: '0.25rem', fontWeight: 500 }}>Role</label>
                <CustomSelect
                  options={[
                    { value: 'admin', label: 'Admin' },
                    { value: 'manager', label: 'Manager' },
                    { value: 'cashier', label: 'Cashier' },
                    { value: 'stock_manager', label: 'Stock Manager' },
                  ]}
                  value={formData.role}
                  onChange={v => setFormData({...formData, role: v})}
                  style={{ width: '100%' }}
                />
              </div>
              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.5rem', marginTop: '1rem' }}>
                <button type="button" className="btn btn-ghost" onClick={() => setShowModal(false)}>Cancel</button>
                <button type="submit" className="btn btn-primary" disabled={loading}>{editingUser ? 'Save Changes' : 'Create User'}</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
