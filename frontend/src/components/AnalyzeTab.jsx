import React, { useState } from 'react';
import { Eye, ShieldAlert, BarChart2, Activity, Info, Upload } from 'lucide-react';

export default function AnalyzeTab() {
  const [coverFile, setCoverFile] = useState(null);
  const [stegoFile, setStegoFile] = useState(null);
  const [coverPreview, setCoverPreview] = useState(null);
  const [stegoPreview, setStegoPreview] = useState(null);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [analysis, setAnalysis] = useState(null);

  const handleAnalyze = async () => {
    if (!coverFile || !stegoFile) {
      setError('Please provide both Cover and Stego images.');
      return;
    }

    setLoading(true);
    setError(null);

    const formData = new FormData();
    formData.append('cover_file', coverFile);
    formData.append('stego_file', stegoFile);

    try {
      const response = await fetch('/api/analyze', {
        method: 'POST',
        body: formData,
      });

      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || 'Analysis failed.');
      }
      setAnalysis(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-8 max-w-6xl mx-auto">
      <div className="bg-white dark:bg-slate-900 rounded-2xl p-6 border border-slate-200 dark:border-slate-800 shadow-sm space-y-6">
        <div>
          <h3 className="font-bold text-xl text-slate-900 dark:text-white flex items-center gap-2">
            <Eye className="w-6 h-6 text-indigo-600" />
            Forensic & Statistical Steganalysis
          </h3>
          <p className="text-xs text-slate-500 mt-0.5">
            Compare Cover vs Stego, inspect modification direction clusters (Fig. 7), and evaluate live SPAM and SRNet detection scores.
          </p>
        </div>

        {/* Image Upload Row */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="space-y-2">
            <span className="text-xs font-semibold uppercase text-slate-500">1. Original Cover</span>
            <div className="border-2 border-dashed border-slate-300 dark:border-slate-700 rounded-xl p-3 text-center">
              <input
                type="file"
                id="analyze-cover"
                accept="image/*"
                onChange={(e) => {
                  const f = e.target.files[0];
                  if (f) {
                    setCoverFile(f);
                    setCoverPreview(URL.createObjectURL(f));
                  }
                }}
                className="hidden"
              />
              <label htmlFor="analyze-cover" className="cursor-pointer block">
                {coverPreview ? (
                  <img src={coverPreview} alt="Cover" className="max-h-48 mx-auto rounded-lg object-contain" />
                ) : (
                  <div className="py-8 text-sm text-slate-500">Click to Select Cover Image</div>
                )}
              </label>
            </div>
          </div>

          <div className="space-y-2">
            <span className="text-xs font-semibold uppercase text-slate-500">2. Stego Image</span>
            <div className="border-2 border-dashed border-slate-300 dark:border-slate-700 rounded-xl p-3 text-center">
              <input
                type="file"
                id="analyze-stego"
                accept="image/*"
                onChange={(e) => {
                  const f = e.target.files[0];
                  if (f) {
                    setStegoFile(f);
                    setStegoPreview(URL.createObjectURL(f));
                  }
                }}
                className="hidden"
              />
              <label htmlFor="analyze-stego" className="cursor-pointer block">
                {stegoPreview ? (
                  <img src={stegoPreview} alt="Stego" className="max-h-48 mx-auto rounded-lg object-contain" />
                ) : (
                  <div className="py-8 text-sm text-slate-500">Click to Select Stego Image</div>
                )}
              </label>
            </div>
          </div>
        </div>

        <button
          onClick={handleAnalyze}
          disabled={loading || !coverFile || !stegoFile}
          className="w-full py-3 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white rounded-xl font-semibold shadow-md shadow-blue-500/25 flex items-center justify-center gap-2 transition-all cursor-pointer disabled:opacity-50"
        >
          {loading ? 'Computing Forensic Statistics & SPAM Features...' : 'Run Comparative Analysis'}
        </button>

        {error && (
          <div className="p-3 bg-red-50 dark:bg-red-900/30 border border-red-200 dark:border-red-800 rounded-lg text-red-700 dark:text-red-300 text-xs">
            {error}
          </div>
        )}

        {/* Results Section */}
        {analysis && (
          <div className="space-y-6 pt-4 border-t border-slate-100 dark:border-slate-800">
            {/* Visual Heatmap */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="text-center space-y-1">
                <span className="text-xs font-semibold text-slate-600 dark:text-slate-400">Cover Image</span>
                <img src={analysis.cover_image} alt="Cover" className="rounded-lg border border-slate-200 dark:border-slate-800 mx-auto aspect-square object-cover" />
              </div>
              <div className="text-center space-y-1">
                <span className="text-xs font-semibold text-blue-600 dark:text-blue-400">Stego Image</span>
                <img src={analysis.stego_image} alt="Stego" className="rounded-lg border border-blue-300 dark:border-blue-700 mx-auto aspect-square object-cover" />
              </div>
              <div className="text-center space-y-1">
                <span className="text-xs font-semibold text-purple-600 dark:text-purple-400">Difference Heatmap (Fig. 7)</span>
                <img src={analysis.diff_heatmap} alt="Difference Heatmap" className="rounded-lg border border-purple-300 dark:border-purple-700 mx-auto aspect-square object-cover" />
                <p className="text-[10px] text-slate-400">White: +1, Black: -1, Gray: 0</p>
              </div>
            </div>

            {/* Metrics Breakdown */}
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
              <div className="p-3 bg-slate-50 dark:bg-slate-800/60 rounded-xl">
                <span className="text-[11px] text-slate-500 font-bold uppercase">PSNR</span>
                <p className="text-lg font-bold text-slate-900 dark:text-white">{analysis.metrics.psnr} dB</p>
              </div>
              <div className="p-3 bg-slate-50 dark:bg-slate-800/60 rounded-xl">
                <span className="text-[11px] text-slate-500 font-bold uppercase">SSIM</span>
                <p className="text-lg font-bold text-slate-900 dark:text-white">{analysis.metrics.ssim}</p>
              </div>
              <div className="p-3 bg-slate-50 dark:bg-slate-800/60 rounded-xl">
                <span className="text-[11px] text-slate-500 font-bold uppercase">Change Rate</span>
                <p className="text-lg font-bold text-slate-900 dark:text-white">{(analysis.metrics.change_rate * 100).toFixed(2)}%</p>
              </div>
              <div className="p-3 bg-slate-50 dark:bg-slate-800/60 rounded-xl">
                <span className="text-[11px] text-slate-500 font-bold uppercase">FCC (2nd Order)</span>
                <p className="text-lg font-bold text-blue-600 dark:text-blue-400">{analysis.metrics.fcc2.toFixed(5)}</p>
              </div>
              <div className="p-3 bg-slate-50 dark:bg-slate-800/60 rounded-xl">
                <span className="text-[11px] text-slate-500 font-bold uppercase">FCC (3rd Order)</span>
                <p className="text-lg font-bold text-slate-900 dark:text-white">{analysis.metrics.fcc3.toFixed(5)}</p>
              </div>
              <div className="p-3 bg-slate-50 dark:bg-slate-800/60 rounded-xl">
                <span className="text-[11px] text-slate-500 font-bold uppercase">FCC (4th Order)</span>
                <p className="text-lg font-bold text-slate-900 dark:text-white">{analysis.metrics.fcc4.toFixed(6)}</p>
              </div>
            </div>

            {/* Steganalysis Security Detection Scores */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
              <div className="p-4 bg-slate-50 dark:bg-slate-800/60 rounded-xl border border-slate-200 dark:border-slate-800 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-bold text-slate-800 dark:text-slate-200">SRNet-lite CNN Stego Probability</span>
                  <span className={`text-sm font-bold ${analysis.srnet_score > 0.5 ? 'text-amber-500' : 'text-emerald-500'}`}>
                    {(analysis.srnet_score * 100).toFixed(1)}%
                  </span>
                </div>
                <div className="w-full bg-slate-200 dark:bg-slate-700 h-2.5 rounded-full overflow-hidden">
                  <div
                    className={`h-full transition-all duration-500 ${analysis.srnet_score > 0.5 ? 'bg-amber-500' : 'bg-emerald-500'}`}
                    style={{ width: `${analysis.srnet_score * 100}%` }}
                  />
                </div>
                <p className="text-[11px] text-slate-500">
                  Ideal security: 50% (random guess probability). Low detection probability indicates superior imperceptibility.
                </p>
              </div>

              <div className="p-4 bg-slate-50 dark:bg-slate-800/60 rounded-xl border border-slate-200 dark:border-slate-800 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-bold text-slate-800 dark:text-slate-200">SPAM 686-D Markov Transition L2 Norm</span>
                  <span className="text-sm font-bold text-indigo-600 dark:text-indigo-400">
                    {analysis.spam_norm}
                  </span>
                </div>
                <p className="text-[11px] text-slate-500">
                  Subtractive Pixel Adjacency Matrix 2nd-order Markov transition probabilities along horizontal, vertical, and diagonal difference directions.
                </p>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
