#!/usr/bin/env python3
"""
visual_metrics.py — verify-output.sh'in görsel metrik yardımcısı.

Verilen kare görsellerinden (PNG/JPG dosya yolları, argv) üç metrik
hesaplar ve "anahtar=değer" satırları basar (bash'te kolay parse edilir):
  edge_density_avg   — kare başına ortalama kenar (gradyan) yoğunluğu
  content_pixel_pct  — baskın (arka plan) renkten belirgin sapan piksel yüzdesi
  frame_diff_avg     — ardışık kareler arası ortalama piksel farkı

Tahmin değil ölçüm: gerçek render edilmiş karelerden hesaplanır.
Kullanım: python visual_metrics.py frame1.png frame2.png ...
"""
import sys

import numpy as np
from PIL import Image


def _load_gray(path: str) -> np.ndarray:
    img = Image.open(path).convert("L")
    return np.asarray(img, dtype=np.float64)


def _load_rgb(path: str) -> np.ndarray:
    img = Image.open(path).convert("RGB")
    return np.asarray(img, dtype=np.float64)


def edge_density(gray: np.ndarray) -> float:
    """Basit Sobel-benzeri gradyan büyüklüğü — kenar yoğunluğu için ölçüm."""
    gx = np.diff(gray, axis=1)
    gy = np.diff(gray, axis=0)
    # Boyutları eşitle (diff bir eksende 1 küçültür)
    gx = gx[:-1, :]
    gy = gy[:, :-1]
    magnitude = np.sqrt(gx**2 + gy**2)
    return float(magnitude.mean())


def content_pixel_pct(rgb: np.ndarray, threshold: float = 20.0) -> float:
    """
    Baskın (en sık) renkten Öklid mesafesi > threshold olan piksellerin yüzdesi.
    Düz tek renk arka plan (örn. navy) baskındır; içerik ondan sapan piksellerdir.
    """
    h, w, _ = rgb.shape
    flat = rgb.reshape(-1, 3)
    # Baskın rengi örnekleme ile bul (performans için — tüm piksel sayımı pahalı)
    sample = flat[:: max(1, len(flat) // 5000)]
    colors, counts = np.unique(sample.astype(np.int32), axis=0, return_counts=True)
    dominant = colors[np.argmax(counts)].astype(np.float64)
    dist = np.sqrt(((flat - dominant) ** 2).sum(axis=1))
    return float((dist > threshold).sum() / len(flat) * 100)


def frame_diff(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.abs(a - b).mean())


def main() -> None:
    paths = sys.argv[1:]
    if len(paths) < 2:
        print("HATA: en az 2 kare gerekli", file=sys.stderr)
        sys.exit(1)

    grays = [_load_gray(p) for p in paths]
    rgbs = [_load_rgb(p) for p in paths]

    edge_avg = float(np.mean([edge_density(g) for g in grays]))
    content_avg = float(np.mean([content_pixel_pct(r) for r in rgbs]))
    diffs = [frame_diff(grays[i], grays[i + 1]) for i in range(len(grays) - 1)]
    diff_avg = float(np.mean(diffs)) if diffs else 0.0

    print(f"edge_density_avg={edge_avg:.3f}")
    print(f"content_pixel_pct={content_avg:.3f}")
    print(f"frame_diff_avg={diff_avg:.3f}")


if __name__ == "__main__":
    main()
