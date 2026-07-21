import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './AuthContext';
import DashboardLayout from './layouts/DashboardLayout';
import LoginPage from './pages/LoginPage';
import DashboardPage from './pages/DashboardPage';
import POSPage from './pages/POSPage';
import PaymentPage from './pages/PaymentPage';
import ReceiptPage from './pages/ReceiptPage';
import ProductsPage from './pages/ProductsPage';
import SalesReportsPage from './pages/SalesReportsPage';
import OrdersPage from './pages/OrdersPage';
import AnomaliesPage from './pages/AnomaliesPage';
import ForecastingPage from './pages/ForecastingPage';
import SegmentsPage from './pages/SegmentsPage';
import UserManagementPage from './pages/UserManagementPage';
import ActivityLogsPage from './pages/ActivityLogsPage';
import StockDashboardPage from './pages/StockDashboardPage';
import StockPage from './pages/StockPage';
import StockMovementsPage from './pages/StockMovementsPage';
import SuppliersPage from './pages/SuppliersPage';
import RecommendationsPage from './pages/RecommendationsPage';

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth();
  if (loading) return null;
  if (!user) return <Navigate to="/login" replace />;
  return <>{children}</>;
}

function RoleRoute({ children, allowedRoles }: { children: React.ReactNode, allowedRoles: string[] }) {
  const { user, loading } = useAuth();
  if (loading) return null;
  if (!user) return <Navigate to="/login" replace />;
  
  if (!allowedRoles.includes(user.role)) {
    switch (user.role) {
      case 'cashier': return <Navigate to="/pos" replace />;
      case 'stock_manager': return <Navigate to="/stock/dashboard" replace />;
      default: return <Navigate to="/dashboard" replace />;
    }
  }
  return <>{children}</>;
}

function RoleRedirect() {
  const { user } = useAuth();
  if (!user) return <Navigate to="/login" replace />;

  switch (user.role) {
    case 'cashier':
      return <Navigate to="/pos" replace />;
    case 'stock_manager':
      return <Navigate to="/stock/dashboard" replace />;
    default:
      return <Navigate to="/dashboard" replace />;
  }
}

function AppRoutes() {
  const { user, loading } = useAuth();
  if (loading) return null;

  return (
    <Routes>
      <Route path="/login" element={user ? <RoleRedirect /> : <LoginPage />} />

      {/* Cashier POS — full-screen, no sidebar */}
      <Route path="/pos" element={
        <RoleRoute allowedRoles={['admin', 'manager', 'cashier']}><POSPage /></RoleRoute>
      } />
      <Route path="/pos/payment" element={
        <RoleRoute allowedRoles={['admin', 'manager', 'cashier']}><PaymentPage /></RoleRoute>
      } />
      <Route path="/pos/receipt" element={
        <RoleRoute allowedRoles={['admin', 'manager', 'cashier']}><ReceiptPage /></RoleRoute>
      } />

      {/* Admin / Manager / Stock Manager — with sidebar */}
      <Route path="/" element={
        <ProtectedRoute><DashboardLayout /></ProtectedRoute>
      }>
        <Route index element={<RoleRedirect />} />

        {/* Admin/Manager Analytics */}
        <Route path="dashboard" element={<RoleRoute allowedRoles={['admin', 'manager']}><DashboardPage /></RoleRoute>} />
        <Route path="sales-reports" element={<RoleRoute allowedRoles={['admin', 'manager']}><SalesReportsPage /></RoleRoute>} />
        <Route path="customer-insights" element={<RoleRoute allowedRoles={['admin', 'manager']}><DashboardPage /></RoleRoute>} />
        <Route path="orders" element={<RoleRoute allowedRoles={['admin', 'manager', 'cashier', 'stock_manager']}><OrdersPage /></RoleRoute>} />

        {/* AI Modules */}
        <Route path="ai/anomalies" element={<RoleRoute allowedRoles={['admin', 'manager']}><AnomaliesPage /></RoleRoute>} />
        <Route path="ai/forecasting" element={<RoleRoute allowedRoles={['admin', 'manager', 'stock_manager']}><ForecastingPage /></RoleRoute>} />
        <Route path="ai/segments" element={<RoleRoute allowedRoles={['admin', 'manager']}><SegmentsPage /></RoleRoute>} />
        <Route path="ai/recommendations" element={<RoleRoute allowedRoles={['admin', 'manager']}><RecommendationsPage /></RoleRoute>} />

        {/* Management */}
        <Route path="products" element={<RoleRoute allowedRoles={['admin', 'manager']}><ProductsPage /></RoleRoute>} />

        {/* User Management */}
        <Route path="users" element={<RoleRoute allowedRoles={['admin']}><UserManagementPage /></RoleRoute>} />
        <Route path="activity-logs" element={<RoleRoute allowedRoles={['admin', 'manager']}><ActivityLogsPage /></RoleRoute>} />

        {/* Stock Manager */}
        <Route path="stock/dashboard" element={<RoleRoute allowedRoles={['admin', 'manager', 'stock_manager']}><StockDashboardPage /></RoleRoute>} />
        <Route path="stock/inventory" element={<RoleRoute allowedRoles={['admin', 'manager', 'stock_manager']}><StockPage /></RoleRoute>} />
        <Route path="stock/movements" element={<RoleRoute allowedRoles={['admin', 'manager', 'stock_manager']}><StockMovementsPage /></RoleRoute>} />
        <Route path="stock/suppliers" element={<RoleRoute allowedRoles={['admin', 'manager', 'stock_manager']}><SuppliersPage /></RoleRoute>} />
      </Route>

      <Route path="*" element={<RoleRedirect />} />
    </Routes>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <AppRoutes />
      </AuthProvider>
    </BrowserRouter>
  );
}
