import type { User } from './types';

export type Role = User['role'];

const routeAccess: Array<{ path: string; roles: Role[] }> = [
  { path: '/pos', roles: ['manager', 'cashier'] },
  { path: '/dashboard', roles: ['manager'] },
  { path: '/sales-reports', roles: ['manager'] },
  { path: '/customer-insights', roles: ['manager'] },
  { path: '/orders', roles: ['manager', 'cashier', 'stock_manager'] },
  { path: '/ai/anomalies', roles: ['manager'] },
  { path: '/ai/forecasting', roles: ['manager', 'stock_manager'] },
  { path: '/ai/segments', roles: ['manager'] },
  { path: '/ai/recommendations', roles: ['manager'] },
  { path: '/products', roles: ['manager'] },
  { path: '/users', roles: ['manager'] },
  { path: '/audit-logs', roles: ['manager'] },
  { path: '/stock/dashboard', roles: ['stock_manager'] },
  { path: '/stock/inventory', roles: ['stock_manager'] },
  { path: '/stock/movements', roles: ['stock_manager'] },
  { path: '/stock/suppliers', roles: ['stock_manager'] },
];

export function getHomePathForRole(role: Role) {
  if (role === 'cashier') return '/pos';
  if (role === 'stock_manager') return '/stock/dashboard';
  return '/dashboard';
}

export function canAccessPath(role: Role, pathname: string) {
  if (pathname === '/') return true;

  const matchingRoute = routeAccess.find(({ path }) => (
    pathname === path || pathname.startsWith(`${path}/`)
  ));

  return matchingRoute ? matchingRoute.roles.includes(role) : false;
}
