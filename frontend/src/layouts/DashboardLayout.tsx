import { NavLink, Outlet, useNavigate } from 'react-router-dom';
import { useAuth } from '../AuthContext';
import {
  LayoutDashboard, Package, Users,
  TrendingUp, ShieldAlert,
  LogOut, Activity, ClipboardList, ChefHat,
  FileText, PieChart, Boxes, ArrowLeftRight, Truck, Lightbulb
} from 'lucide-react';

/* ── Admin/Manager Sidebar ─────────────── */
const adminNav = [
  { section: 'ANALYTICS', items: [
    { to: '/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
    { to: '/sales-reports', icon: FileText, label: 'Sales Reports' },
  ]},
  { section: 'AI & INTELLIGENCE', items: [
    { to: '/ai/recommendations', icon: Lightbulb, label: 'Recommendations' },
    { to: '/ai/anomalies', icon: ShieldAlert, label: 'Anomaly Detection' },
    { to: '/ai/segments', icon: PieChart, label: 'Customer Segments' },
  ]},
  { section: 'MANAGEMENT', items: [
    { to: '/orders', icon: ClipboardList, label: 'Orders' },
    { to: '/products', icon: Package, label: 'Products' },
  ]},
  { section: 'USER MANAGEMENT', items: [
    { to: '/users', icon: Users, label: 'Users' },
    { to: '/activity-logs', icon: Activity, label: 'Activity Logs' },
  ]},
];

/* ── Stock Manager Sidebar ─────────────── */
const stockNav = [
  { section: '', items: [
    { to: '/stock/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
    { to: '/stock/inventory', icon: Boxes, label: 'Inventory' },
    { to: '/stock/movements', icon: ArrowLeftRight, label: 'Stock Movements' },
    { to: '/stock/suppliers', icon: Truck, label: 'Suppliers' },
    { to: '/ai/forecasting', icon: TrendingUp, label: 'Demand Forecasting' },
  ]},
];

function SidebarNav({ sections }: { sections: typeof adminNav }) {
  return (
    <nav style={{ flex: 1, paddingTop: '0.25rem' }}>
      {sections.map((group) => (
        <div key={group.section || 'main'}>
          {group.section && <div className="sidebar-section">{group.section}</div>}
          {group.items.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) => `sidebar-link ${isActive ? 'active' : ''}`}
            >
              <item.icon size={18} />
              {item.label}
            </NavLink>
          ))}
        </div>
      ))}
    </nav>
  );
}

export default function DashboardLayout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const roleSubtitle: Record<string, string> = {
    admin: 'Management Portal',
    manager: 'Reporting & Analytics',
    cashier: 'Main Terminal',
    stock_manager: 'Stock Management',
  };

  // Cashier gets redirected to POS, not the dashboard layout
  const navSections = user?.role === 'stock_manager' ? stockNav : adminNav;

  return (
    <div style={{ display: 'flex' }}>
      {/* Sidebar */}
      <aside className="sidebar">
        <div className="sidebar-logo">
          <div className="logo-icon">
            <ChefHat size={22} />
          </div>
          <div>
            <h1>RestaurantPOS</h1>
            <span className="logo-subtitle">{roleSubtitle[user?.role || ''] || ''}</span>
          </div>
        </div>

        <SidebarNav sections={navSections} />

        {/* Footer */}
        <div style={{ padding: '1rem 1.5rem', borderTop: '1px solid var(--color-border)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.75rem' }}>
            <div className="user-avatar" style={{ background: '#DC3545' }}>
              {user?.full_name?.split(' ').map(n => n[0]).join('').slice(0, 2)}
            </div>
            <div>
              <div style={{ fontSize: '0.875rem', fontWeight: 600 }}>{user?.full_name}</div>
              <div style={{ fontSize: '0.6875rem', color: 'var(--color-text-muted)' }}>{user?.email}</div>
            </div>
          </div>
          <button onClick={handleLogout} className="btn btn-ghost btn-sm" style={{ width: '100%' }}>
            <LogOut size={14} /> Sign Out
          </button>
        </div>
      </aside>

      {/* Main area */}
      <div className="main-content">
        <main className="page-content">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
