import React, { useState, useEffect } from 'react';
import { BarChart, Bar, LineChart, Line, XAxis, YAxis, Tooltip, Legend, ResponsiveContainer, CartesianGrid } from 'recharts';
import { BarChart3, TrendingUp, Layers, Sliders, Image as ImageIcon } from 'lucide-react';

export default function ExperimentsTab() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [selectedPlot, setSelectedPlot] = useState('fig14');

  useEffect(() => {
    fetch('/api/experiments')
      .then((res) => res.json())
      .then((json) => {
        setData(json);
        setLoading(false);
      })
      .catch((err) => {
        console.error('Failed to load experiment data:', err);
        setLoading(false);
      });
  }, []);

  if (loading) {
    return (
      <div className="text-center py-20 text-slate-500">
        Loading benchmark evaluation datasets...
      </div>
    );
  }

  if (!data) {
    return (
      <div className="text-center py-20 text-red-500">
        Failed to load experiment datasets. Run backend benchmark first.
      </div>
    );
  }

  // Pivot payload sweep for Recharts
  const payloadChartData = [];
  const payloads = [0.05, 0.1, 0.2, 0.3, 0.4, 0.5];
  payloads.forEach((p) => {
    const entry = { payload: p };
    data.payload_sweep.forEach((row) => {
      if (row.payload_bpp === p) {
        entry[row.scheme] = row.spam_pe;
      }
    });
    payloadChartData.push(entry);
  });

  const plots = [
    { id: 'fig14', name: 'Fig. 14: Detection Error vs. Payload', src: '/plots/fig14_pe_vs_payload.png' },
    { id: 'fig11', name: 'Fig. 11: FCC(2) vs. Alpha', src: '/plots/fig11_fcc2_vs_alpha.png' },
    { id: 'fig12', name: 'Fig. 12: Change Rate vs. Alpha', src: '/plots/fig12_changerate_vs_alpha.png' },
    { id: 'fig13', name: 'Fig. 13: Detection Error vs. Alpha', src: '/plots/fig13_pe_vs_alpha.png' },
    { id: 'fig15', name: 'Fig. 15: FCC(2) vs. Payload', src: '/plots/fig15_fcc2_vs_payload.png' },
    { id: 'fig16', name: 'Fig. 16: Lattice Decomposition L', src: '/plots/fig16_lattice_L_comparison.png' },
    { id: 'fig19', name: 'Fig. 19: Comprehensive Ablation Study', src: '/plots/fig19_ablation_comparison.png' },
  ];

  return (
    <div className="space-y-8 max-w-6xl mx-auto">
      {/* Header */}
      <div className="bg-white dark:bg-slate-900 rounded-2xl p-6 border border-slate-200 dark:border-slate-800 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h3 className="font-bold text-xl text-slate-900 dark:text-white flex items-center gap-2">
            <BarChart3 className="w-6 h-6 text-blue-600" />
            Experimental Evaluation Dashboard
          </h3>
          <p className="text-xs text-slate-500 mt-0.5">
            Empirical results mirroring IEEE TIFS 2015 paper across baselines, parameter sweeps, and novel improvements.
          </p>
        </div>
        <div className="flex gap-2">
          <span className="px-3 py-1 bg-blue-50 dark:bg-blue-900/40 text-blue-700 dark:text-blue-300 rounded-lg text-xs font-semibold">
            6 Comparative Schemes
          </span>
          <span className="px-3 py-1 bg-indigo-50 dark:bg-indigo-900/40 text-indigo-700 dark:text-indigo-300 rounded-lg text-xs font-semibold">
            Real Executed Runs
          </span>
        </div>
      </div>

      {/* Interactive Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Chart 1: Detection Error vs Payload */}
        <div className="bg-white dark:bg-slate-900 rounded-2xl p-6 border border-slate-200 dark:border-slate-800 shadow-sm space-y-4">
          <div className="flex items-center justify-between">
            <h4 className="font-semibold text-sm text-slate-800 dark:text-slate-200 flex items-center gap-2">
              <TrendingUp className="w-4 h-4 text-blue-600" />
              Fig. 14: Detection Error P_E vs. Relative Payload
            </h4>
            <span className="text-xs text-slate-400">SPAM 686-D</span>
          </div>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={payloadChartData}>
                <CartesianGrid strokeDasharray="3 3" opacity={0.2} />
                <XAxis dataKey="payload" unit=" bpp" tick={{ fontSize: 11 }} />
                <YAxis domain={[0, 0.5]} tick={{ fontSize: 11 }} />
                <Tooltip />
                <Legend />
                <Line type="monotone" dataKey="HILL" stroke="#8884d8" strokeDasharray="4 4" />
                <Line type="monotone" dataKey="S-UNIWARD" stroke="#82ca9d" strokeDasharray="4 4" />
                <Line type="monotone" dataKey="HILL-CMD" stroke="#ff7300" strokeWidth={2} />
                <Line type="monotone" dataKey="S-UNIWARD-CMD" stroke="#e91e63" strokeWidth={2} />
                <Line type="monotone" dataKey="HILL-CMD+" stroke="#00C49F" strokeWidth={3} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Chart 2: FCC(2) vs Alpha */}
        <div className="bg-white dark:bg-slate-900 rounded-2xl p-6 border border-slate-200 dark:border-slate-800 shadow-sm space-y-4">
          <div className="flex items-center justify-between">
            <h4 className="font-semibold text-sm text-slate-800 dark:text-slate-200 flex items-center gap-2">
              <Sliders className="w-4 h-4 text-indigo-600" />
              Fig. 11: Feature Continuity FCC(2) vs. Alpha
            </h4>
            <span className="text-xs text-slate-400">Payload 0.4 bpp</span>
          </div>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={data.alpha_sweep}>
                <CartesianGrid strokeDasharray="3 3" opacity={0.2} />
                <XAxis dataKey="alpha" tick={{ fontSize: 11 }} />
                <YAxis tick={{ fontSize: 11 }} />
                <Tooltip />
                <Legend />
                <Line type="monotone" dataKey="fcc2" stroke="#3b82f6" strokeWidth={2.5} name="FCC(2) Correlation" />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Chart 3: Change Rate vs Alpha */}
        <div className="bg-white dark:bg-slate-900 rounded-2xl p-6 border border-slate-200 dark:border-slate-800 shadow-sm space-y-4">
          <div className="flex items-center justify-between">
            <h4 className="font-semibold text-sm text-slate-800 dark:text-slate-200 flex items-center gap-2">
              <Layers className="w-4 h-4 text-amber-500" />
              Fig. 12: Change Rate vs. Alpha
            </h4>
            <span className="text-xs text-slate-400">Consolidation Curve</span>
          </div>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={data.alpha_sweep}>
                <CartesianGrid strokeDasharray="3 3" opacity={0.2} />
                <XAxis dataKey="alpha" tick={{ fontSize: 11 }} />
                <YAxis tick={{ fontSize: 11 }} unit="%" />
                <Tooltip formatter={(val) => [(val * 100).toFixed(2) + '%', 'Change Rate']} />
                <Legend />
                <Line type="monotone" dataKey="change_rate" stroke="#f59e0b" strokeWidth={2.5} name="Change Rate" />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Chart 4: Ablation Study Comparison */}
        <div className="bg-white dark:bg-slate-900 rounded-2xl p-6 border border-slate-200 dark:border-slate-800 shadow-sm space-y-4">
          <div className="flex items-center justify-between">
            <h4 className="font-semibold text-sm text-slate-800 dark:text-slate-200 flex items-center gap-2">
              <BarChart3 className="w-4 h-4 text-emerald-500" />
              Fig. 19: Ablation of Novel Enhancements
            </h4>
            <span className="text-xs text-slate-400">Payload 0.4 bpp</span>
          </div>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={data.ablation_study} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" opacity={0.2} />
                <XAxis type="number" domain={[0, 0.05]} tick={{ fontSize: 10 }} />
                <YAxis type="category" dataKey="configuration" width={140} tick={{ fontSize: 9 }} />
                <Tooltip />
                <Bar dataKey="fcc2" fill="#3b82f6" name="FCC(2) Clustering" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Generated Paper Figures Viewer */}
      <div className="bg-white dark:bg-slate-900 rounded-2xl p-6 border border-slate-200 dark:border-slate-800 shadow-sm space-y-5">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-100 dark:border-slate-800 pb-4">
          <div>
            <h4 className="font-bold text-lg text-slate-900 dark:text-white flex items-center gap-2">
              <ImageIcon className="w-5 h-5 text-indigo-600" />
              Publication-Quality High-Resolution Figures (300 DPI)
            </h4>
            <p className="text-xs text-slate-500">Matching IEEE TIFS 2015 layout and presentation standards</p>
          </div>
          <div className="flex flex-wrap gap-1.5">
            {plots.map((p) => (
              <button
                key={p.id}
                onClick={() => setSelectedPlot(p.id)}
                className={`px-2.5 py-1 text-xs rounded-lg font-medium transition-colors cursor-pointer ${
                  selectedPlot === p.id
                    ? 'bg-blue-600 text-white'
                    : 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 hover:bg-slate-200'
                }`}
              >
                {p.id.toUpperCase()}
              </button>
            ))}
          </div>
        </div>

        <div className="p-4 bg-slate-50 dark:bg-slate-950/40 rounded-xl border border-slate-200 dark:border-slate-800 text-center">
          {(() => {
            const current = plots.find((p) => p.id === selectedPlot) || plots[0];
            return (
              <div className="space-y-3">
                <span className="text-sm font-semibold text-slate-800 dark:text-slate-200 block">
                  {current.name}
                </span>
                <img
                  src={current.src}
                  alt={current.name}
                  className="max-h-96 mx-auto rounded-lg shadow-md border border-slate-200 dark:border-slate-800 object-contain"
                />
              </div>
            );
          })()}
        </div>
      </div>
    </div>
  );
}
