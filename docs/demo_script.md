# CMD-Stego+: Live Demonstration Walkthrough Script

This step-by-step demonstration script guides you through presenting the **CMD-Stego+** system during your capstone project defense, project review, or viva evaluation.

---

## 1. Environment Startup (30 Seconds)

Open two terminals:

### Terminal 1: Backend API (FastAPI)
```bash
python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```
*Expected log:* `Application startup complete. Uvicorn running on http://0.0.0.0:8000`

### Terminal 2: Frontend Web App (Vite React)
```bash
cd frontend
npm run dev
```
*Expected log:* `Local: http://localhost:5173/`

Navigate in your browser to: **`http://localhost:5173`**

---

## 2. Step 1: Demonstrate Embedding (Embed Tab)

1. **Cover Image Upload:**
   - Under **"1. Upload Cover Image"**, click the upload area and select any cover image from `data/covers/` (e.g. `cover_00001.png`), or upload any 8-bit grayscale image.
   - *Observation:* The cover preview loads instantly.

2. **Payload & Security Configuration:**
   - Enter secret text in **Secret Message**:  
     `"CMD-Stego+ Confidential Payload: Confirmed 100% Bit-Exact Recovery over Syndrome-Trellis Codes!"`
   - Enter Password: `"SeniorEngineer_2026"` *(Activates AES-256-GCM authenticated encryption)*.
   - Enter Stego Key: `"StegoKey_Alpha"` *(Activates key-based lattice permutation)*.

3. **Algorithm & Novel Improvement Controls:**
   - Select **Baseline Distortion**: `HILL`.
   - Adjust **Lattice $L$**: Keep at `2` ($2 \times 2 = 4$ sub-images).
   - Adjust **Clustering Parameter $\alpha$**: Keep at `9.0` (paper default).
   - Notice the **three novel switches**:
     - [x] **A. Adaptive-$\alpha$ Modulation** *(scales $\alpha$ by local 5x5 variance)*
     - [x] **B. Key-based Randomization** *(permutes sub-image order & pixel sequences)*
     - [x] **C. 8-Neighbor Weighted Voting** *(orthogonal 1.0, diagonal 0.5)*

4. **Execute Embedding:**
   - Click **"Execute CMD-Stego+ Embedding"**.
   - *Observation:* The Numba JIT-accelerated Viterbi trellis executes in ~200–400 ms.
   - *Review the Results Panel:*
     - **Cover vs. Stego vs. Difference Heatmap (Fig. 7):** Point out how $+1$ modifications (white) and $-1$ modifications (black) form spatial clusters rather than scattered salt-and-pepper noise.
     - **Metrics Cards:** Highlight PSNR (~56–68 dB), SSIM (> 0.996), Change Rate, and the positive $FCC^{(2)}$ value indicating directional correlation.
     - Click **"Download Stego PNG"** to save the generated image to disk as `stego.png`.

---

## 3. Step 2: Demonstrate Extraction & Authentication (Extract Tab)

1. Click on the **"Extract"** tab in the navigation bar.
2. Upload the newly generated `stego.png`.
3. Enter the same password: `"SeniorEngineer_2026"`.
4. Enter the same stego key: `"StegoKey_Alpha"`.
5. Click **"Extract & Authenticate Payload"**.
6. *Observation:*
   - A green success card appears: **"Payload Authenticated & Decrypted Perfectly (CRC32 Valid)"**.
   - The recovered plaintext displays with 100% bit-exact accuracy.
   - The metadata badge displays the exact payload byte size and enabled security flags.

7. **Tamper & Authentication Resistance Test (Examiner Wow-Factor):**
   - Change the password to `"WrongPassword"`.
   - Click **"Extract & Authenticate Payload"**.
   - *Observation:* An immediate red error appears: **"Authentication failed: Incorrect password or corrupted stego data."**
   - *Explanation to examiners:* Proves that the AES-256-GCM authentication tag and CRC32 prevent malicious tampering or unauthorized eavesdropping.

---

## 4. Step 3: Forensic & Statistical Analysis (Analyze Tab)

1. Click on the **"Analyze"** tab.
2. Upload `cover_00001.png` on the left and `stego.png` on the right.
3. Click **"Run Comparative Analysis"**.
4. *Observation:*
   - Side-by-side visualization with the Paper Fig. 7 difference heatmap.
   - Quantitative metrics table showing PSNR, SSIM, Change Rate, $FCC^{(2)}$, $FCC^{(3)}$, and $FCC^{(4)}$.
   - Live **SRNet-lite CNN Stego Probability score** and **SPAM 686-D Markov transition norm**.

---

## 5. Step 4: Experimental Dashboard & Publication Plots (Experiments Tab)

1. Click on the **"Experiments"** tab.
2. Point out the **four interactive Recharts graphs**:
   - **Fig. 14 (Detection Error vs. Relative Payload):** Show how HILL-CMD+ maintains the highest detection error $P_E$ across 0.05 to 0.50 bpp.
   - **Fig. 11 ($FCC^{(2)}$ vs. $\alpha$):** Show how increasing $\alpha$ from 3 to 15 increases modification clustering.
   - **Fig. 12 (Change Rate vs. $\alpha$):** Show the change rate saturation curve.
   - **Fig. 19 (Ablation Analysis):** Show the incremental gain of each novel component (Baseline $\to$ HILL-CMD $\to$ +A $\to$ +B $\to$ +C $\to$ Full HILL-CMD+).
3. Under **"Publication-Quality High-Resolution Figures (300 DPI)"**, click between `FIG14`, `FIG11`, `FIG12`, `FIG19` to show the pre-rendered academic plots matching IEEE TIFS formatting.

---

## 6. Step 5: Operations History (History Tab)

1. Click on the **"History"** tab.
2. Show the persistent session log recording every embed and extract event with timestamp, run ID, payload rate, and metrics.
