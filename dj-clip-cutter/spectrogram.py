"""Spectrogram renderer for the editor's audio track.

SESSIE 19 — Phase 10. Renders a colour-mapped log-magnitude spectrogram
PNG for a given clip. The file is cached on disk so repeat opens are fast,
and the audio source is the same per-job WAV the waveform endpoint already
uses (no re-decoding the source video for each request).

Why a hand-rolled PNG encoder?
The dj-clip-cutter venv ships librosa + numpy but no Pillow / matplotlib
/ imageio. Adding a heavy plotting dep just for one PNG felt wrong, so
this file uses only stdlib `struct` + `zlib` to write the PNG. The output
is a 24-bit RGB image — no alpha, no metadata.
"""

from __future__ import annotations

import os
import struct
import zlib
import logging

import numpy as np

log = logging.getLogger(__name__)

# Spectrogram tuning. Hop_length 512 at 22.05 kHz gives ~23 ms time
# resolution which is plenty for visual inspection of drops / breakdowns.
DEFAULT_SR        = 22050
DEFAULT_N_FFT     = 2048
DEFAULT_HOP       = 512
DEFAULT_FMIN_HZ   = 30
DEFAULT_FMAX_HZ   = 11025  # nyquist for 22.05k SR
DEFAULT_DB_FLOOR  = -70.0  # values below this clip to 0


def _write_png_rgb(out_path: str, rgb: np.ndarray) -> None:
    """Encode an HxWx3 uint8 array as a 24-bit RGB PNG using only stdlib.

    rgb must be C-contiguous; we add the per-row filter byte (type 0 =
    None) before zlib-deflating the IDAT payload.
    """
    if rgb.dtype != np.uint8:
        rgb = rgb.astype(np.uint8, copy=False)
    if rgb.ndim != 3 or rgb.shape[2] != 3:
        raise ValueError(f"_write_png_rgb expects HxWx3, got {rgb.shape}")
    h, w, _ = rgb.shape

    # Each scanline = 1 filter-type byte + 3*w pixel bytes.
    rgb = np.ascontiguousarray(rgb)
    row_filter = np.zeros((h, 1), dtype=np.uint8)
    raw_rows = np.concatenate([row_filter, rgb.reshape(h, w * 3)], axis=1)
    raw_bytes = raw_rows.tobytes()

    def _chunk(tag: bytes, data: bytes) -> bytes:
        clen = struct.pack('>I', len(data))
        crc  = zlib.crc32(tag + data) & 0xffffffff
        return clen + tag + data + struct.pack('>I', crc)

    sig  = b'\x89PNG\r\n\x1a\n'
    # IHDR: width, height, bit_depth=8, colour_type=2 (RGB), compression=0,
    # filter=0, interlace=0
    ihdr = struct.pack('>IIBBBBB', w, h, 8, 2, 0, 0, 0)
    idat = zlib.compress(raw_bytes, 9)

    tmp_path = out_path + '.tmp'
    with open(tmp_path, 'wb') as f:
        f.write(sig)
        f.write(_chunk(b'IHDR', ihdr))
        f.write(_chunk(b'IDAT', idat))
        f.write(_chunk(b'IEND', b''))
    os.replace(tmp_path, out_path)


def _viridis_lut() -> np.ndarray:
    """Approximation of matplotlib's viridis colormap as a 256x3 LUT.

    Hand-tuned anchor stops + linear interpolation. Avoids depending on
    matplotlib for one tiny lookup table. Visually indistinguishable from
    real viridis at the resolutions we render at (~600x96 px).
    """
    # (position, R, G, B) — positions in 0..1, RGB in 0..255
    stops = [
        (0.0,   68,   1,  84),
        (0.13,  72,  35, 116),
        (0.25,  64,  67, 135),
        (0.38,  52,  94, 141),
        (0.50,  41, 121, 142),
        (0.63,  32, 144, 140),
        (0.75,  34, 167, 132),
        (0.88,  68, 190, 112),
        (0.94, 121, 209,  81),
        (1.00, 253, 231,  37),
    ]
    lut = np.zeros((256, 3), dtype=np.uint8)
    pos = np.array([s[0] for s in stops])
    rgb = np.array([s[1:] for s in stops], dtype=np.float32)
    xs  = np.linspace(0, 1, 256)
    for c in range(3):
        lut[:, c] = np.clip(np.interp(xs, pos, rgb[:, c]), 0, 255).astype(np.uint8)
    return lut


# Module-level singleton — built once.
_VIRIDIS = _viridis_lut()


def render_spectrogram_png(audio_path: str,
                           start: float,
                           duration: float,
                           out_path: str,
                           width: int = 800,
                           height: int = 96,
                           sr: int = DEFAULT_SR,
                           n_fft: int = DEFAULT_N_FFT,
                           hop: int = DEFAULT_HOP,
                           fmin: float = DEFAULT_FMIN_HZ,
                           fmax: float = DEFAULT_FMAX_HZ,
                           db_floor: float = DEFAULT_DB_FLOOR) -> str:
    """Render a colour-mapped log-magnitude spectrogram for one clip.

    Loads only the requested time slice via librosa.load(offset=, duration=)
    so this is fast even on hour-long sets. Returns the output path on
    success; raises on failure (caller should turn that into a 500).
    """
    if duration <= 0.05:
        raise ValueError("duration must be > 0.05 s")
    width  = max(80, min(2000, int(width)))
    height = max(40, min(400,  int(height)))

    import librosa  # lazy — avoids cold-start cost on app boot

    y, sr_used = librosa.load(audio_path, sr=sr, mono=True,
                              offset=max(0.0, float(start)),
                              duration=float(duration))
    if y is None or len(y) < 16:
        raise ValueError("audio slice too short to STFT")

    # Magnitude STFT, log-scaled to dB.
    stft = librosa.stft(y, n_fft=n_fft, hop_length=hop, window='hann')
    mag  = np.abs(stft)
    db   = librosa.amplitude_to_db(mag, ref=np.max)
    # Clip to [db_floor, 0] and normalise to 0..1.
    db = np.clip(db, db_floor, 0.0)
    norm = (db - db_floor) / (-db_floor)  # 0..1, 1 = loudest

    # STFT row 0 = DC, last row = nyquist. Pick the rows inside [fmin..fmax].
    n_freq_bins = norm.shape[0]
    freqs = np.linspace(0, sr_used / 2, n_freq_bins)
    fmask = (freqs >= fmin) & (freqs <= fmax)
    if not fmask.any():
        raise ValueError(f"no frequency bins in [{fmin}, {fmax}]")
    band = norm[fmask]

    # Resample to (height x width) by nearest-pixel binning. Time axis
    # (cols) is downsampled with max-pooling so transient kicks remain
    # visible even at narrow widths.
    n_t = band.shape[1]
    if n_t == 0:
        raise ValueError("STFT produced 0 frames")
    if n_t >= width:
        col_edges = np.linspace(0, n_t, width + 1).astype(int)
        cols_out  = np.zeros((band.shape[0], width), dtype=np.float32)
        for i in range(width):
            a, b = col_edges[i], max(col_edges[i] + 1, col_edges[i + 1])
            cols_out[:, i] = band[:, a:b].max(axis=1)
    else:
        # Stretch shorter clips to the requested width with linear interp.
        xp = np.linspace(0, 1, n_t)
        xq = np.linspace(0, 1, width)
        cols_out = np.zeros((band.shape[0], width), dtype=np.float32)
        for r in range(band.shape[0]):
            cols_out[r] = np.interp(xq, xp, band[r])

    # Frequency axis (rows): logarithmic spacing so the bass band gets
    # more pixels — visually matches what a DJ would expect.
    n_f = cols_out.shape[0]
    log_idx = np.geomspace(1, max(2, n_f), height) - 1
    log_idx = np.clip(log_idx.astype(int), 0, n_f - 1)
    rows_out = cols_out[log_idx, :]

    # Flip vertically so high freqs render at the top (DAW convention).
    rows_out = rows_out[::-1, :]

    # Map 0..1 → viridis LUT → uint8 RGB.
    idx = np.clip((rows_out * 255.0).astype(np.int32), 0, 255)
    rgb = _VIRIDIS[idx]  # shape (height, width, 3), uint8

    _write_png_rgb(out_path, rgb)
    return out_path
