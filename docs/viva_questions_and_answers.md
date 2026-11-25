# CMD-Stego+: Final Review Viva Q&A Guide (25 Questions & Answers)

This comprehensive reference document prepares you for technical inquiries from university evaluators, external examiners, and faculty defense panels.

---

### Q1: What is the core problem addressed by this project?
**Answer:** Traditional spatial steganography algorithms (such as standard HILL, S-UNIWARD, and WOW) are based on the **additive distortion minimization framework**. They treat each pixel's modification cost independently, ignoring the modification directions of its adjacent neighbors. Consequently, modifications of opposing signs ($+1$ and $-1$) frequently scatter in close spatial proximity, introducing artificial high-frequency variations. These unnatural phase/sign transitions are readily detected by modern steganalysis models such as SPAM (Subtractive Pixel Adjacency Matrix) and deep neural networks like SRNet. CMD-Stego+ resolves this vulnerability by clustering modifications of the same sign into cohesive spatial regions.

---

### Q2: On which seminal research paper is CMD-Stego+ founded?
**Answer:** It is founded on the IEEE Transactions on Information Forensics and Security (TIFS 2015) paper:
> **"A Strategy of Clustering Modification Directions in Spatial Image Steganography"**  
> Authors: Bin Li, Meng Wang, Jiwu Huang, and Ping Tan (Vol. 10, No. 9, Sept. 2015).

---

### Q3: What is the mathematical formulation of the HILL distortion function?
**Answer:** HILL (High-pass, Low-pass, Low-pass) computes initial spatial costs $C$ via:
$$C = \frac{1}{|X \otimes H| \otimes P_1 + 10^{-10}} \otimes P_2$$
Where:
- $H$ is a $3 \times 3$ Ker-Böhme high-pass filter: $\begin{bmatrix}-1 & 2 & -1 \\ 2 & -4 & 2 \\ -1 & 2 & -1\end{bmatrix}$
- $P_1$ is a $3 \times 3$ averaging filter ($\frac{1}{9} \mathbf{1}_{3 \times 3}$) for initial residual smoothing.
- $P_2$ is a $15 \times 15$ averaging filter ($\frac{1}{225} \mathbf{1}_{15 \times 15}$) to disperse cost into neighborhood textures.
- $\otimes$ denotes 2D convolution with mirror reflection padding (`BORDER_REFLECT`).

---

### Q4: Why is mirror padding (BORDER_REFLECT) critical?
**Answer:** Zero-padding causes sharp intensity drops at the image boundaries, artificially inflating high-pass residuals and erroneously assigning very low modification costs to border pixels. Mirror padding maintains continuous intensity gradients, preventing edge-steganalysis leaks.

---

### Q5: How does the sub-image decomposition work in CMD?
**Answer:** The image grid is partitioned into $L \times L$ interleaved sub-images (default $L=2 \implies 4$ sub-images $S_1, S_2, S_3, S_4$). For pixel coordinates $(r, c)$, its sub-image assignment is determined by $(r \bmod L, c \bmod L)$. Pixels within any single sub-image are separated by a spatial distance of at least $L$ pixels, ensuring that modifications inside sub-image $S_t$ do not directly interfere with each other during that step's trellis encoding.

---

### Q6: How does the directional cost update rule work in sub-image $t > 1$?
**Answer:** For each pixel $(r, c) \in S_t$:
1. We compute the current difference image $D = Y - X \in \{-1, 0, +1\}$.
2. We inspect its neighbors in $D$ and count positive modifications $N_+$ and negative modifications $N_-$.
3. If $N_+ > N_-$, the positive cost is discounted: $\rho_+(r,c) = c(r,c) / \alpha$, while $\rho_-(r,c) = c(r,c)$.
4. If $N_- > N_+$, the negative cost is discounted: $\rho_-(r,c) = c(r,c) / \alpha$, while $\rho_+(r,c) = c(r,c)$.
5. If $N_+ == N_-$, both costs remain $c(r,c)$.
The default clustering factor is $\alpha = 9.0$.

---

### Q7: What are the wet costs, and why are they set to $10^{10}$?
**Answer:** In 8-bit grayscale images, pixel intensities are bounded in $[0, 255]$. Modifying a pixel of value 0 by $-1$ causes underflow to $-1$ or wraps to $255$; modifying 255 by $+1$ causes overflow to 256. To prevent truncation artifacts or illegal pixel ranges:
$$\rho_-(r,c) = 10^{10} \quad \text{if } X(r,c) == 0$$
$$\rho_+(r,c) = 10^{10} \quad \text{if } X(r,c) == 255$$
A cost of $10^{10}$ represents an effectively infinite barrier in the Viterbi path metric, guaranteeing that boundary modifications are strictly avoided.

---

### Q8: What are Syndrome-Trellis Codes (STC), and why are they used instead of LSB replacement?
**Answer:** LSB replacement or matching without coding modifies on average $50\%$ of chosen pixels, resulting in an embedding efficiency of only $2.0$ bits per change. Syndrome-Trellis Codes (Filler et al., 2011) use convolutional parity-check matrices and the Viterbi algorithm to near-optimally embed payload bits with minimal total distortion $\sum \rho_i |y_i - x_i|$, achieving embedding efficiencies often exceeding $4.0$ to $6.0$ bits per change.

---

### Q9: How is STC extraction performed by the receiver?
**Answer:** The receiver requires **no search or optimization**. Given the stego vector $\mathbf{y}$, the receiver computes:
$$\mathbf{m} = \mathbb{H} \cdot (\mathbf{y} \bmod 2) \pmod 2$$
This is a single sparse matrix-vector multiplication in GF(2), executing in $O(n)$ linear time with $100\%$ mathematical determinism.

---

### Q10: How do you achieve ternary embedding with binary STC?
**Answer:** Each pixel $x \in \{0, \dots, 255\}$ has binary LSB parity $b = x \bmod 2$. Notice that:
$$(x + 1) \bmod 2 \equiv (x - 1) \bmod 2 \equiv 1 - (x \bmod 2)$$
Both $+1$ and $-1$ flip the LSB parity bit identically. Therefore, the binary STC trellis determines which pixels should have their parities flipped by setting the flip cost to $\min(\rho_+, \rho_-)$. When the trellis flips a pixel, the embedder chooses the direction ($+1$ or $-1$) that has the lower cost (or the clustered direction dictated by CMD). The receiver extracts from $(y \bmod 2)$, which yields the exact bitstream regardless of whether $+1$ or $-1$ was applied.

---

### Q11: What is Novel Improvement A (Adaptive-$\alpha$)?
**Answer:** The base paper uses a static $\alpha = 9.0$ uniformly across the entire image. However, smooth flat regions cannot tolerate strong clustering without creating visible contouring, whereas complex textured regions can accommodate aggressive clustering. We compute a local $5 \times 5$ sample variance map $V(r,c)$, normalize it to $[0, 1]$ via percentile clipping, and dynamically scale $\alpha$:
$$\alpha(r,c) = \alpha_{min} + (\alpha_{max} - \alpha_{min}) \cdot \tilde{V}(r,c)$$
This focuses clustering where it is most undetectable.

---

### Q12: What is Novel Improvement B (Key-Based Randomization)?
**Answer:** In the base paper, sub-images are visited in a static horizontal zig-zag raster order: $(0,0) \to (0,1) \to (1,1) \to (1,0)$. This violates Kerckhoffs's principle. In CMD-Stego+, a secret stego-key is hashed via SHA-256 to seed a PRNG that permutes the sub-image visitation order, selects random sub-lattice spatial offsets, and pseudo-randomly permutes pixel ordering during trellis chaining. Without the key, an adversary cannot even identify the sub-image boundaries.

---

### Q13: What is Novel Improvement C (8-Neighborhood Weighted Voting)?
**Answer:** The original paper considers only the 4 orthogonal neighbors. CMD-Stego+ extends voting to all 8 spatial neighbors with Euclidean distance weighting:
- Orthogonal neighbors: $(r\pm 1, c), (r, c\pm 1)$ with weight $w_{\text{ortho}} = 1.0$.
- Diagonal neighbors: $(r\pm 1, c\pm 1)$ with weight $w_{\text{diag}} = 0.5$ (since Euclidean distance is $\sqrt{2} \approx 1.414$).
The consensus score $V = \sum w_k D(k)$ triggers directional discounts if $|V| > 0.25$, boosting $FCC^{(2)}$ by $18.1\%$ over 4-neighborhood voting.

---

### Q14: What is Novel Improvement D (Cryptographic Security)?
**Answer:** Before embedding, the payload is framed with:
1. PBKDF2-HMAC-SHA256 (100,000 iterations) key derivation from user password.
2. AES-256-GCM authenticated encryption with a 12-byte random IV and 16-byte authentication tag.
3. 32-bit CRC32 checksum for fast integrity verification.
4. Additional Authenticated Data (AAD) binding header metadata to the ciphertext.
This guarantees that incorrect passwords or data corruptions raise an authentication error rather than outputting garbled text.

---

### Q15: How does autonomous extraction work without manually specifying payload length?
**Answer:** The first 64 pixels of the image store a dedicated 64-bit header using LSB modulation:
- 32-bit Magic identifier: `b'CMDS'`
- 32-bit integer: `total_bits`
The receiver reads the first 64 pixels, verifies the magic bytes, recovers `total_bits`, and autonomously extracts all segments without requiring the user to pass length parameters.

---

### Q16: What is the Feature Continuity / Correlation (FCC) metric?
**Answer:** $FCC^{(2)}$ measures the correlation between adjacent modification directions in $D = Y - X$:
$$FCC^{(2)} = \frac{1}{|\Omega|} \left[ \sum_{i,j} D(i,j) D(i, j+1) + \sum_{i,j} D(i,j) D(i+1, j) \right]$$
In additive embedding (HILL), $FCC^{(2)} \approx 0.004$ (near zero). In CMD-Stego+, $FCC^{(2)} \approx 0.0321$, proving that identical signs cluster together.

---

### Q17: What is the SPAM steganalyzer, and how many features does it extract?
**Answer:** SPAM (Subtractive Pixel Adjacency Matrix, Pevný et al., 2010) models difference arrays $D = X_{i+1} - X_i$ as Markov chains. Truncated to threshold $T=3$ ($2T+1 = 7$ states), it computes second-order transition probabilities along horizontal, vertical, diagonal, and anti-diagonal directions. Averaging directional symmetries yields $343 + 343 = 686$ features.

---

### Q18: What is the SRNet-lite steganalyzer architecture?
**Answer:** Inspired by Boroumand et al. (IEEE TIFS 2018), SRNet-lite uses:
- Layer 1: High-pass residual extraction with unpooled convolutions (preserving weak stego noise).
- Layers 2–4: Deep residual blocks with BatchNorm and LeakyReLU.
- Global Average Pooling (GAP) + Linear classification head.
It outputs the probability $P(\text{stego})$ and evaluates detection error $P_E = (FPR + FNR)/2$.

---

### Q19: What does detection error $P_E = 0.50$ mean?
**Answer:** $P_E = 0.50$ represents a completely random guess (50% accuracy), which is the theoretical ideal of steganographic imperceptibility. Lower $P_E$ indicates that the steganalyzer can reliably distinguish stego images from cover images.

---

### Q20: How do you explain the trade-off between Change Rate and Security in CMD?
**Answer:** When CMD clusters modifications, the change rate is slightly higher than unclustered additive embedding (e.g., $10.4\%$ vs $7.7\%$ at 0.4 bpp). However, because the modifications share signs and follow natural texture contours, the resulting stego image has higher detection error $P_E$ and higher $FCC^{(2)}$. Clustering proves that **where and how modifications are placed is more important than raw change count**.

---

### Q21: What was the speed of your Numba-compiled STC engine?
**Answer:** In our benchmark runs, 10,000 pixels were embedded in $10 \text{ ms}$. A full $512 \times 512$ image (262,144 pixels) embeds in approximately $260 \text{ ms}$ on standard consumer CPUs.

---

### Q22: How does the optimal embedding simulator differ from real STC?
**Answer:** The simulator calculates the theoretical Gibbs-Boltzmann probability distribution $P_+(i) = \frac{e^{-\lambda \rho_+}}{Z}$ using bisection on $\lambda$ to match the target entropy $H(\lambda) = m$ bits. It represents the asymptotic theoretical limit of an infinite-constraint code, whereas STC is a practical, finite-state ($h=7, 8$) encoder that can be extracted bit-exact in real time.

---

### Q23: How were saturated pixels handled during cost recomputation?
**Answer:** Whenever a pixel reached 0, its negative modification cost $\rho_-$ was overwritten with the wet cost $10^{10}$. Whenever a pixel reached 255, its positive modification cost $\rho_+$ was overwritten with $10^{10}$. This guaranteed zero underflow or overflow across all test runs.

---

### Q24: What are the main components of your full-stack web application?
**Answer:**
- **Backend:** Python 3.11/3.13 with FastAPI, NumPy, SciPy, OpenCV, PyTorch, and Numba.
- **Frontend:** React 18, Vite, Tailwind CSS v4, Lucide React icons, and Recharts.
- **Pages:** Embed (interactive parameter tuning), Extract (authenticated recovery), Analyze (side-by-side comparison, Fig. 7 heatmap, live SPAM/CNN scoring), Experiments (interactive charts of real runs), and History (audit log).

---

### Q25: What future research directions could extend this project?
**Answer:**
1. **Color Steganography:** Extending directional clustering across inter-channel RGB color correlations.
2. **JPEG Domain Steganography:** Adapting modification clustering to block-DCT coefficients (such as J-UNIWARD with inter-block clustering).
3. **Adversarial Steganography:** Utilizing gradient-guided adversarial perturbations directly against CNN steganalyzers during the iterative sub-image passes.
