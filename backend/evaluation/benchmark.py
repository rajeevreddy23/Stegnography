"""
Benchmark Execution Engine for CMD-Stego+.
Executes real experimental runs, extracts SPAM 686-D and SRNet features,
evaluates detection error P_E = (FPR + FNR)/2, and outputs verified CSV results.
"""

import os
import time
import pandas as pd
import numpy as np
from typing import List, Dict, Any

from .dataset import prepare_dataset, load_grayscale_image
from ..core.simulator import simulate_embedding
from ..core.metrics import compute_all_metrics
from ..core.steganalysis import extract_spam_686, SteganalysisEnsemble
from ..core.srnet import SRNetLite, train_srnet, evaluate_srnet, StegoDataset
from torch.utils.data import DataLoader


def run_full_benchmark(
    num_images: int = 50,
    results_dir: str = "d:/Stegnography/results/csv",
    models_dir: str = "d:/Stegnography/results/models",
) -> Dict[str, pd.DataFrame]:
    """
    Executes the full suite of experiments:
    1. Payload sweep: 0.05 to 0.5 bpp across baseline and CMD schemes.
    2. Alpha sweep: alpha in {3, 5, 7, 9, 11, 13, 15}.
    3. Lattice sweep: L in {2, 4, 8}.
    4. Ablation study: Baseline vs HILL-CMD vs (+A) vs (+B) vs (+C) vs HILL-CMD+.
    """
    os.makedirs(results_dir, exist_ok=True)
    os.makedirs(models_dir, exist_ok=True)

    print(f"=== Starting CMD-Stego+ Benchmark Evaluation (Dataset: {num_images} images) ===")
    image_paths = prepare_dataset(num_images=num_images, size=256)
    covers = [load_grayscale_image(p, size=256) for p in image_paths]

    # Pre-train SRNet-lite model on a representative subset of cover-stego pairs
    print("Training baseline SRNet-lite steganalyzer on stego pairs...")
    sample_stegos = []
    for c in covers[:min(30, len(covers))]:
        s, _ = simulate_embedding(c, payload_bpp=0.4, scheme="HILL", cmd_enabled=False)
        sample_stegos.append(s)

    srnet_model, _ = train_srnet(
        covers=covers[:len(sample_stegos)],
        stegos=sample_stegos,
        epochs=8,
        batch_size=8,
        save_path=os.path.join(models_dir, "srnet_lite_best.pt"),
    )

    # -------------------------------------------------------------
    # Experiment 1: Payload Sweep (0.05 to 0.5 bpp)
    # -------------------------------------------------------------
    print("\n--- Running Experiment 1: Payload Sweep ---")
    payloads = [0.05, 0.1, 0.2, 0.3, 0.4, 0.5]
    schemes = [
        ("HILL", False, False, False, False),
        ("S-UNIWARD", False, False, False, False),
        ("WOW", False, False, False, False),
        ("HILL-CMD", True, False, False, False),
        ("S-UNIWARD-CMD", True, False, False, False),
        ("HILL-CMD+", True, True, True, True),
    ]

    payload_rows = []
    for p_bpp in payloads:
        print(f"Evaluating payload: {p_bpp} bpp...")
        for name, cmd_en, adapt_a, neigh8, key_rand in schemes:
            base_scheme = "S-UNIWARD" if "UNIWARD" in name else ("WOW" if "WOW" in name else "HILL")
            
            psnr_list, ssim_list, chg_list, fcc2_list, fcc3_list, fcc4_list, time_list = [], [], [], [], [], [], []
            stegos_for_steg = []

            for cov in covers:
                t0 = time.time()
                stego, stats = simulate_embedding(
                    cov,
                    payload_bpp=p_bpp,
                    scheme=base_scheme,
                    cmd_enabled=cmd_en,
                    alpha=9.0,
                    adaptive_alpha=adapt_a,
                    neighborhood_8=neigh8,
                    key_randomized=key_rand,
                )
                t1 = time.time()
                m = compute_all_metrics(cov, stego, embed_time_sec=t1 - t0)

                psnr_list.append(m['psnr'])
                ssim_list.append(m['ssim'])
                chg_list.append(m['change_rate'])
                fcc2_list.append(m['fcc2'])
                fcc3_list.append(m['fcc3'])
                fcc4_list.append(m['fcc4'])
                time_list.append(m['embed_time_ms'])
                stegos_for_steg.append(stego)

            # Evaluate SPAM classification error P_E on 50/50 split
            half = len(covers) // 2
            train_covers, test_covers = covers[:half], covers[half:]
            train_stegos, test_stegos = stegos_for_steg[:half], stegos_for_steg[half:]

            X_train = [extract_spam_686(img) for img in train_covers + train_stegos]
            y_train = np.array([0] * len(train_covers) + [1] * len(train_stegos))
            X_test = [extract_spam_686(img) for img in test_covers + test_stegos]
            y_test = np.array([0] * len(test_covers) + [1] * len(test_stegos))

            clf = SteganalysisEnsemble(classifier_type="lda")
            clf.train(np.array(X_train), y_train)
            spam_res = clf.evaluate(np.array(X_test), y_test)

            # Evaluate SRNet detection error
            test_ds = StegoDataset(test_covers + test_stegos, [0] * len(test_covers) + [1] * len(test_stegos))
            test_loader = DataLoader(test_ds, batch_size=8, shuffle=False)
            srnet_res = evaluate_srnet(srnet_model, test_loader, device=srnet_model.layer1[0].weight.device)

            row = {
                'scheme': name,
                'payload_bpp': p_bpp,
                'psnr': round(float(np.mean(psnr_list)), 2),
                'ssim': round(float(np.mean(ssim_list)), 4),
                'change_rate': round(float(np.mean(chg_list)), 4),
                'fcc2': round(float(np.mean(fcc2_list)), 6),
                'fcc3': round(float(np.mean(fcc3_list)), 6),
                'fcc4': round(float(np.mean(fcc4_list)), 6),
                'spam_pe': spam_res['p_e'],
                'srnet_pe': srnet_res['p_e'],
                'embed_time_ms': round(float(np.mean(time_list)), 1),
            }
            payload_rows.append(row)

    df_payload = pd.DataFrame(payload_rows)
    df_payload.to_csv(os.path.join(results_dir, "payload_sweep.csv"), index=False)
    print("Saved payload_sweep.csv")

    # -------------------------------------------------------------
    # Experiment 2: Alpha Parameter Sweep (alpha in {3, 5, 7, 9, 11, 13, 15})
    # -------------------------------------------------------------
    print("\n--- Running Experiment 2: Alpha Sweep ---")
    alphas = [3, 5, 7, 9, 11, 13, 15]
    alpha_rows = []
    p_fixed = 0.4  # Reference payload

    for a in alphas:
        chg_list, fcc2_list = [], []
        stegos_a = []
        for cov in covers:
            stego, _ = simulate_embedding(cov, payload_bpp=p_fixed, scheme="HILL", cmd_enabled=True, alpha=float(a))
            m = compute_all_metrics(cov, stego)
            chg_list.append(m['change_rate'])
            fcc2_list.append(m['fcc2'])
            stegos_a.append(stego)

        half = len(covers) // 2
        X_train = [extract_spam_686(img) for img in covers[:half] + stegos_a[:half]]
        y_train = np.array([0] * half + [1] * half)
        X_test = [extract_spam_686(img) for img in covers[half:] + stegos_a[half:]]
        y_test = np.array([0] * (len(covers) - half) + [1] * (len(stegos_a) - half))

        clf = SteganalysisEnsemble(classifier_type="lda")
        clf.train(np.array(X_train), y_train)
        spam_res = clf.evaluate(np.array(X_test), y_test)

        test_ds = StegoDataset(covers[half:] + stegos_a[half:], [0] * (len(covers) - half) + [1] * (len(stegos_a) - half))
        test_loader = DataLoader(test_ds, batch_size=8, shuffle=False)
        srnet_res = evaluate_srnet(srnet_model, test_loader, device=srnet_model.layer1[0].weight.device)

        alpha_rows.append({
            'alpha': a,
            'change_rate': round(float(np.mean(chg_list)), 4),
            'fcc2': round(float(np.mean(fcc2_list)), 6),
            'spam_pe': spam_res['p_e'],
            'srnet_pe': srnet_res['p_e'],
        })

    df_alpha = pd.DataFrame(alpha_rows)
    df_alpha.to_csv(os.path.join(results_dir, "alpha_sweep.csv"), index=False)
    print("Saved alpha_sweep.csv")

    # -------------------------------------------------------------
    # Experiment 3: Sub-image Lattice Decomposition Sweep (L in {2, 4, 8})
    # -------------------------------------------------------------
    print("\n--- Running Experiment 3: Lattice Sweep (L) ---")
    lattices = [2, 4, 8]
    lattice_rows = []

    for l_val in lattices:
        chg_list, fcc2_list, time_list = [], [], []
        stegos_l = []
        for cov in covers:
            t0 = time.time()
            stego, _ = simulate_embedding(cov, payload_bpp=p_fixed, scheme="HILL", cmd_enabled=True, L=l_val, alpha=9.0)
            t1 = time.time()
            m = compute_all_metrics(cov, stego, embed_time_sec=t1 - t0)
            chg_list.append(m['change_rate'])
            fcc2_list.append(m['fcc2'])
            time_list.append(m['embed_time_ms'])
            stegos_l.append(stego)

        half = len(covers) // 2
        X_train = [extract_spam_686(img) for img in covers[:half] + stegos_l[:half]]
        y_train = np.array([0] * half + [1] * half)
        X_test = [extract_spam_686(img) for img in covers[half:] + stegos_l[half:]]
        y_test = np.array([0] * (len(covers) - half) + [1] * (len(stegos_l) - half))

        clf = SteganalysisEnsemble(classifier_type="lda")
        clf.train(np.array(X_train), y_train)
        spam_res = clf.evaluate(np.array(X_test), y_test)

        lattice_rows.append({
            'L': l_val,
            'sub_images': l_val * l_val,
            'change_rate': round(float(np.mean(chg_list)), 4),
            'fcc2': round(float(np.mean(fcc2_list)), 6),
            'spam_pe': spam_res['p_e'],
            'embed_time_ms': round(float(np.mean(time_list)), 1),
        })

    df_lattice = pd.DataFrame(lattice_rows)
    df_lattice.to_csv(os.path.join(results_dir, "lattice_sweep.csv"), index=False)
    print("Saved lattice_sweep.csv")

    # -------------------------------------------------------------
    # Experiment 4: Comprehensive Ablation Study
    # -------------------------------------------------------------
    print("\n--- Running Experiment 4: Ablation Study ---")
    ablation_configs = [
        ("Baseline HILL", False, False, False, False),
        ("HILL-CMD (Base alpha=9)", True, False, False, False),
        ("+ Improvement A (Adaptive-alpha)", True, True, False, False),
        ("+ Improvement B (Key-Randomization)", True, False, False, True),
        ("+ Improvement C (8-Neighbor Voting)", True, False, True, False),
        ("HILL-CMD+ (All Improvements A+B+C)", True, True, True, True),
    ]

    ablation_rows = []
    for cfg_name, cmd_en, adapt_a, neigh8, key_rand in ablation_configs:
        psnr_list, ssim_list, chg_list, fcc2_list = [], [], [], []
        stegos_ab = []
        for cov in covers:
            stego, _ = simulate_embedding(
                cov,
                payload_bpp=0.4,
                scheme="HILL",
                cmd_enabled=cmd_en,
                alpha=9.0,
                adaptive_alpha=adapt_a,
                neighborhood_8=neigh8,
                key_randomized=key_rand,
            )
            m = compute_all_metrics(cov, stego)
            psnr_list.append(m['psnr'])
            ssim_list.append(m['ssim'])
            chg_list.append(m['change_rate'])
            fcc2_list.append(m['fcc2'])
            stegos_ab.append(stego)

        half = len(covers) // 2
        X_train = [extract_spam_686(img) for img in covers[:half] + stegos_ab[:half]]
        y_train = np.array([0] * half + [1] * half)
        X_test = [extract_spam_686(img) for img in covers[half:] + stegos_ab[half:]]
        y_test = np.array([0] * (len(covers) - half) + [1] * (len(stegos_ab) - half))

        clf = SteganalysisEnsemble(classifier_type="lda")
        clf.train(np.array(X_train), y_train)
        spam_res = clf.evaluate(np.array(X_test), y_test)

        test_ds = StegoDataset(covers[half:] + stegos_ab[half:], [0] * (len(covers) - half) + [1] * (len(stegos_ab) - half))
        test_loader = DataLoader(test_ds, batch_size=8, shuffle=False)
        srnet_res = evaluate_srnet(srnet_model, test_loader, device=srnet_model.layer1[0].weight.device)

        ablation_rows.append({
            'configuration': cfg_name,
            'change_rate': round(float(np.mean(chg_list)), 4),
            'fcc2': round(float(np.mean(fcc2_list)), 6),
            'psnr': round(float(np.mean(psnr_list)), 2),
            'ssim': round(float(np.mean(ssim_list)), 4),
            'spam_pe': spam_res['p_e'],
            'srnet_pe': srnet_res['p_e'],
        })

    df_ablation = pd.DataFrame(ablation_rows)
    df_ablation.to_csv(os.path.join(results_dir, "ablation_study.csv"), index=False)
    print("Saved ablation_study.csv")
    print("=== All Benchmark Experiments Completed Successfully! ===")

    return {
        'payload': df_payload,
        'alpha': df_alpha,
        'lattice': df_lattice,
        'ablation': df_ablation,
    }


if __name__ == "__main__":
    run_full_benchmark(num_images=30)
