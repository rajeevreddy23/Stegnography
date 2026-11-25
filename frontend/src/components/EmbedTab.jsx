import React, { useState } from 'react';
import { Upload, Download, Sparkles, Sliders, Lock, Key, ShieldCheck, AlertCircle } from 'lucide-react';

export default function EmbedTab() {
  const [coverFile, setCoverFile] = useState(null);
  const [coverPreview, setCoverPreview] = useState(null);
  const [message, setMessage] = useState('Secret Data: Confirmed 100% Round-Trip with CMD-Stego+ Adaptive Clustering!');
  const [password, setPassword] = useState('SeniorEngineer_2026');
  const [stegoKey, setStegoKey] = useState('StegoKey_Alpha');
  const [scheme, setScheme] = useState('HILL');
  const [L, setL] = useState(2);
  const [alpha, setAlpha] = useState(9.0);
  const [adaptiveAlpha, setAdaptiveAlpha] = useState(true);
  const [neighborhood8, setNeighborhood8] = useState(true);
  const [keyRandomized, setKeyRandomized] = useState(true);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [result, setResult] = useState(null);

  const handleCoverChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      setCoverFile(file);
      setCoverPreview(URL.createObjectURL(file));
      setResult(null);
      setError(null);
    }
  };

  const handleEmbed = async () => {
    if (!coverFile) {
      setError('Please upload a cover image first.');
      return;
    }
    if (!message) {
      setError('Please enter a secret message to embed.');
      return;
    }

    setLoading(true);
    setError(null);

    const formData = new FormData();
    formData.append('cover_file', coverFile);
    formData.append('message', message);
    if (password) formData.append('password', password);
    if (stegoKey) formData.append('stego_key', stegoKey);
    formData.append('scheme', scheme);
    formData.append('L', L);
    formData.append('alpha', alpha);
    formData.append('adaptive_alpha', adaptiveAlpha);
    formData.append('neighborhood_8', neighborhood8);
    formData.append('key_randomized', keyRandomized);

    try {
      const response = await fetch('/api/embed', {
        method: 'POST',
        body: formData,
      });

      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || 'Embedding failed.');
      }
      setResult(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-8 max-w-6xl mx-auto">
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* Left Column: Configuration Controls */}
        <div className="lg:col-span-5 space-y-6">
          <div className="bg-white dark:bg-slate-900 rounded-2xl p-6 border border-slate-200 dark:border-slate-800 shadow-sm space-y-5">
            <h3 className="font-semibold text-lg text-slate-900 dark:text-white flex items-center gap-2">
              <Upload className="w-5 h-5 text-blue-600" />
              1. Upload Cover Image
            </h3>

            <div className="border-2 border-dashed border-slate-300 dark:border-slate-700 rounded-xl p-4 text-center hover:border-blue-500 transition-colors">
              <input
                type="file"
                id="cover-upload"
                accept="image/png, image/jpeg, image/bmp, image/pgm"
                onChange={handleCoverChange}
                className="hidden"
              />
              <label htmlFor="cover-upload" className="cursor-pointer block">
                {coverPreview ? (
                  <div className="relative group">
                    <img
                      src={coverPreview}
                      alt="Cover Preview"
                      className="max-h-48 mx-auto rounded-lg object-contain shadow-sm"
                    />
                    <div className="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 flex items-center justify-center text-white text-xs font-medium rounded-lg transition-opacity">
                      Click to Change Cover
                    </div>
                  </div>
                ) : (
                  <div className="py-8">
                    <Upload className="w-10 h-10 text-slate-400 mx-auto mb-2" />
                    <span className="text-sm font-medium text-blue-600 dark:text-blue-400">Choose an 8-bit Grayscale Image</span>
                    <p className="text-xs text-slate-500 mt-1">PNG, JPG, BMP, PGM (up to 512×512)</p>
                  </div>
                )}
              </label>
            </div>

            <div className="space-y-4 pt-2">
              <div>
                <label className="block text-xs font-semibold uppercase text-slate-500 dark:text-slate-400 mb-1">
                  Secret Message
                </label>
                <textarea
                  rows={3}
                  value={message}
                  onChange={(e) => setMessage(e.target.value)}
                  placeholder="Type secret text payload..."
                  className="w-full text-sm rounded-lg border border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 p-2.5 text-slate-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:outline-none"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold uppercase text-slate-500 dark:text-slate-400 mb-1 flex items-center gap-1">
                    <Lock className="w-3.5 h-3.5 text-amber-500" /> Password (AES-256)
                  </label>
                  <input
                    type="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="Optional encryption key"
                    className="w-full text-sm rounded-lg border border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 p-2 text-slate-900 dark:text-white"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold uppercase text-slate-500 dark:text-slate-400 mb-1 flex items-center gap-1">
                    <Key className="w-3.5 h-3.5 text-indigo-500" /> Stego Key
                  </label>
                  <input
                    type="text"
                    value={stegoKey}
                    onChange={(e) => setStegoKey(e.target.value)}
                    placeholder="Lattice seed"
                    className="w-full text-sm rounded-lg border border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 p-2 text-slate-900 dark:text-white"
                  />
                </div>
              </div>
            </div>
          </div>

          {/* Algorithm Parameters & Novel Improvements */}
          <div className="bg-white dark:bg-slate-900 rounded-2xl p-6 border border-slate-200 dark:border-slate-800 shadow-sm space-y-5">
            <h3 className="font-semibold text-lg text-slate-900 dark:text-white flex items-center gap-2">
              <Sliders className="w-5 h-5 text-indigo-600" />
              2. Parameters & Novel Enhancements
            </h3>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-semibold text-slate-600 dark:text-slate-400 mb-1">
                  Baseline Distortion
                </label>
                <select
                  value={scheme}
                  onChange={(e) => setScheme(e.target.value)}
                  className="w-full text-sm rounded-lg border border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 p-2 text-slate-900 dark:text-white"
                >
                  <option value="HILL">HILL (Default)</option>
                  <option value="S-UNIWARD">S-UNIWARD</option>
                  <option value="WOW">WOW</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-600 dark:text-slate-400 mb-1">
                  Lattice L: {L} ({L}×{L} = {L * L} Sub-images)
                </label>
                <input
                  type="range"
                  min={2}
                  max={8}
                  step={2}
                  value={L}
                  onChange={(e) => setL(parseInt(e.target.value))}
                  className="w-full mt-2"
                />
              </div>
            </div>

            <div>
              <div className="flex justify-between text-xs font-semibold text-slate-600 dark:text-slate-400 mb-1">
                <span>Clustering Parameter α: {alpha}</span>
                <span className="text-slate-400">Default: 9.0</span>
              </div>
              <input
                type="range"
                min={3}
                max={17}
                step={2}
                value={alpha}
                onChange={(e) => setAlpha(parseFloat(e.target.value))}
                className="w-full"
              />
            </div>

            {/* Novel Improvement Toggles */}
            <div className="pt-2 border-t border-slate-100 dark:border-slate-800 space-y-3">
              <span className="text-xs font-bold uppercase tracking-wider text-blue-600 dark:text-blue-400">
                Novel Contributions (Switchable)
              </span>

              <label className="flex items-center justify-between text-sm cursor-pointer p-2 rounded-lg hover:bg-slate-50 dark:hover:bg-slate-800/60">
                <div>
                  <span className="font-medium text-slate-800 dark:text-slate-200">A. Adaptive-α Modulation</span>
                  <p className="text-xs text-slate-500">Scales α by local texture complexity</p>
                </div>
                <input
                  type="checkbox"
                  checked={adaptiveAlpha}
                  onChange={(e) => setAdaptiveAlpha(e.target.checked)}
                  className="w-4 h-4 text-blue-600 rounded"
                />
              </label>

              <label className="flex items-center justify-between text-sm cursor-pointer p-2 rounded-lg hover:bg-slate-50 dark:hover:bg-slate-800/60">
                <div>
                  <span className="font-medium text-slate-800 dark:text-slate-200">B. Key-based Randomization</span>
                  <p className="text-xs text-slate-500">Permutes lattice offsets & STC chaining</p>
                </div>
                <input
                  type="checkbox"
                  checked={keyRandomized}
                  onChange={(e) => setKeyRandomized(e.target.checked)}
                  className="w-4 h-4 text-blue-600 rounded"
                />
              </label>

              <label className="flex items-center justify-between text-sm cursor-pointer p-2 rounded-lg hover:bg-slate-50 dark:hover:bg-slate-800/60">
                <div>
                  <span className="font-medium text-slate-800 dark:text-slate-200">C. 8-Neighbor Weighted Voting</span>
                  <p className="text-xs text-slate-500">Orthogonal 1.0, Diagonal 0.5 weights</p>
                </div>
                <input
                  type="checkbox"
                  checked={neighborhood8}
                  onChange={(e) => setNeighborhood8(e.target.checked)}
                  className="w-4 h-4 text-blue-600 rounded"
                />
              </label>
            </div>

            <button
              onClick={handleEmbed}
              disabled={loading}
              className="w-full py-3 px-4 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white rounded-xl font-semibold shadow-md shadow-blue-500/25 flex items-center justify-center gap-2 disabled:opacity-50 transition-all cursor-pointer"
            >
              {loading ? (
                <span>Executing Viterbi Trellis Embedding...</span>
              ) : (
                <>
                  <Sparkles className="w-5 h-5" />
                  <span>Execute CMD-Stego+ Embedding</span>
                </>
              )}
            </button>

            {error && (
              <div className="p-3 bg-red-50 dark:bg-red-900/30 border border-red-200 dark:border-red-800 rounded-lg text-red-700 dark:text-red-300 text-xs flex items-center gap-2">
                <AlertCircle className="w-4 h-4 shrink-0" />
                <span>{error}</span>
              </div>
            )}
          </div>
        </div>

        {/* Right Column: Visualization & Results */}
        <div className="lg:col-span-7 space-y-6">
          {result ? (
            <div className="bg-white dark:bg-slate-900 rounded-2xl p-6 border border-slate-200 dark:border-slate-800 shadow-sm space-y-6">
              <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-800 pb-4">
                <div>
                  <h3 className="font-bold text-xl text-slate-900 dark:text-white">Embedding Output & Heatmap</h3>
                  <p className="text-xs text-slate-500">Run ID: {result.run_id}</p>
                </div>
                <a
                  href={result.stego_image}
                  download={`stego_${result.run_id}.png`}
                  className="px-3.5 py-2 bg-blue-50 text-blue-700 hover:bg-blue-100 dark:bg-blue-900/40 dark:text-blue-300 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-colors"
                >
                  <Download className="w-4 h-4" />
                  Download Stego PNG
                </a>
              </div>

              {/* Visual Comparisons: Cover vs Stego vs Difference Heatmap */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="space-y-1.5 text-center">
                  <span className="text-xs font-semibold text-slate-600 dark:text-slate-400">Cover Image</span>
                  <img src={result.cover_image} alt="Cover" className="rounded-lg border border-slate-200 dark:border-slate-800 mx-auto aspect-square object-cover" />
                </div>
                <div className="space-y-1.5 text-center">
                  <span className="text-xs font-semibold text-blue-600 dark:text-blue-400">Stego Image</span>
                  <img src={result.stego_image} alt="Stego" className="rounded-lg border border-blue-300 dark:border-blue-700 mx-auto aspect-square object-cover" />
                </div>
                <div className="space-y-1.5 text-center">
                  <span className="text-xs font-semibold text-purple-600 dark:text-purple-400">
                    Difference Heatmap (Fig. 7)
                  </span>
                  <img src={result.diff_heatmap} alt="Difference Heatmap" className="rounded-lg border border-purple-300 dark:border-purple-700 mx-auto aspect-square object-cover" />
                  <p className="text-[10px] text-slate-400">White: +1, Black: -1, Gray: 0</p>
                </div>
              </div>

              {/* Metrics Grid */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-4 border-t border-slate-100 dark:border-slate-800">
                <div className="p-3 bg-slate-50 dark:bg-slate-800/60 rounded-xl">
                  <span className="text-[11px] text-slate-500 uppercase font-bold">PSNR</span>
                  <p className="text-lg font-bold text-slate-900 dark:text-white">{result.metrics.psnr} dB</p>
                </div>
                <div className="p-3 bg-slate-50 dark:bg-slate-800/60 rounded-xl">
                  <span className="text-[11px] text-slate-500 uppercase font-bold">SSIM</span>
                  <p className="text-lg font-bold text-slate-900 dark:text-white">{result.metrics.ssim}</p>
                </div>
                <div className="p-3 bg-slate-50 dark:bg-slate-800/60 rounded-xl">
                  <span className="text-[11px] text-slate-500 uppercase font-bold">Change Rate</span>
                  <p className="text-lg font-bold text-slate-900 dark:text-white">{(result.stats.change_rate * 100).toFixed(2)}%</p>
                </div>
                <div className="p-3 bg-slate-50 dark:bg-slate-800/60 rounded-xl">
                  <span className="text-[11px] text-slate-500 uppercase font-bold">FCC (2nd-Order)</span>
                  <p className="text-lg font-bold text-blue-600 dark:text-blue-400">{result.metrics.fcc2.toFixed(5)}</p>
                </div>
                <div className="p-3 bg-slate-50 dark:bg-slate-800/60 rounded-xl">
                  <span className="text-[11px] text-slate-500 uppercase font-bold">Total Changes</span>
                  <p className="text-sm font-semibold text-slate-900 dark:text-white">
                    {result.stats.changes} (+{result.stats.pos_changes} / -{result.stats.neg_changes})
                  </p>
                </div>
                <div className="p-3 bg-slate-50 dark:bg-slate-800/60 rounded-xl">
                  <span className="text-[11px] text-slate-500 uppercase font-bold">Payload Rate</span>
                  <p className="text-sm font-semibold text-slate-900 dark:text-white">{result.stats.bpp.toFixed(4)} bpp</p>
                </div>
                <div className="p-3 bg-slate-50 dark:bg-slate-800/60 rounded-xl">
                  <span className="text-[11px] text-slate-500 uppercase font-bold">Embed Time</span>
                  <p className="text-sm font-semibold text-slate-900 dark:text-white">{result.metrics.embed_time_ms} ms</p>
                </div>
                <div className="p-3 bg-slate-50 dark:bg-slate-800/60 rounded-xl">
                  <span className="text-[11px] text-slate-500 uppercase font-bold">SRNet Stego Prob</span>
                  <p className={`text-sm font-semibold ${result.srnet_score > 0.5 ? 'text-amber-500' : 'text-emerald-500'}`}>
                    {(result.srnet_score * 100).toFixed(1)}%
                  </p>
                </div>
              </div>
            </div>
          ) : (
            <div className="bg-slate-50 dark:bg-slate-900/40 rounded-2xl p-12 border border-slate-200 dark:border-slate-800 text-center space-y-3">
              <ShieldCheck className="w-16 h-16 text-slate-300 dark:text-slate-700 mx-auto" />
              <h4 className="font-semibold text-slate-700 dark:text-slate-300">Ready for Embedding</h4>
              <p className="text-sm text-slate-500 max-w-md mx-auto">
                Configure your cover image and payload parameters on the left and click "Execute CMD-Stego+ Embedding" to view real-time difference clustering and metrics.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
