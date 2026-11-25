"""
Academic Plot Generation Script for CMD-Stego+.
Produces high-resolution (300 DPI) publication-quality figures mirroring the IEEE TIFS 2015 paper:
- Fig 11: FCC(2) vs Alpha (Clustering strength)
- Fig 12: Change rate vs Alpha
- Fig 13: Detection error P_E vs Alpha
- Fig 14: Detection error P_E vs Payload (HILL, S-UNIWARD, WOW, HILL-CMD, S-UNIWARD-CMD, HILL-CMD+)
- Fig 15: FCC(2) vs Payload
- Fig 16: Sub-image Partition L comparison (L=2, 4, 8)
- Fig 19: Comprehensive Ablation Study bar chart
"""

import os
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np


def set_academic_style():
    plt.rcParams.update({
        'font.size': 12,
        'axes.labelsize': 13,
        'axes.titlesize': 14,
        'xtick.labelsize': 11,
        'ytick.labelsize': 11,
        'legend.fontsize': 11,
        'figure.titlesize': 15,
        'figure.dpi': 300,
        'axes.grid': True,
        'grid.alpha': 0.35,
        'grid.linestyle': '--',
        'lines.linewidth': 2.0,
        'lines.markersize': 7,
    })


def generate_all_plots(
    csv_dir: str = "d:/Stegnography/results/csv",
    plots_dir: str = "d:/Stegnography/results/plots",
):
    os.makedirs(plots_dir, exist_ok=True)
    set_academic_style()

    df_payload = pd.read_csv(os.path.join(csv_dir, "payload_sweep.csv"))
    df_alpha = pd.read_csv(os.path.join(csv_dir, "alpha_sweep.csv"))
    df_lattice = pd.read_csv(os.path.join(csv_dir, "lattice_sweep.csv"))
    df_ablation = pd.read_csv(os.path.join(csv_dir, "ablation_study.csv"))

    # -------------------------------------------------------------
    # Fig 11: FCC(2) vs Alpha
    # -------------------------------------------------------------
    plt.figure(figsize=(7, 5))
    plt.plot(df_alpha['alpha'], df_alpha['fcc2'], marker='o', color='#1f77b4', label=r'HILL-CMD ($FCC^{(2)}$)')
    plt.title(r'Fig. 11: $FCC^{(2)}$ vs. Clustering Parameter $\alpha$ (Payload = 0.4 bpp)')
    plt.xlabel(r'Clustering Parameter $\alpha$')
    plt.ylabel(r'2nd-Order Feature Continuity $FCC^{(2)}$')
    plt.xticks(df_alpha['alpha'])
    plt.tight_layout()
    plt.savefig(os.path.join(plots_dir, "fig11_fcc2_vs_alpha.png"))
    plt.close()

    # -------------------------------------------------------------
    # Fig 12: Change Rate vs Alpha
    # -------------------------------------------------------------
    plt.figure(figsize=(7, 5))
    plt.plot(df_alpha['alpha'], df_alpha['change_rate'] * 100, marker='s', color='#ff7f0e', label='HILL-CMD')
    plt.title(r'Fig. 12: Change Rate vs. Clustering Parameter $\alpha$ (Payload = 0.4 bpp)')
    plt.xlabel(r'Clustering Parameter $\alpha$')
    plt.ylabel('Change Rate (%)')
    plt.xticks(df_alpha['alpha'])
    plt.tight_layout()
    plt.savefig(os.path.join(plots_dir, "fig12_changerate_vs_alpha.png"))
    plt.close()

    # -------------------------------------------------------------
    # Fig 13: Detection Error P_E vs Alpha
    # -------------------------------------------------------------
    plt.figure(figsize=(7, 5))
    plt.plot(df_alpha['alpha'], df_alpha['spam_pe'], marker='^', color='#2ca02c', label='SPAM 686-D')
    plt.plot(df_alpha['alpha'], df_alpha['srnet_pe'], marker='D', color='#d62728', linestyle='--', label='SRNet-lite CNN')
    plt.title(r'Fig. 13: Detection Error $P_E$ vs. $\alpha$ (Payload = 0.4 bpp)')
    plt.xlabel(r'Clustering Parameter $\alpha$')
    plt.ylabel(r'Average Detection Error $P_E$')
    plt.xticks(df_alpha['alpha'])
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(plots_dir, "fig13_pe_vs_alpha.png"))
    plt.close()

    # -------------------------------------------------------------
    # Fig 14: Detection Error P_E vs Payload
    # -------------------------------------------------------------
    plt.figure(figsize=(8, 5.5))
    scheme_styles = {
        'HILL': ('#7f7f7f', 'o', ':'),
        'S-UNIWARD': ('#8c564b', 'v', ':'),
        'WOW': ('#e377c2', '<', ':'),
        'HILL-CMD': ('#1f77b4', 's', '-'),
        'S-UNIWARD-CMD': ('#ff7f0e', '^', '-'),
        'HILL-CMD+': ('#2ca02c', '*', '-'),
    }

    for name, group in df_payload.groupby('scheme'):
        color, marker, lstyle = scheme_styles.get(name, ('black', 'o', '-'))
        lw = 2.8 if name == 'HILL-CMD+' else 1.8
        plt.plot(group['payload_bpp'], group['spam_pe'], label=name, color=color, marker=marker, linestyle=lstyle, linewidth=lw)

    plt.title(r'Fig. 14: Detection Error $P_E$ vs. Relative Payload (SPAM 686-D)')
    plt.xlabel('Relative Payload (bpp)')
    plt.ylabel(r'Detection Error $P_E = (FPR + FNR)/2$')
    plt.legend(loc='lower left')
    plt.tight_layout()
    plt.savefig(os.path.join(plots_dir, "fig14_pe_vs_payload.png"))
    plt.close()

    # -------------------------------------------------------------
    # Fig 15: FCC(2) vs Payload
    # -------------------------------------------------------------
    plt.figure(figsize=(7.5, 5))
    for name in ['HILL', 'HILL-CMD', 'HILL-CMD+']:
        sub = df_payload[df_payload['scheme'] == name]
        color, marker, lstyle = scheme_styles[name]
        plt.plot(sub['payload_bpp'], sub['fcc2'], label=name, color=color, marker=marker, linestyle=lstyle)

    plt.title(r'Fig. 15: Modification Direction Correlation $FCC^{(2)}$ vs. Payload')
    plt.xlabel('Relative Payload (bpp)')
    plt.ylabel(r'2nd-Order Feature Continuity $FCC^{(2)}$')
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(plots_dir, "fig15_fcc2_vs_payload.png"))
    plt.close()

    # -------------------------------------------------------------
    # Fig 16: Lattice Decomposition L Comparison
    # -------------------------------------------------------------
    fig, ax1 = plt.subplots(figsize=(7, 5))
    color = '#1f77b4'
    ax1.set_xlabel(r'Lattice Parameter $L$ ($L \times L$ Sub-images)')
    ax1.set_ylabel('Change Rate (%)', color=color)
    ax1.bar(df_lattice['L'] - 0.2, df_lattice['change_rate'] * 100, width=0.4, color=color, alpha=0.8, label='Change Rate (%)')
    ax1.tick_params(axis='y', labelcolor=color)
    ax1.set_xticks(df_lattice['L'])

    ax2 = ax1.twinx()
    color2 = '#2ca02c'
    ax2.set_ylabel(r'Detection Error $P_E$', color=color2)
    ax2.plot(df_lattice['L'], df_lattice['spam_pe'], color=color2, marker='o', linewidth=2.5, label=r'SPAM $P_E$')
    ax2.tick_params(axis='y', labelcolor=color2)

    plt.title(r'Fig. 16: Impact of Sub-image Lattice Decomposition $L \in \{2, 4, 8\}$')
    fig.tight_layout()
    plt.savefig(os.path.join(plots_dir, "fig16_lattice_L_comparison.png"))
    plt.close()

    # -------------------------------------------------------------
    # Fig 19: Comprehensive Ablation Study
    # -------------------------------------------------------------
    plt.figure(figsize=(9, 5.5))
    y_pos = np.arange(len(df_ablation))
    bars = plt.barh(y_pos, df_ablation['spam_pe'], color='#3b82f6', alpha=0.85, edgecolor='#1d4ed8')
    plt.yticks(y_pos, df_ablation['configuration'])
    plt.xlabel(r'Steganalysis Detection Error $P_E$ (Higher is More Secure)')
    plt.title(r'Fig. 19: Ablation Analysis of Proposed Novel Enhancements (Payload 0.4 bpp)')
    plt.xlim(0.0, 0.52)
    plt.axvline(0.5, color='gray', linestyle='--', alpha=0.7, label='Ideal Unbounded Security (0.50)')

    for bar in bars:
        width = bar.get_width()
        plt.text(width + 0.008, bar.get_y() + bar.get_height() / 2, f"{width:.4f}", va='center', fontsize=10)

    plt.legend(loc='lower right')
    plt.tight_layout()
    plt.savefig(os.path.join(plots_dir, "fig19_ablation_comparison.png"))
    plt.close()

    print(f"All 7 academic plots generated in {plots_dir}!")


if __name__ == "__main__":
    generate_all_plots()
