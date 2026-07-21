import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../AuthContext';
import { ChefHat, ArrowRight, Mail, Lock, Sparkles, Eye, EyeOff, ArrowLeft } from 'lucide-react';

export default function LoginPage() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const user = await login(username.trim(), password);
      switch (user?.role) {
        case 'cashier': navigate('/pos'); break;
        case 'stock_manager': navigate('/stock/dashboard'); break;
        default: navigate('/dashboard'); break;
      }
    } catch {
      setError('Invalid username or password');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-page">
      {/* ── LEFT: Form ── */}
      <div className="login-left">
        <a href="#" className="login-back-link" onClick={(e) => { e.preventDefault(); navigate('/'); }}>
          <ArrowLeft size={18} />
          <span>Back to Home</span>
        </a>

        <div className="login-form-container">
          {/* Badge */}
          <div className="login-badge">
            <Sparkles size={14} /> POS Terminal Access
          </div>

          {/* Heading */}
          <h1>Welcome back.</h1>
          <p className="login-subtitle">Enter your credentials to access the POS system.</p>

          {/* Error */}
          {error && <div className="login-error">{error}</div>}

          {/* Form */}
          <form onSubmit={handleSubmit}>
            {/* Username */}
            <div className="form-group">
              <label htmlFor="login-username">Username</label>
              <div className="input-with-icon">
                <Mail size={18} />
                <input
                  id="login-username"
                  type="text"
                  placeholder="your username"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  required
                  autoFocus
                />
              </div>
            </div>

            {/* Password */}
            <div className="form-group">
              <div className="label-row">
                <label htmlFor="login-password">Password</label>
                <a href="#">Forgot password?</a>
              </div>
              <div className="input-with-icon">
                <Lock size={18} />
                <input
                  id="login-password"
                  type={showPassword ? 'text' : 'password'}
                  placeholder="••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                />
                <button
                  type="button"
                  className="toggle-password"
                  onClick={() => setShowPassword(!showPassword)}
                >
                  {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                </button>
              </div>
            </div>

            {/* Submit */}
            <button type="submit" className="login-submit-btn" disabled={loading}>
              {loading ? (
                <div style={{
                  width: 22, height: 22,
                  border: '2px solid rgba(255,255,255,0.3)',
                  borderTopColor: '#fff',
                  borderRadius: '50%',
                  animation: 'spin 0.8s linear infinite',
                }} />
              ) : (
                <>Sign In <ArrowRight size={18} /></>
              )}
            </button>
          </form>

          {/* Footer */}
          <p className="login-footer-text">
            Don't have an account? <a href="#">Contact admin</a>
          </p>

        </div>
      </div>

      {/* ── RIGHT: Brand Visual ── */}
      <div className="login-right">
        {/* Animated gradient blobs */}
        <div className="login-right-gradient">
          <div className="gradient-blob blob-1" />
          <div className="gradient-blob blob-2" />
          <div className="gradient-blob blob-3" />
        </div>

        {/* Content */}
        <div className="login-right-content">
          <div className="brand-logo">
            <ChefHat size={36} />
          </div>

          <div className="brand-quote">
            <div className="quote-mark">&ldquo;</div>
            <h3>
              Intelligent POS that learns your business
              and serves your customers better.
            </h3>
            <div className="quote-mark" style={{ textAlign: 'right' }}>&rdquo;</div>
          </div>

          <div style={{ marginTop: '2rem' }}>
            <div className="brand-author">POS Intelligent Timsoft</div>
            <div className="brand-author-role">AI-Powered Restaurant Management</div>
          </div>
        </div>
      </div>
    </div>
  );
}
