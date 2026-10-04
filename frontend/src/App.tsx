import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './AuthContext';
import DashboardLayout from './layouts/DashboardLayout';
import LoginPage from './pages/LoginPage';
import DashboardPage from './pages/DashboardPage';
import CustomerInsightsPage from './pages/CustomerInsightsPage';
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
import AuditLogsPage from './pages/AuditLogsPage';
import StockDashboardPage from './pages/StockDashboardPage';
import StockPage from './pages/StockPage';
import StockMovementsPage from './pages/StockMovementsPage';
import SuppliersPage from './pages/SuppliersPage';
import RecommendationsPage from './pages/RecommendationsPage';
import UnauthorizedPage from './pages/UnauthorizedPage';
import { getHomePathForRole } from './rbac';

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
    return <Navigate to="/unauthorized" replace />;
  }
  return <>{children}</>;
}

function RoleRedirect() {
  const { user } = useAuth();
  if (!user) return <Navigate to="/login" replace />;

  return <Navigate to={getHomePathForRole(user.role)} replace />;
}

function AppRoutes() {
  const { user, loading } = useAuth();
  if (loading) return null;

  return (
    <Routes>
      <Route path="/login" element={user ? <RoleRedirect /> : <LoginPage />} />
      <Route path="/unauthorized" element={<UnauthorizedPage />} />

      {/* Cashier POS — full-screen, no sidebar */}
      <Route path="/pos" element={
        <RoleRoute allowedRoles={['manager', 'cashier']}><POSPage /></RoleRoute>
      } />
      <Route path="/pos/payment" element={
        <RoleRoute allowedRoles={['manager', 'cashier']}><PaymentPage /></RoleRoute>
      } />
      <Route path="/pos/receipt" element={
        <RoleRoute allowedRoles={['manager', 'cashier']}><ReceiptPage /></RoleRoute>
      } />

      {/* Manager / Stock Manager — with sidebar */}
      <Route path="/" element={
        <ProtectedRoute><DashboardLayout /></ProtectedRoute>
      }>
        <Route index element={<RoleRedirect />} />

        {/* Manager Analytics */}
        <Route path="dashboard" element={<RoleRoute allowedRoles={['manager']}><DashboardPage /></RoleRoute>} />
        <Route path="sales-reports" element={<RoleRoute allowedRoles={['manager']}><SalesReportsPage /></RoleRoute>} />
        <Route path="customer-insights" element={<RoleRoute allowedRoles={['manager']}><CustomerInsightsPage /></RoleRoute>} />
        <Route path="orders" element={<RoleRoute allowedRoles={['manager', 'cashier', 'stock_manager']}><OrdersPage /></RoleRoute>} />

        {/* AI Modules */}
        <Route path="ai/anomalies" element={<RoleRoute allowedRoles={['manager']}><AnomaliesPage /></RoleRoute>} />
        <Route path="ai/forecasting" element={<RoleRoute allowedRoles={['manager', 'stock_manager']}><ForecastingPage /></RoleRoute>} />
        <Route path="ai/segments" element={<RoleRoute allowedRoles={['manager']}><SegmentsPage /></RoleRoute>} />
        <Route path="ai/recommendations" element={<RoleRoute allowedRoles={['manager']}><RecommendationsPage /></RoleRoute>} />

        {/* Management */}
        <Route path="products" element={<RoleRoute allowedRoles={['manager']}><ProductsPage /></RoleRoute>} />

        {/* User Management */}
        <Route path="users" element={<RoleRoute allowedRoles={['manager']}><UserManagementPage /></RoleRoute>} />
        <Route path="audit-logs" element={<RoleRoute allowedRoles={['manager']}><AuditLogsPage /></RoleRoute>} />

        {/* Stock Manager */}
        <Route path="stock/dashboard" element={<RoleRoute allowedRoles={['stock_manager']}><StockDashboardPage /></RoleRoute>} />
        <Route path="stock/inventory" element={<RoleRoute allowedRoles={['stock_manager']}><StockPage /></RoleRoute>} />
        <Route path="stock/movements" element={<RoleRoute allowedRoles={['stock_manager']}><StockMovementsPage /></RoleRoute>} />
        <Route path="stock/suppliers" element={<RoleRoute allowedRoles={['stock_manager']}><SuppliersPage /></RoleRoute>} />
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
