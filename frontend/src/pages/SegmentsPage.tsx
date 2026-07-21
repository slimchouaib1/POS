import { useEffect, useState, useRef, useCallback } from 'react';
import api from '../api';
import { useAuth } from '../AuthContext';
import { UserCheck, Award, AlertTriangle, Clock, Target, Star, Users, Briefcase, Heart, Activity, RefreshCw, CheckCircle2 } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts';

const getSegmentConfig = (name: string) => {
  const n = name.toLowerCase();
  if (n.includes('champion')) return { icon: Award, color: '#f59e0b', bg: 'rgba(245,158,11,0.1)' };
  if (n.includes('loyal')) return { icon: Heart, color: '#ec4899', bg: 'rgba(236,72,153,0.1)' };
  if (n.includes('risk') || n.includes('attention')) return { icon: AlertTriangle, color: '#ef4444', bg: 'rgba(239,68,68,0.1)' };
  if (n.includes('hibernating') || n.includes('lost')) return { icon: Clock, color: '#6b7280', bg: 'rgba(107,114,128,0.1)' };
  if (n.includes('promising') || n.includes('new')) return { icon: Star, color: '#10b981', bg: 'rgba(16,185,129,0.1)' };
  if (n.includes('cannot lose')) return { icon: Target, color: '#8b5cf6', bg: 'rgba(139,92,246,0.1)' };
  return { icon: Users, color: '#6366f1', bg: 'rgba(99,102,241,0.1)' };
};

export default function SegmentsPage() {
  const { user } = useAuth();
  const [data, setData] = useState<any>(null);
  const [regenerating, setRegenerating] = useState(false);
  const [regenDone, setRegenDone] = useState(false);
  const [lastRegen, setLastRegen] = useState<string | null>(null);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const fetchData = useCallback(() => {
    api.get('/api/ai/segmentation/overview').then((r) => {
      setData(r.data);
      if (r.data.last_regenerated) setLastRegen(r.data.last_regenerated);
    });
  }, []);

  useEffect(() => { fetchData(); }, [fetchData]);

  // Cleanup polling on unmount
  useEffect(() => {
    return () => { if (pollRef.current) clearInterval(pollRef.current); };
  }, []);

  const handleRegenerate = async () => {
    try {
      setRegenerating(true);
      setRegenDone(false);
      await api.post('/api/ai/segmentation/regenerate');

      // Poll status every 3s until done
      pollRef.current = setInterval(async () => {
        try {
          const res = await api.get('/api/ai/segmentation/regenerate/status');
          if (!res.data.running) {
            if (pollRef.current) clearInterval(pollRef.current);
            pollRef.current = null;
            setRegenerating(false);
            setRegenDone(true);
            if (res.data.last_run) setLastRegen(res.data.last_run);
            // Auto-refresh dashboard
            fetchData();
            // Clear the "done" badge after 5s
            setTimeout(() => setRegenDone(false), 5000);
          }
        } catch { /* keep polling */ }
      }, 3000);
    } catch (err: any) {
      setRegenerating(false);
      if (err.response?.status === 409) {
        alert('A regeneration is already in progress.');
      } else {
        alert(err.response?.data?.detail || 'Failed to start regeneration');
      }
    }
  };

  const isAdminOrManager = user?.role === 'admin' || user?.role === 'manager';

  if (!data) return (
    <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '60vh', color: 'var(--primary)', gap: '0.75rem', fontWeight: 600 }}>
      <Activity className="animate-spin" /> Loading Customer Insights...
    </div>
  );

  return (
    <div className="animate-fadeIn">
      <div className="page-header" style={{ marginBottom: '2rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', flexWrap: 'wrap', gap: '1rem' }}>
          <div>
            <h2 style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '1.5rem', fontWeight: 800 }}>
              <UserCheck size={28} color="var(--primary)" /> Customer Segments
            </h2>
            <p style={{ color: 'var(--text-secondary)', marginTop: '0.25rem', fontSize: '0.9375rem' }}>
              RFM + KMeans + Hybrid — <strong style={{ color: 'var(--text-primary)' }}>{data.total_customers.toLocaleString()}</strong> customers analyzed
            </p>
          </div>

          {isAdminOrManager && (
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: '0.375rem' }}>
              <button
                className={`btn ${regenDone ? 'btn-outline' : 'btn-primary'}`}
                onClick={handleRegenerate}
                disabled={regenerating}
                style={{
                  display: 'flex', alignItems: 'center', gap: '0.5rem',
                  ...(regenDone ? { color: 'var(--success)', borderColor: 'var(--success)' } : {}),
                }}
              >
                {regenerating ? (
                  <><RefreshCw size={16} className="animate-spin" /> Regenerating…</>
                ) : regenDone ? (
                  <><CheckCircle2 size={16} /> Done!</>
                ) : (
                  <><RefreshCw size={16} /> Regenerate Segments</>
                )}
              </button>
              {lastRegen && (
                <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                  Last regenerated: {new Date(lastRegen).toLocaleString()}
                </span>
              )}
            </div>
          )}
        </div>
      </div>

      {/* RFM Segments */}
      <div className="card" style={{ marginBottom: '1.5rem', border: '1px solid var(--border)', boxShadow: '0 4px 6px -1px rgba(0,0,0,0.05)' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
          <h3 style={{ fontSize: '1.125rem', fontWeight: 700, color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Briefcase size={20} color="var(--text-secondary)" /> RFM Segments 
            <span className="badge badge-info" style={{ marginLeft: '0.5rem' }}>{data.rfm_segments?.length || 0}</span>
          </h3>
        </div>
        
        {data.rfm_segments?.length > 0 ? (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: '1rem' }}>
            {data.rfm_segments.map((seg: any, i: number) => {
              const { icon: Icon, color, bg } = getSegmentConfig(seg.segment);
              return (
                <div key={i} className="kpi-card" style={{ position: 'relative', overflow: 'hidden', transition: 'transform 0.2s, box-shadow 0.2s', cursor: 'default' }} 
                     onMouseEnter={(e) => { e.currentTarget.style.transform = 'translateY(-2px)'; e.currentTarget.style.boxShadow = '0 10px 15px -3px rgba(0,0,0,0.1)'; }}
                     onMouseLeave={(e) => { e.currentTarget.style.transform = 'none'; e.currentTarget.style.boxShadow = 'var(--shadow-sm)'; }}>
                  <div style={{ position: 'absolute', top: 0, right: 0, width: '60px', height: '60px', background: bg, borderBottomLeftRadius: '100%', zIndex: 0, opacity: 0.5 }}></div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', marginBottom: '1rem', position: 'relative', zIndex: 1 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                      <div style={{ padding: '0.5rem', borderRadius: '8px', background: bg, color: color }}>
                        <Icon size={20} />
                      </div>
                      <span style={{ fontWeight: 700, fontSize: '0.9375rem', color: 'var(--text-primary)' }}>{seg.segment}</span>
                    </div>
                    <span style={{ fontSize: '0.75rem', fontWeight: 600, padding: '0.25rem 0.6rem', borderRadius: '999px', background: bg, color: color }}>
                      {seg.customers.toLocaleString()} users
                    </span>
                  </div>
                  
                  <div style={{ display: 'flex', justifyContent: 'space-between', padding: '0.75rem', background: 'var(--bg-page)', borderRadius: '8px', position: 'relative', zIndex: 1 }}>
                    <div style={{ textAlign: 'center' }}>
                      <div style={{ fontSize: '0.6875rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.5px' }}>Revenue</div>
                      <div style={{ fontWeight: 700, color: 'var(--accent)', fontSize: '0.875rem' }}>{(seg.total_revenue / 1000).toFixed(1)}k DT</div>
                    </div>
                    <div style={{ width: '1px', background: 'var(--border)' }}></div>
                    <div style={{ textAlign: 'center' }}>
                      <div style={{ fontSize: '0.6875rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.5px' }}>Avg Order</div>
                      <div style={{ fontWeight: 700, color: 'var(--text-primary)', fontSize: '0.875rem' }}>{seg.avg_monetary.toFixed(0)} DT</div>
                    </div>
                    <div style={{ width: '1px', background: 'var(--border)' }}></div>
                    <div style={{ textAlign: 'center' }}>
                      <div style={{ fontSize: '0.6875rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.5px' }}>Freq</div>
                      <div style={{ fontWeight: 700, color: 'var(--text-primary)', fontSize: '0.875rem' }}>{seg.avg_frequency.toFixed(1)}</div>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        ) : <p style={{ color: 'var(--text-muted)', padding: '2rem', textAlign: 'center' }}>No RFM data available</p>}
      </div>

      {/* KMeans */}
      <div className="card" style={{ marginBottom: '1.5rem' }}>
        <h3 style={{ fontSize: '1.125rem', fontWeight: 700, color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1.5rem' }}>
          <Target size={20} color="var(--primary)" /> KMeans Clusters <span className="badge badge-primary" style={{ marginLeft: '0.5rem' }}>{data.kmeans_segments?.length || 0}</span>
        </h3>
        {data.kmeans_segments?.length > 0 && (
          <ResponsiveContainer width="100%" height={320}>
            <BarChart data={data.kmeans_segments} margin={{ top: 20, right: 30, left: 0, bottom: 20 }}>
              <defs>
                <linearGradient id="colorCluster" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="var(--primary)" stopOpacity={0.9}/>
                  <stop offset="95%" stopColor="var(--primary)" stopOpacity={0.4}/>
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" vertical={false} />
              <XAxis dataKey="segment_name" tick={{ fill: 'var(--text-secondary)', fontSize: 11, fontWeight: 500 }} axisLine={false} tickLine={false} dy={10} />
              <YAxis tick={{ fill: 'var(--text-secondary)', fontSize: 11 }} axisLine={false} tickLine={false} />
              <Tooltip 
                cursor={{ fill: 'rgba(99,102,241,0.05)' }}
                contentStyle={{ background: 'rgba(255,255,255,0.9)', backdropFilter: 'blur(8px)', border: '1px solid var(--border)', borderRadius: '12px', boxShadow: '0 10px 15px -3px rgba(0,0,0,0.1)', color: 'var(--text-primary)' }}
                itemStyle={{ color: 'var(--primary)', fontWeight: 700 }}
              />
              <Bar dataKey="customers" fill="url(#colorCluster)" radius={[6, 6, 0, 0]} maxBarSize={60}>
                {data.kmeans_segments.map((_entry: any, index: number) => (
                  <Cell key={`cell-${index}`} fill={`url(#colorCluster)`} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        )}
      </div>

      {/* Hybrid Segments */}
      <div className="card" style={{ marginBottom: '2rem' }}>
        <h3 style={{ fontSize: '1.125rem', fontWeight: 700, color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1.5rem' }}>
          <Star size={20} color="var(--accent)" /> Hybrid Segments <span className="badge badge-warning" style={{ marginLeft: '0.5rem' }}>{data.hybrid_segments?.length || 0}</span>
        </h3>
        {data.hybrid_segments?.length > 0 ? (
          <div style={{ borderRadius: '12px', overflow: 'hidden', border: '1px solid var(--border)' }}>
            <table className="data-table" style={{ margin: 0 }}>
              <thead style={{ background: 'var(--bg-page)' }}>
                <tr>
                  <th style={{ padding: '1rem', color: 'var(--text-secondary)', fontWeight: 600, textTransform: 'uppercase', fontSize: '0.75rem', letterSpacing: '0.5px' }}>Hybrid Segment</th>
                  <th style={{ padding: '1rem', color: 'var(--text-secondary)', fontWeight: 600, textTransform: 'uppercase', fontSize: '0.75rem', letterSpacing: '0.5px' }}>Customers</th>
                  <th style={{ padding: '1rem', color: 'var(--text-secondary)', fontWeight: 600, textTransform: 'uppercase', fontSize: '0.75rem', letterSpacing: '0.5px' }}>Revenue</th>
                  <th style={{ padding: '1rem', color: 'var(--text-secondary)', fontWeight: 600, textTransform: 'uppercase', fontSize: '0.75rem', letterSpacing: '0.5px' }}>Recommended Action</th>
                </tr>
              </thead>
              <tbody>
                {data.hybrid_segments.map((seg: any, i: number) => {
                  const { color, bg } = getSegmentConfig(seg.segment);
                  return (
                    <tr key={i} style={{ borderBottom: i === data.hybrid_segments.length - 1 ? 'none' : '1px solid var(--border)', transition: 'background 0.2s' }} onMouseEnter={(e) => e.currentTarget.style.background = 'var(--bg-page)'} onMouseLeave={(e) => e.currentTarget.style.background = 'transparent'}>
                      <td style={{ padding: '1rem', fontWeight: 600, color: 'var(--text-primary)' }}>{seg.segment}</td>
                      <td style={{ padding: '1rem' }}><span style={{ padding: '0.25rem 0.75rem', borderRadius: '999px', background: 'var(--bg-page)', border: '1px solid var(--border)', fontSize: '0.8125rem', fontWeight: 600, color: 'var(--text-primary)' }}>{seg.customers.toLocaleString()}</span></td>
                      <td style={{ padding: '1rem', color: 'var(--accent)', fontWeight: 700 }}>{seg.total_revenue.toLocaleString()} DT</td>
                      <td style={{ padding: '1rem' }}>
                        {seg.recommended_action ? (
                          <span style={{ 
                            fontSize: '0.8125rem', 
                            fontWeight: 600, 
                            padding: '0.35rem 0.75rem', 
                            borderRadius: '8px', 
                            background: bg, 
                            color: color,
                            display: 'inline-block'
                          }}>
                            {seg.recommended_action}
                          </span>
                        ) : (
                          <span style={{ color: 'var(--text-muted)' }}>—</span>
                        )}
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        ) : <p style={{ color: 'var(--text-muted)', padding: '2rem', textAlign: 'center' }}>No hybrid data available</p>}
      </div>
    </div>
  );
}
