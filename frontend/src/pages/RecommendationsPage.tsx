import { useEffect, useState } from 'react';
import api from '../api';
import type { Recommendation } from '../types';
import { Brain, Search, GitMerge, Zap } from 'lucide-react';
import CustomSelect from '../components/CustomSelect';

export default function RecommendationsPage() {
  const [basketItems, setBasketItems] = useState<string[]>([]);
  const [results, setResults] = useState<Recommendation[]>([]);
  const [loading, setLoading] = useState(false);
  const [summary, setSummary] = useState<any>(null);
  const [products, setProducts] = useState<{ id: number; name: string }[]>([]);

  const search = async () => {
    if (basketItems.length === 0) return;
    setLoading(true);
    try {
      const res = await api.post('/api/ai/recommendations', { basket_items: basketItems, top_n: 8 });
      setResults(res.data);
    } catch (e) { console.error(e); }
    setLoading(false);
  };

  const loadData = async () => {
    try {
      const [sumRes, prodRes] = await Promise.all([
        api.get('/api/ai/recommendations/summary'),
        api.get('/api/products')
      ]);
      setSummary(sumRes.data);
      setProducts(prodRes.data);
    } catch (e) { console.error(e); }
  };

  useEffect(() => { loadData(); }, []);

  return (
    <div className="animate-fadeIn">
      <div className="page-header">
        <h2 style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <Brain size={24} color="var(--primary-light)" /> Recommandations IA (Hybride)
        </h2>
        <p>Moteur hybride combinant FP-Growth (Règles d'association), SVD (Filtrage Collaboratif) et Factorization Machines (Contexte).</p>
      </div>

      {/* Summary */}
      {summary && summary.fp_growth && (
        <div className="grid-3" style={{ marginBottom: '1.5rem' }}>
          <div className="kpi-card">
            <div className="kpi-icon" style={{ background: 'rgba(99,102,241,0.15)' }}>
              <Brain size={24} color="#818cf8" />
            </div>
            <div>
              <div className="kpi-value" style={{ color: '#818cf8' }}>{summary.fp_growth.total_rules}</div>
              <div className="kpi-label">Règles FP-Growth</div>
            </div>
          </div>
          <div className="kpi-card">
            <div className="kpi-icon" style={{ background: 'rgba(245,158,11,0.15)' }}>
              <GitMerge size={24} color="#fbbf24" />
            </div>
            <div>
              <div className="kpi-value" style={{ color: '#fbbf24' }}>{summary.svd?.total_items || 0}</div>
              <div className="kpi-label">Articles SVD (Filtrage)</div>
            </div>
          </div>
          <div className="kpi-card">
            <div className="kpi-icon" style={{ background: 'rgba(16,185,129,0.15)' }}>
              <Zap size={24} color="#34d399" />
            </div>
            <div>
              <div className="kpi-value" style={{ color: '#34d399' }}>{summary.fm?.n_features || 0}</div>
              <div className="kpi-label">Features Contextuels (FM)</div>
            </div>
          </div>
        </div>
      )}

      {/* Search */}
      <div className="card" style={{ marginBottom: '1.5rem' }}>
        <h3 style={{ fontSize: '0.9375rem', fontWeight: 600, marginBottom: '0.75rem' }}>
          Tester une recommandation (Panier)
        </h3>
        
        {/* Chips for selected items */}
        {basketItems.length > 0 && (
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem', marginBottom: '1rem' }}>
            {basketItems.map(item => (
              <div key={item} className="badge" style={{ display: 'flex', alignItems: 'center', gap: '0.25rem', padding: '0.4rem 0.75rem', fontSize: '0.875rem' }}>
                {item}
                <button 
                  onClick={() => setBasketItems(basketItems.filter(i => i !== item))}
                  style={{ background: 'none', border: 'none', cursor: 'pointer', display: 'flex', alignItems: 'center', marginLeft: '0.25rem', color: 'var(--text-muted)' }}
                >×</button>
              </div>
            ))}
          </div>
        )}

        <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
          <div style={{ flex: 1, minWidth: 250 }}>
            <CustomSelect 
              placeholder="+ Ajouter un produit au panier..."
              options={products.filter(p => !basketItems.includes(p.name)).map(p => ({ value: p.name, label: p.name }))}
              value=""
              onChange={(val) => {
                if (val && !basketItems.includes(val)) {
                  setBasketItems([...basketItems, val]);
                }
              }}
            />
          </div>
          <button className="btn btn-primary" onClick={search} disabled={loading || basketItems.length === 0} style={{ height: '42px' }}>
            <Search size={16} /> {loading ? '...' : 'Analyser'}
          </button>
        </div>
      </div>

      {/* Results */}
      {results.length > 0 && (
        <div>
          <h3 style={{ fontSize: '1rem', fontWeight: 600, marginBottom: '1rem' }}>
            {results.length} recommandations trouvées
          </h3>
          <div className="grid-2">
            {results.map((r, i) => (
              <div key={i} className="card" style={{ animationDelay: `${i * 80}ms` }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', marginBottom: '0.75rem' }}>
                  <div>
                    <div style={{ fontWeight: 700, fontSize: '1rem' }}>{r.product_name}</div>
                    <span className="badge badge-primary" style={{ marginTop: '0.25rem' }}>{r.source?.join(' + ')}</span>
                  </div>
                  <div style={{ textAlign: 'right' }}>
                    <div style={{ fontSize: '1.25rem', fontWeight: 700, color: 'var(--accent)' }}>
                      {r.confidence}%
                    </div>
                    <div style={{ fontSize: '0.6875rem', color: 'var(--text-muted)' }}>confiance</div>
                  </div>
                </div>
                <div style={{ fontSize: '0.8125rem', color: 'var(--text-secondary)', marginBottom: '0.75rem', lineHeight: 1.5 }}>
                  💡 {r.explanation}
                </div>
                <div style={{ display: 'flex', gap: '0.5rem' }}>
                  <span className="badge badge-info">Lift: {r.lift}x</span>
                  <span className="badge badge-success">Support: {r.support}%</span>
                  <span className="badge badge-warning">Score: {r.score}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
