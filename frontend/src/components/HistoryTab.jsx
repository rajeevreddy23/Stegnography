import React, { useState, useEffect } from 'react';
import { History, Shield, Lock, Clock, CheckCircle2 } from 'lucide-react';

export default function HistoryTab() {
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchHistory = () => {
    fetch('/api/history')
      .then((res) => res.json())
      .then((data) => {
        setHistory(data.history || []);
        setLoading(false);
      })
      .catch((err) => {
        console.error('Failed to fetch history:', err);
        setLoading(false);
      });
  };

  useEffect(() => {
    fetchHistory();
  }, []);

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      <div className="bg-white dark:bg-slate-900 rounded-2xl p-6 border border-slate-200 dark:border-slate-800 shadow-sm space-y-4">
        <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-800 pb-4">
          <div>
            <h3 className="font-bold text-xl text-slate-900 dark:text-white flex items-center gap-2">
              <History className="w-6 h-6 text-blue-600" />
              Recent Operations Log
            </h3>
            <p className="text-xs text-slate-500">Persistent log of recent embedding and extraction sessions</p>
          </div>
          <button
            onClick={fetchHistory}
            className="text-xs px-3 py-1.5 bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 rounded-lg font-medium text-slate-700 dark:text-slate-300 transition-colors"
          >
            Refresh
          </button>
        </div>

        {loading ? (
          <div className="py-12 text-center text-sm text-slate-500">Loading history...</div>
        ) : history.length === 0 ? (
          <div className="py-12 text-center text-sm text-slate-500">
            No recent operations recorded yet. Try embedding or extracting a secret payload!
          </div>
        ) : (
          <div className="space-y-3">
            {history.map((item) => (
              <div
                key={item.id}
                className="p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-800/40 flex flex-col sm:flex-row sm:items-center justify-between gap-3"
              >
                <div className="flex items-start gap-3">
                  <div
                    className={`p-2 rounded-lg text-white ${
                      item.action === 'Embed' ? 'bg-blue-600' : 'bg-emerald-600'
                    }`}
                  >
                    {item.action === 'Embed' ? <Shield className="w-4 h-4" /> : <Lock className="w-4 h-4" />}
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="font-semibold text-sm text-slate-900 dark:text-white">
                        {item.action}: {item.scheme}
                      </span>
                      <span className="text-[10px] px-2 py-0.5 rounded font-mono bg-slate-200 dark:bg-slate-700 text-slate-700 dark:text-slate-300">
                        {item.id}
                      </span>
                    </div>
                    <div className="flex items-center gap-3 text-xs text-slate-500 dark:text-slate-400 mt-1">
                      <span className="flex items-center gap-1">
                        <Clock className="w-3 h-3" />
                        {item.timestamp}
                      </span>
                      {item.bpp && <span>{item.bpp.toFixed(4)} bpp</span>}
                      {item.psnr && <span>PSNR: {item.psnr} dB</span>}
                      {item.change_rate && <span>Change: {(item.change_rate * 100).toFixed(2)}%</span>}
                    </div>
                  </div>
                </div>

                <div className="text-right">
                  <span className="inline-flex items-center gap-1 text-xs font-semibold text-emerald-600 dark:text-emerald-400">
                    <CheckCircle2 className="w-3.5 h-3.5" /> Success
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
