import { Link } from 'react-router-dom';
import { ChefHat, Home, LogOut, ShieldAlert } from 'lucide-react';
import { useAuth } from '../AuthContext';

export default function UnauthorizedPage() {
  const { logout, user } = useAuth();
  const roleLabel = user?.role?.replace('_', ' ') || 'Guest';

  return (
    <main className="unauthorized-page">
      <section className="unauthorized-panel" aria-labelledby="unauthorized-title">
        <div className="unauthorized-brand">
          <Link to="/" className="unauthorized-logo">
            <span className="unauthorized-logo-icon">
              <ChefHat size={19} />
            </span>
            RestaurantPOS
          </Link>
          <span className="unauthorized-status">403</span>
        </div>

        <div className="unauthorized-content">
          <div className="unauthorized-icon">
            <ShieldAlert size={30} />
          </div>

          <div className="unauthorized-copy">
            <p className="unauthorized-eyebrow">Access blocked</p>
            <h1 id="unauthorized-title">Not authorized</h1>
            <p>
              Your <span>{roleLabel}</span> account does not have permission to open this page.
              Head back to your workspace or sign in with a different account.
            </p>
          </div>

          <div className="unauthorized-actions">
            <Link to="/" className="btn btn-primary unauthorized-action">
              <Home size={17} />
              My workspace
            </Link>
            <Link
              to="/login"
              onClick={() => logout()}
              className="btn btn-outline unauthorized-action"
            >
              <LogOut size={17} />
              Switch account
            </Link>
          </div>
        </div>
      </section>
    </main>
  );
}
