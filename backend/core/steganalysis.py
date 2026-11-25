"""
Steganalysis Feature Extractors and Classifiers for Spatial Steganography.
Implements:
1. SPAM (Subtractive Pixel Adjacency Matrix) 686-D feature extractor - Pevny et al., 2010
2. SRM-lite residual co-occurrence feature extractor
3. Ensemble Classifiers (Random Forest and Fisher Linear Discriminant ensemble)
4. Evaluation of Detection Error: P_E = (FPR + FNR) / 2
"""

import numpy as np
from numba import njit
from sklearn.ensemble import RandomForestClassifier
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
from typing import Tuple, Dict, Any, List


@njit(fastmath=True)
def _extract_spam_2nd_order(diff_map: np.ndarray, T: int = 3) -> np.ndarray:
    """
    Computes 2nd-order Markov transition probabilities for a 2D difference map.
    Returns 343-D feature vector.
    """
    K = 2 * T + 1  # 7
    counts = np.zeros((K, K, K), dtype=np.float64)
    H, W = diff_map.shape

    # Horizontal transitions
    for r in range(H):
        for c in range(W - 2):
            u = diff_map[r, c] + T
            v = diff_map[r, c + 1] + T
            w = diff_map[r, c + 2] + T
            counts[u, v, w] += 1.0

    # Row-normalization
    features = np.zeros((K, K, K), dtype=np.float64)
    for u in range(K):
        for v in range(K):
            row_sum = 0.0
            for w in range(K):
                row_sum += counts[u, v, w]
            if row_sum > 0.0:
                for w in range(K):
                    features[u, v, w] = counts[u, v, w] / row_sum
            else:
                for w in range(K):
                    features[u, v, w] = 1.0 / K

    return features.ravel()


def extract_spam_686(image: np.ndarray, T: int = 3) -> np.ndarray:
    """
    Extracts the standard 686-dimensional SPAM feature vector from a grayscale image.
    1. Horizontal & Vertical differences -> M_HV (343 dimensions)
    2. Diagonal & Anti-Diagonal differences -> M_diag (343 dimensions)
    Total = 686 dimensions.
    """
    img = image.astype(np.int16)
    H, W = img.shape

    # Horizontal and Vertical differences clipped to [-T, T]
    D_h = np.clip(img[:, 1:] - img[:, :-1], -T, T)
    D_v = np.clip(img[1:, :] - img[:-1, :], -T, T)

    # Diagonal differences
    D_diag = np.clip(img[1:, 1:] - img[:-1, :-1], -T, T)
    D_adiag = np.clip(img[1:, :-1] - img[:-1, 1:], -T, T)

    # 2nd-order Markov features
    f_h = _extract_spam_2nd_order(D_h, T=T)
    f_v = _extract_spam_2nd_order(D_v.T, T=T)
    f_hv = (f_h + f_v) / 2.0

    f_d = _extract_spam_2nd_order(D_diag, T=T)
    f_ad = _extract_spam_2nd_order(D_adiag, T=T)
    f_diag = (f_d + f_ad) / 2.0

    spam_features = np.concatenate([f_hv, f_diag])
    return spam_features


def extract_srm_lite(image: np.ndarray) -> np.ndarray:
    """
    Extracts a lightweight Spatial Rich Model (SRM-lite) residual feature vector.
    Uses 3 residual filters (KB, Edge, Laplace) with co-occurrences and summary statistics (128-D).
    """
    import cv2
    img = image.astype(np.float64)

    filters = [
        # KB filter
        np.array([[-1, 2, -1], [2, -4, 2], [-1, 2, -1]], dtype=np.float64),
        # Horizontal edge
        np.array([[-1, 2, -1], [0, 0, 0], [1, -2, 1]], dtype=np.float64),
        # Diagonal edge
        np.array([[2, -1, 0], [-1, 0, 1], [0, 1, -2]], dtype=np.float64),
        # High-pass Laplace
        np.array([[0, 1, 0], [1, -4, 1], [0, 1, 0]], dtype=np.float64),
    ]

    features = []
    for f in filters:
        res = cv2.filter2D(img, -1, f, borderType=cv2.BORDER_REFLECT)
        # Moments & quantiles
        features.append(np.mean(np.abs(res)))
        features.append(np.std(res))
        features.append(np.percentile(res, 25))
        features.append(np.percentile(res, 75))
        features.append(np.percentile(res, 95))
        # Quantized co-occurrence histogram
        q_res = np.clip(np.round(res), -2, 2).astype(np.int32) + 2  # 0..4
        hist, _ = np.histogram(q_res[:, :-1] * 5 + q_res[:, 1:], bins=25, range=(0, 25))
        features.extend(hist / (hist.sum() + 1e-10))

    return np.array(features, dtype=np.float64)


class SteganalysisEnsemble:
    """
    Ensemble classifier for Cover vs Stego detection using SPAM or SRM-lite features.
    """
    def __init__(self, classifier_type: str = "rf"):
        self.classifier_type = classifier_type
        if classifier_type == "rf":
            self.model = RandomForestClassifier(n_estimators=100, max_depth=15, random_state=42, n_jobs=-1)
        else:
            self.model = LinearDiscriminantAnalysis()
        self.is_trained = False

    def train(self, X_train: np.ndarray, y_train: np.ndarray) -> Dict[str, float]:
        """
        Trains classifier. y: 0 for Cover, 1 for Stego.
        """
        self.model.fit(X_train, y_train)
        self.is_trained = True

        y_pred = self.model.predict(X_train)
        acc = float(np.mean(y_pred == y_train))
        return {'train_accuracy': acc}

    def evaluate(self, X_test: np.ndarray, y_test: np.ndarray) -> Dict[str, float]:
        """
        Computes detection error: P_E = (FPR + FNR) / 2
        """
        if not self.is_trained:
            raise RuntimeError("Model is not trained.")

        y_pred = self.model.predict(X_test)

        cover_mask = (y_test == 0)
        stego_mask = (y_test == 1)

        # False Positive Rate (Cover classified as Stego)
        fpr = float(np.mean(y_pred[cover_mask] == 1)) if np.any(cover_mask) else 0.0
        # False Negative Rate (Stego classified as Cover)
        fnr = float(np.mean(y_pred[stego_mask] == 0)) if np.any(stego_mask) else 0.0
        # Total detection error
        p_e = (fpr + fnr) / 2.0
        accuracy = float(np.mean(y_pred == y_test))

        return {
            'p_e': round(p_e, 4),
            'fpr': round(fpr, 4),
            'fnr': round(fnr, 4),
            'accuracy': round(accuracy, 4),
        }

    def predict_score(self, feature_vector: np.ndarray) -> float:
        """
        Returns probability score that image is Stego [0.0 = Cover, 1.0 = Stego].
        """
        if not self.is_trained:
            # Fallback heuristic if not yet fitted
            return 0.5
        probs = self.model.predict_proba(feature_vector.reshape(1, -1))
        return float(probs[0, 1])
