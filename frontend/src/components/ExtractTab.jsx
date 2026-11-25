import React, { useState } from 'react';
import { Lock, Unlock, Download, Key, CheckCircle2, AlertCircle, FileText } from 'lucide-react';

export default function ExtractTab() {
  const [stegoFile, setStegoFile] = useState(null);
  const [stegoPreview, setStegoPreview] = useState(null);
  const [password, setPassword] = useState('SeniorEngineer_2026');
  const [stegoKey, setStegoKey] = useState('StegoKey_Alpha');
  const [L, setL] = useState(2);
  const [keyRandomized, setKeyRandomized] = useState(true);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [result, setResult] = useState(null);

  const handleStegoChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      setStegoFile(file);
      setStegoPreview(URL.createObjectURL(file));
      setResult(null);
      setError(null);
    }
  };

  const handleExtract = async () => {
    if (!stegoFile) {
      setError('Please upload a stego image.');
      return;
    }

    setLoading(true);
    setError(null);

    const formData = new FormData();
    formData.append('stego_file', stegoFile);
    if (password) formData.append('password', password);
    if (stegoKey) formData.append('stego_key', stegoKey);
    formData.append('L', L);
    formData.append('key_randomized', keyRandomized);

    try {
      const response = await fetch('/api/extract', {
        method: 'POST',
        body: formData,
      });

      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || 'Extraction failed.');
      }
      setResult(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-8 max-w-4xl mx-auto">
      <div className="bg-white dark:bg-slate-900 rounded-2xl p-6 border border-slate-200 dark:border-slate-800 shadow-sm space-y-6">
        <div className="flex items-center gap-3 border-b border-slate-100 dark:border-slate-800 pb-4">
          <div className="p-2.5 bg-blue-50 dark:bg-blue-900/40 rounded-xl text-blue-600 dark:text-blue-400">
            <Unlock className="w-6 h-6" />
          </div>
          <div>
            <h3 className="font-bold text-xl text-slate-900 dark:text-white">Recover Secret Payload</h3>
            <p className="text-xs text-slate-500">Autonomous STC syndrome extraction with AES-256-GCM authentication</p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Stego Upload */}
          <div className="border-2 border-dashed border-slate-300 dark:border-slate-700 rounded-xl p-4 text-center hover:border-blue-500 transition-colors">
            <input
              type="file"
              id="stego-upload"
              accept="image/png, image/jpeg, image/bmp, image/pgm"
              onChange={handleStegoChange}
              className="hidden"
            />
            <label htmlFor="stego-upload" className="cursor-pointer block">
              {stegoPreview ? (
                <div className="relative group">
                  <img
                    src={stegoPreview}
                    alt="Stego Preview"
                    className="max-h-56 mx-auto rounded-lg object-contain shadow-sm"
                  />
                  <div className="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 flex items-center justify-center text-white text-xs font-medium rounded-lg transition-opacity">
                    Click to Change Stego Image
                  </div>
                </div>
              ) : (
                <div className="py-12">
                  <Lock className="w-10 h-10 text-slate-400 mx-auto mb-2" />
                  <span className="text-sm font-medium text-blue-600 dark:text-blue-400">Choose Stego Image</span>
                  <p className="text-xs text-slate-500 mt-1">PNG containing embedded bitstream</p>
                </div>
              )}
            </label>
          </div>

          {/* Extraction Keys & Parameters */}
          <div className="space-y-4">
            <div>
              <label className="block text-xs font-semibold uppercase text-slate-500 dark:text-slate-400 mb-1 flex items-center gap-1">
                <Lock className="w-3.5 h-3.5 text-amber-500" /> Password (If Encrypted)
              </label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Enter decryption password..."
                className="w-full text-sm rounded-lg border border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 p-2.5 text-slate-900 dark:text-white"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold uppercase text-slate-500 dark:text-slate-400 mb-1 flex items-center gap-1">
                <Key className="w-3.5 h-3.5 text-indigo-500" /> Stego Key (Lattice Permutation)
              </label>
              <input
                type="text"
                value={stegoKey}
                onChange={(e) => setStegoKey(e.target.value)}
                placeholder="Enter stego key seed..."
                className="w-full text-sm rounded-lg border border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 p-2.5 text-slate-900 dark:text-white"
              />
            </div>

            <div className="grid grid-cols-2 gap-3 pt-2">
              <div>
                <label className="block text-xs font-semibold text-slate-600 dark:text-slate-400 mb-1">
                  Lattice L: {L}
                </label>
                <select
                  value={L}
                  onChange={(e) => setL(parseInt(e.target.value))}
                  className="w-full text-sm rounded-lg border border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 p-2 text-slate-900 dark:text-white"
                >
                  <option value={2}>L = 2 (4 Sub-images)</option>
                  <option value={4}>L = 4 (16 Sub-images)</option>
                  <option value={8}>L = 8 (64 Sub-images)</option>
                </select>
              </div>

              <div className="flex items-center pt-5">
                <label className="flex items-center gap-2 text-xs font-medium text-slate-700 dark:text-slate-300 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={keyRandomized}
                    onChange={(e) => setKeyRandomized(e.target.checked)}
                    className="w-4 h-4 text-blue-600 rounded"
                  />
                  <span>Key-Randomized</span>
                </label>
              </div>
            </div>

            <button
              onClick={handleExtract}
              disabled={loading}
              className="w-full py-3 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white rounded-xl font-semibold shadow-md shadow-blue-500/25 flex items-center justify-center gap-2 transition-all cursor-pointer disabled:opacity-50 mt-4"
            >
              {loading ? 'Performing Syndrome Trellis Decoding...' : 'Extract & Authenticate Payload'}
            </button>
          </div>
        </div>

        {error && (
          <div className="p-4 bg-red-50 dark:bg-red-900/30 border border-red-200 dark:border-red-800 rounded-xl text-red-700 dark:text-red-300 text-sm flex items-center gap-2">
            <AlertCircle className="w-5 h-5 shrink-0" />
            <div>
              <p className="font-semibold">Extraction or Authentication Failed</p>
              <p className="text-xs mt-0.5">{error}</p>
            </div>
          </div>
        )}

        {result && (
          <div className="p-6 bg-emerald-50 dark:bg-emerald-950/30 border border-emerald-200 dark:border-emerald-800 rounded-2xl space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 text-emerald-700 dark:text-emerald-300 font-bold">
                <CheckCircle2 className="w-5 h-5" />
                <span>Payload Authenticated & Decrypted Perfectly (CRC32 Valid)</span>
              </div>
              <span className="text-xs px-2.5 py-1 bg-emerald-100 dark:bg-emerald-900/60 text-emerald-800 dark:text-emerald-200 rounded-full font-semibold">
                {result.payload_length} Bytes
              </span>
            </div>

            <div>
              <label className="block text-xs font-semibold text-emerald-800 dark:text-emerald-400 uppercase mb-1">
                Recovered Message:
              </label>
              <div className="p-3 bg-white dark:bg-slate-900 rounded-xl border border-emerald-200 dark:border-emerald-800 font-mono text-sm text-slate-800 dark:text-slate-100 whitespace-pre-wrap select-all">
                {result.message}
              </div>
            </div>

            <div className="flex flex-wrap gap-2 text-[11px] text-slate-500 dark:text-slate-400 pt-2 border-t border-emerald-200/60 dark:border-emerald-800/60">
              <span className="px-2 py-0.5 bg-white dark:bg-slate-800 rounded">Encrypted: {result.metadata.encrypted ? 'AES-256-GCM' : 'No'}</span>
              <span className="px-2 py-0.5 bg-white dark:bg-slate-800 rounded">Adaptive-α: {result.metadata.adaptive_alpha ? 'Yes' : 'No'}</span>
              <span className="px-2 py-0.5 bg-white dark:bg-slate-800 rounded">8-Neighborhood: {result.metadata.neighborhood_8 ? 'Yes' : 'No'}</span>
              <span className="px-2 py-0.5 bg-white dark:bg-slate-800 rounded">Key Randomized: {result.metadata.key_randomized ? 'Yes' : 'No'}</span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
