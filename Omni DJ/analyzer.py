"""
Audio analysis engine for DJ set drop/buildup detection.
Bar-aware: works in musical bars (4 beats), outputs in seconds.
Uses HPSS (harmonic/percussive separation) for better accuracy.
Optionally uses Demucs for AI source separation.
"""

import librosa
import numpy as np
from scipy.signal import find_peaks
from scipy.ndimage import uniform_filter1d


# ---------------------------------------------------------------------------
# BPM & beat grid
# ---------------------------------------------------------------------------

# SESSIE 22 — Krumhansl-Schmuckler key profiles for major and minor keys.
# Standard published profiles (Krumhansl & Kessler 1982 / Temperley revision).
# Index 0 = C, 1 = C#/Db, ..., 11 = B. Higher value = higher tonal weight.
_KEY_PROFILE_MAJOR = np.array([
    6.35, 2.23, 3.48, 2.33, 4.38, 4.09,
    2.52, 5.19, 2.39, 3.66, 2.29, 2.88,
])
_KEY_PROFILE_MINOR = np.array([
    6.33, 2.68, 3.52, 5.38, 2.60, 3.53,
    2.54, 4.75, 3.98, 2.69, 3.34, 3.17,
])
_PITCH_NAMES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
# Camelot Wheel — DJ-friendly key notation. Major = 'B', minor = 'A'.
# Mapping is the standard arrangement used by Mixed In Key, Rekordbox etc.
_CAMELOT_MAJOR = {
    'C':  '8B', 'C#': '3B', 'D':  '10B', 'D#': '5B', 'E':  '12B', 'F':  '7B',
    'F#': '2B', 'G':  '9B', 'G#': '4B',  'A':  '11B', 'A#': '6B',  'B':  '1B',
}
_CAMELOT_MINOR = {
    'C':  '5A', 'C#': '12A', 'D':  '7A', 'D#': '2A', 'E':  '9A', 'F':  '4A',
    'F#': '11A', 'G':  '6A', 'G#': '1A', 'A':  '8A', 'A#': '3A', 'B':  '10A',
}


def detect_musical_key(audio_path=None, sr=22050, y_audio=None):
    """SESSIE 22 — Detect the musical key of an audio file via chroma +
    Krumhansl-Schmuckler template-matching.

    Args:
        audio_path: path to load (when y_audio not supplied)
        sr: sample rate. 22050 is enough for chroma. Lower = faster.
        y_audio: pre-loaded mono numpy array (avoids redundant file IO when
                 called right after detect_bpm)

    Returns dict:
        {
          tonic: 'F#' etc (str | None on failure),
          mode:  'major' | 'minor' | None,
          camelot: '7A' / '3B' etc (str | None),
          confidence: 0..1 (correlation score, useful for low-confidence flagging),
        }

    Notes on robustness — DJ-content specific:
    - We average the chromagram across the whole loaded window. For house/techno
      sets the modal key is usually stable, so this beats per-frame voting.
    - Loads up to 180s like detect_bpm; that's plenty for key inference.
    - HPSS-harmonic-only would improve accuracy but doubles loading time. We
      use the raw audio — empirically within ±1 semitone of HPSS on test sets.
    """
    if y_audio is None:
        if audio_path is None:
            return {'tonic': None, 'mode': None, 'camelot': None, 'confidence': 0.0}
        try:
            y_audio, sr = librosa.load(audio_path, sr=sr, mono=True, duration=180)
        except Exception as e:
            print(f"  Key detection load failed: {e}")
            return {'tonic': None, 'mode': None, 'camelot': None, 'confidence': 0.0}
    try:
        # chroma_cqt is robust to percussive content (vs chroma_stft). DJ
        # sets have heavy bass + drums, so this matters.
        chroma = librosa.feature.chroma_cqt(y=y_audio, sr=sr, hop_length=2048)
        if chroma is None or chroma.size == 0:
            return {'tonic': None, 'mode': None, 'camelot': None, 'confidence': 0.0}
        # Mean across time → 12-bin pitch-class profile for the whole window.
        pcp = chroma.mean(axis=1)
        # Normalise so correlation isn't dominated by overall energy.
        norm = pcp / (np.linalg.norm(pcp) + 1e-9)

        # Score against all 24 rotations (12 major + 12 minor). Pearson
        # correlation between observed PCP and the rotated template is the
        # standard scoring function for Krumhansl-Schmuckler.
        best_score = -1e9
        best_tonic = None
        best_mode  = None
        def corr(a, b):
            a = a - a.mean()
            b = b - b.mean()
            denom = (np.linalg.norm(a) * np.linalg.norm(b)) + 1e-12
            return float(np.dot(a, b) / denom)
        for i in range(12):
            major_template = np.roll(_KEY_PROFILE_MAJOR, i)
            minor_template = np.roll(_KEY_PROFILE_MINOR, i)
            major_score = corr(norm, major_template)
            minor_score = corr(norm, minor_template)
            if major_score > best_score:
                best_score = major_score
                best_tonic = _PITCH_NAMES[i]
                best_mode  = 'major'
            if minor_score > best_score:
                best_score = minor_score
                best_tonic = _PITCH_NAMES[i]
                best_mode  = 'minor'
        camelot_map = _CAMELOT_MAJOR if best_mode == 'major' else _CAMELOT_MINOR
        return {
            'tonic':      best_tonic,
            'mode':       best_mode,
            'camelot':    camelot_map.get(best_tonic),
            # Map correlation to a 0..1-ish confidence band. Empirical
            # ceiling around 0.7 for clean tonal material.
            'confidence': max(0.0, min(1.0, (best_score + 0.3) / 0.9)),
        }
    except Exception as e:
        print(f"  Key detection failed: {e}")
        return {'tonic': None, 'mode': None, 'camelot': None, 'confidence': 0.0}


# SESSIE 24 — librosa.beat.beat_track sometimes locks onto the half-tempo of
# melodic / less-hard-kicked dance music. For example, a 124 BPM melodic-house
# set can come back as ~72 BPM because the onset detector picks up only the
# down-beat kick and treats every other kick as a syncopation. Tools like
# Mixed In Key / Rekordbox don't have this problem because they're trained
# specifically on dance music; librosa is general-purpose.
#
# Heuristic: if the detected tempo lands in [60, 90) AND doubling lands in
# the dance-music range [120, 180], assume half-tempo bias and double both
# the reported tempo AND densify the beat grid (insert midpoints) so that
# bar_duration / bar_times / downstream bar-snapping remain INTERNALLY
# CONSISTENT. Otherwise the BPM stamp would say "144" but the bar-aligned
# clip cutter would still operate on the 72 BPM grid — confusing for users
# and a latent footgun for any future feature that reads `bpm`.
#
# Conservative range chosen so we never up-tempo legit downtempo / hip-hop
# / dub sets (those sit in 60-100 BPM and stay there). Sjuul's product is
# squarely dance music; if a user uploads a 75 BPM lofi-set we'd rather be
# wrong cosmetically once than break a real 150 BPM trance set.
def _maybe_double_tempo(tempo, beat_times):
    """Return (tempo, beat_times, was_doubled). See SESSIE 24 comment above."""
    if not (60.0 <= tempo < 90.0):
        return tempo, beat_times, False
    doubled = tempo * 2
    if not (120.0 <= doubled <= 180.0):
        return tempo, beat_times, False
    if len(beat_times) < 2:
        return doubled, beat_times, True
    densified = []
    for i in range(len(beat_times) - 1):
        densified.append(beat_times[i])
        densified.append((beat_times[i] + beat_times[i + 1]) / 2.0)
    densified.append(beat_times[-1])
    return doubled, densified, True


def detect_bpm(audio_path, sr=22050, y_audio=None):
    """
    Detect global BPM and beat/bar positions.

    Returns dict with:
        bpm (float), beat_times (list[float]), bar_times (list[float]),
        bar_duration (float — seconds per bar),
        bpm_raw (float|None — original librosa value when half-tempo
                 doubling was applied; None when no doubling happened),
        bpm_doubled (bool — was the half-tempo heuristic triggered?),
        key (str|None — Camelot notation like '7A'),
        key_tonic (str|None — e.g. 'F#'),
        key_mode  (str|None — 'major'/'minor'),
        key_confidence (float 0..1)
    """
    if y_audio is None:
        if audio_path is None:
            raise ValueError("Either audio_path or y_audio must be provided")
        print("  Loading audio for BPM detection...")
        # Only load first 3 min for speed
        y_audio, sr = librosa.load(audio_path, sr=sr, mono=True, duration=180)

    try:
        tempo, beats = librosa.beat.beat_track(y=y_audio, sr=sr)

        # librosa >= 0.10 may return tempo as a numpy array
        if hasattr(tempo, '__len__'):
            tempo = tempo[0] if len(tempo) > 0 else 120.0
        tempo = float(tempo)

        beat_times = librosa.frames_to_time(beats, sr=sr).tolist()

        # SESSIE 24 — half-tempo correction. See _maybe_double_tempo() above.
        tempo_raw = tempo
        tempo, beat_times, was_doubled = _maybe_double_tempo(tempo, beat_times)
        if was_doubled:
            print(f"  ⚠ librosa returned {tempo_raw:.1f} BPM — likely half-tempo. "
                  f"Doubling to {tempo:.1f} BPM (dance-music heuristic).")

        # Build bar grid (4 beats per bar)
        bar_times = [beat_times[i] for i in range(0, len(beat_times), 4)]
        bar_duration = (60.0 / tempo) * 4  # seconds per bar

        # SESSIE 22 — also detect musical key on the same loaded audio
        # window so we don't pay double the IO cost.
        key_info = detect_musical_key(audio_path=None, sr=sr, y_audio=y_audio)

        return {
            'bpm': round(tempo, 1),
            'bpm_raw': round(tempo_raw, 1) if was_doubled else None,
            'bpm_doubled': was_doubled,
            'beat_times': [round(t, 3) for t in beat_times],
            'bar_times': [round(t, 3) for t in bar_times],
            'bar_duration': round(bar_duration, 4),
            'key':            key_info.get('camelot'),
            'key_tonic':      key_info.get('tonic'),
            'key_mode':       key_info.get('mode'),
            'key_confidence': key_info.get('confidence', 0.0),
        }
    except Exception as e:
        print(f"  BPM detection failed: {e}, using 128 BPM default")
        bar_dur = (60.0 / 128) * 4
        return {
            'bpm': 128.0,
            'bpm_raw': None,
            'bpm_doubled': False,
            'beat_times': [],
            'bar_times': [],
            'bar_duration': round(bar_dur, 4),
            'key': None, 'key_tonic': None, 'key_mode': None, 'key_confidence': 0.0,
        }


def _snap_to_bar(time_sec, bar_times, bar_duration, mode='nearest'):
    """Snap a timestamp to the nearest bar boundary.

    When `time_sec` falls outside the anchored `bar_times` range we extrapolate
    using `bar_duration` rather than clamping to the nearest anchor — clamping
    is what produced the "many of the same videos" bug, because every peak past
    the last anchor collapsed to the same value and made distinct clips share
    one (start, end) window.
    """
    if bar_duration <= 0:
        # Defensive: nothing to snap to.
        return max(0.0, time_sec)

    if not bar_times:
        # No anchors — quantise to a bar_duration grid starting at 0.
        bar_idx = round(time_sec / bar_duration)
        return max(0.0, bar_idx * bar_duration)

    first, last = bar_times[0], bar_times[-1]

    # --- Out of range: extrapolate from the nearest endpoint anchor ----------
    if time_sec > last + bar_duration / 2:
        delta = time_sec - last
        if mode == 'before':
            n = int(delta // bar_duration)             # floor
        elif mode == 'after':
            n = int(-(-delta // bar_duration))         # ceil
        else:
            n = int(round(delta / bar_duration))
        return round(last + n * bar_duration, 3)

    if time_sec < first - bar_duration / 2:
        delta = first - time_sec
        if mode == 'before':
            n = int(-(-delta // bar_duration))         # ceil → moves earlier
        elif mode == 'after':
            n = int(delta // bar_duration)             # floor → stays nearer first
        else:
            n = int(round(delta / bar_duration))
        return round(first - n * bar_duration, 3)

    # --- In range: original argmin + directional walk -----------------------
    diffs = np.abs(np.array(bar_times) - time_sec)
    idx = int(np.argmin(diffs))

    if mode == 'before':
        while idx > 0 and bar_times[idx] > time_sec:
            idx -= 1
    elif mode == 'after':
        while idx < len(bar_times) - 1 and bar_times[idx] < time_sec:
            idx += 1

    return bar_times[idx]


# ---------------------------------------------------------------------------
# Energy feature extraction
# ---------------------------------------------------------------------------

def _compute_features(y, sr, hop_length=512):
    """
    Compute all energy features from a mono audio signal.
    Uses HPSS for cleaner percussive/harmonic separation (no Demucs needed).

    Returns dict of aligned numpy arrays + frame_duration.
    """
    frame_duration = hop_length / sr

    # HPSS: split into harmonic (tonal) and percussive (transient) components
    print("  Running harmonic/percussive separation (HPSS)...")
    y_harm, y_perc = librosa.effects.hpss(y)

    # Percussive RMS — tracks kick drums and snare hits
    rms_perc = librosa.feature.rms(y=y_perc, hop_length=hop_length)[0]

    # Full RMS — overall energy
    rms_full = librosa.feature.rms(y=y, hop_length=hop_length)[0]

    # Onset strength from percussive — much cleaner than from full mix
    onset_env = librosa.onset.onset_strength(y=y_perc, sr=sr, hop_length=hop_length)

    # Sub-bass energy (20-80 Hz) — the kick/bass that defines a drop
    S = np.abs(librosa.stft(y, hop_length=hop_length))
    freqs = librosa.fft_frequencies(sr=sr)
    sub_bass_mask = (freqs >= 20) & (freqs <= 80)
    sub_bass = np.mean(S[sub_bass_mask, :], axis=0) if sub_bass_mask.any() else np.zeros(S.shape[1])

    # Bass energy (80-250 Hz)
    bass_mask = (freqs >= 80) & (freqs <= 250)
    bass = np.mean(S[bass_mask, :], axis=0) if bass_mask.any() else np.zeros(S.shape[1])

    # Mid energy (300-4000 Hz) — vocals, synths
    mid_mask = (freqs >= 300) & (freqs <= 4000)
    mid = np.mean(S[mid_mask, :], axis=0) if mid_mask.any() else np.zeros(S.shape[1])

    # Harmonic energy — tracks tonal buildup elements
    rms_harm = librosa.feature.rms(y=y_harm, hop_length=hop_length)[0]

    # Align all arrays
    min_len = min(len(rms_perc), len(rms_full), len(onset_env),
                  len(sub_bass), len(bass), len(mid), len(rms_harm))
    return {
        'rms_perc': rms_perc[:min_len],
        'rms_full': rms_full[:min_len],
        'onset': onset_env[:min_len],
        'sub_bass': sub_bass[:min_len],
        'bass': bass[:min_len],
        'mid': mid[:min_len],
        'rms_harm': rms_harm[:min_len],
        'frame_duration': frame_duration,
        'n_frames': min_len,
    }


def _compute_features_demucs(drums, bass, other, sr, hop_length=512):
    """
    Compute features from Demucs-separated stems (better quality than HPSS).
    """
    frame_duration = hop_length / sr

    rms_perc = librosa.feature.rms(y=drums, hop_length=hop_length)[0]
    rms_full = librosa.feature.rms(y=drums + bass + other, hop_length=hop_length)[0]
    onset_env = librosa.onset.onset_strength(y=drums, sr=sr, hop_length=hop_length)

    S_bass = np.abs(librosa.stft(bass, hop_length=hop_length))
    freqs = librosa.fft_frequencies(sr=sr)
    sub_bass_mask = (freqs >= 20) & (freqs <= 80)
    sub_bass = np.mean(S_bass[sub_bass_mask, :], axis=0) if sub_bass_mask.any() else np.zeros(S_bass.shape[1])
    bass_energy = np.mean(S_bass, axis=0)

    S_other = np.abs(librosa.stft(other, hop_length=hop_length))
    mid_mask = (freqs >= 300) & (freqs <= 4000)
    mid = np.mean(S_other[mid_mask, :], axis=0) if mid_mask.any() else np.zeros(S_other.shape[1])

    rms_harm = librosa.feature.rms(y=other, hop_length=hop_length)[0]

    min_len = min(len(rms_perc), len(rms_full), len(onset_env),
                  len(sub_bass), len(bass_energy), len(mid), len(rms_harm))
    return {
        'rms_perc': rms_perc[:min_len],
        'rms_full': rms_full[:min_len],
        'onset': onset_env[:min_len],
        'sub_bass': sub_bass[:min_len],
        'bass': bass_energy[:min_len],
        'mid': mid[:min_len],
        'rms_harm': rms_harm[:min_len],
        'frame_duration': frame_duration,
        'n_frames': min_len,
    }


# ---------------------------------------------------------------------------
# Drop detection — bar-aware
# ---------------------------------------------------------------------------

def _normalize(x):
    mn, mx = x.min(), x.max()
    if mx - mn < 1e-10:
        return np.zeros_like(x)
    return (x - mn) / (mx - mn)


def _detect_drops(features, bpm_info, sensitivity=0.5, bars_before=4, bars_after=4,
                  min_gap_bars=8, duration=0):
    """
    Bar-aware drop detection.

    A drop is defined as a sudden energy increase, especially in sub-bass
    and percussive energy, preceded by a lower-energy section (breakdown/buildup).

    Args:
        features: dict from _compute_features
        bpm_info: dict from detect_bpm
        sensitivity: 0.0 (conservative) to 1.0 (aggressive)
        bars_before: how many bars to include before the drop point
        bars_after: how many bars to include after the drop point
        min_gap_bars: minimum bars between detected drops
        duration: total audio duration in seconds

    Returns:
        List of clip dicts
    """
    fd = features['frame_duration']
    bar_duration = bpm_info['bar_duration']
    bpm = bpm_info['bpm']
    bar_times = bpm_info.get('bar_times', [])

    # Smoothing window = 1 bar (in frames)
    bar_frames = max(1, int(bar_duration / fd))
    smooth_window = bar_frames

    # Smooth all features at bar-level resolution
    rms_perc = uniform_filter1d(features['rms_perc'], smooth_window)
    rms_full = uniform_filter1d(features['rms_full'], smooth_window)
    onset = uniform_filter1d(features['onset'], smooth_window)
    sub_bass = uniform_filter1d(features['sub_bass'], smooth_window)
    bass = uniform_filter1d(features['bass'], smooth_window)
    rms_harm = uniform_filter1d(features['rms_harm'], smooth_window)

    # Normalize
    rms_perc_n = _normalize(rms_perc)
    rms_full_n = _normalize(rms_full)
    onset_n = _normalize(onset)
    sub_bass_n = _normalize(sub_bass)
    bass_n = _normalize(bass)
    rms_harm_n = _normalize(rms_harm)

    # Compute derivatives over a 2-bar window — detects rapid energy changes
    deriv_window = max(1, bar_frames * 2)
    perc_deriv = np.clip(np.gradient(rms_perc_n, deriv_window), 0, None)
    bass_deriv = np.clip(np.gradient(sub_bass_n, deriv_window), 0, None)
    onset_deriv = np.clip(np.gradient(onset_n, deriv_window), 0, None)

    # Energy contrast: compare current frame to the average of the previous 4 bars
    contrast_window = max(1, bar_frames * 4)
    lookback_avg = uniform_filter1d(rms_full_n, contrast_window)
    # Shift lookback to be centered 2 bars before current position
    shift = max(1, bar_frames * 2)
    lookback_shifted = np.zeros_like(lookback_avg)
    lookback_shifted[shift:] = lookback_avg[:-shift]
    energy_contrast = np.clip(rms_full_n - lookback_shifted, 0, None)

    # Drop score — emphasizes the "silence → wall of sound" transition
    drop_score = (
        0.25 * _normalize(perc_deriv) +      # Kick drums suddenly appearing
        0.25 * _normalize(bass_deriv) +       # Sub-bass suddenly appearing
        0.15 * _normalize(onset_deriv) +      # Onset intensity jump
        0.15 * _normalize(energy_contrast) +  # Energy contrast vs previous bars
        0.10 * sub_bass_n +                    # Absolute sub-bass level
        0.10 * rms_perc_n                      # Absolute percussive level
    )

    # Smooth at bar level
    drop_score = uniform_filter1d(drop_score, smooth_window)

    # Find peaks with bar-aware spacing
    min_gap_frames = max(1, int(min_gap_bars * bar_duration / fd))

    # Sensitivity scaling
    std_mult = 2.0 - (sensitivity * 1.8)
    threshold = np.mean(drop_score) + std_mult * np.std(drop_score)

    peaks, properties = find_peaks(
        drop_score,
        height=threshold,
        distance=min_gap_frames,
        prominence=0.03
    )

    # Fallback if nothing found
    if len(peaks) == 0:
        threshold = np.mean(drop_score) + 0.2 * np.std(drop_score)
        peaks, properties = find_peaks(
            drop_score,
            height=threshold,
            distance=min_gap_frames,
            prominence=0.01
        )

    # Classify each peak — DROPS ONLY in this pass.
    # Buildups are detected separately in _detect_buildups_from_drops().
    print(f"  Building drop clips from {len(peaks)} detected moments (bar-aligned)...")
    clips = []
    drop_thresholds = {
        'perc_mean': float(np.mean(perc_deriv)),
        'perc_std':  float(np.std(perc_deriv)),
    }

    for i, peak_frame in enumerate(peaks):
        peak_time = peak_frame * fd
        score = float(drop_score[peak_frame])

        has_sub_bass   = sub_bass_n[peak_frame] > 0.4
        has_percussion = rms_perc_n[peak_frame] > 0.35
        is_rising      = perc_deriv[peak_frame] > (drop_thresholds['perc_mean'] +
                                                    drop_thresholds['perc_std'])
        contrast_val   = float(energy_contrast[peak_frame]) if peak_frame < len(energy_contrast) else 0

        # Only produce a drop clip when there is clear sub-bass + percussion energy.
        # Weak / harmonic-only peaks are ignored here; the buildup pass picks them up.
        is_drop = (has_sub_bass and has_percussion) or \
                  (is_rising and has_sub_bass and contrast_val > 0.08)
        if not is_drop:
            continue

        # Start N bars before the drop, end M bars after.
        # SPEC (2026-04-26): clips are NOT padded to a fixed seconds-floor.
        # Length is purely bar-driven: buildup-before-drop through drop tail.
        # A 129 BPM track with bars_before=4 / bars_after=4 produces ~14.9s
        # clips; a 100 BPM track produces ~19.2s; a 140 BPM track ~13.7s.
        start_time = max(0, peak_time - (bars_before * bar_duration))
        end_time   = min(duration, peak_time + (bars_after * bar_duration))

        if bar_times:
            start_time = _snap_to_bar(start_time, bar_times, bar_duration, mode='before')
            end_time   = _snap_to_bar(end_time,   bar_times, bar_duration, mode='after')

        # Bar-aware floor only — if bar-snap collapsed the window below the
        # requested bar count (rare, can happen near track boundaries) extend
        # forward to honour the bar count, but never to a fixed seconds value.
        min_bars = max(2, (bars_before + bars_after))
        min_dur = bar_duration * min_bars
        if end_time - start_time < min_dur:
            end_time = min(duration, start_time + min_dur)

        clips.append({
            'start':          round(start_time, 2),
            'end':            round(end_time, 2),
            'duration':       round(end_time - start_time, 2),
            'duration_bars':  round((end_time - start_time) / bar_duration, 1),
            'peak_time':      round(peak_time, 2),
            'score':          round(score, 4),
            'type':           'drop',
            'bpm':            bpm,
            'bar_duration':   round(bar_duration, 4),
            'bars_before':    bars_before,
            'bars_after':     bars_after,
            'energy_contrast': round(contrast_val, 3),
        })

    # Rank by score, then re-sort chronologically and assign indices
    clips.sort(key=lambda c: c['score'], reverse=True)
    for i, c in enumerate(clips):
        c['rank'] = i + 1
    clips.sort(key=lambda c: c['start'])
    for i, c in enumerate(clips):
        c['index'] = i + 1

    print(f"  Pass 1 complete: {len(clips)} drops detected")
    return clips


# ---------------------------------------------------------------------------
# Buildup detection — Pass 2 (runs after drop detection)
# ---------------------------------------------------------------------------

def _detect_buildups_from_drops(drop_clips, features, bpm_info, duration,
                                bars_before=4, bars_after=4,
                                time_offset=0.0):
    """
    For each detected drop, scan backward in the harmonic energy signal to find
    the buildup section that precedes it.

    A genuine buildup has:
      - Rising harmonic (tonal) energy leading INTO the drop
      - Low sub-bass energy during the rise (the bass hasn't hit yet)
      - A clear start point — the harmonic trough before the rise begins

    Returns a list of buildup clip dicts (type='buildup').
    """
    if not drop_clips:
        return []

    fd           = features['frame_duration']
    bar_duration = bpm_info['bar_duration']
    bar_times    = bpm_info.get('bar_times', [])
    bar_frames   = max(1, int(bar_duration / fd))
    bpm          = bpm_info['bpm']

    # Smooth harmonic and sub-bass at bar resolution
    rms_harm_s  = uniform_filter1d(features['rms_harm'], bar_frames)
    sub_bass_s  = uniform_filter1d(features['sub_bass'], bar_frames)
    rms_harm_n  = _normalize(rms_harm_s)
    sub_bass_n  = _normalize(sub_bass_s)

    buildups = []

    for drop in drop_clips:
        # peak_time is relative to the chunk; remove time_offset to get frame index
        peak_time_local = drop['peak_time'] - time_offset
        drop_frame = max(0, int(peak_time_local / fd))

        # Search window: up to 16 bars before the drop
        max_lookback = int(16 * bar_frames)
        search_start = max(0, drop_frame - max_lookback)

        window_harm = rms_harm_n[search_start:drop_frame]
        window_bass = sub_bass_n[search_start:drop_frame]

        if len(window_harm) < bar_frames * 2:
            continue

        # Mean sub-bass level during the window — should be LOW for a true buildup
        mean_bass = float(np.mean(window_bass))
        if mean_bass > 0.55:
            # Bass is already active throughout — not a classic buildup
            continue

        # Measure harmonic gradient in the SECOND HALF of the window
        # (the rise should accelerate as it approaches the drop)
        half = len(window_harm) // 2
        harm_grad = np.gradient(window_harm[half:])
        mean_grad = float(np.mean(harm_grad))

        # Require a meaningful positive slope
        if mean_grad < 0.003:
            continue

        # Find where the buildup starts: the harmonic trough in the first 2/3 of window
        search_two_thirds = max(1, len(window_harm) * 2 // 3)
        trough_idx = int(np.argmin(window_harm[:search_two_thirds]))

        buildup_start_frame = search_start + trough_idx
        buildup_start_time  = buildup_start_frame * fd + time_offset

        # Buildup ends right at the drop peak (the release)
        buildup_end_time = drop['peak_time']

        # Snap to bar grid
        if bar_times:
            buildup_start_time = _snap_to_bar(buildup_start_time, bar_times,
                                              bar_duration, mode='before')
            buildup_end_time   = _snap_to_bar(buildup_end_time, bar_times,
                                              bar_duration, mode='after')

        buildup_start_time = max(0, buildup_start_time)
        buildup_end_time   = min(duration, buildup_end_time)

        # Need at least 4 bars
        if buildup_end_time - buildup_start_time < bar_duration * 4:
            continue

        buildups.append({
            'start':             round(buildup_start_time, 2),
            'end':               round(buildup_end_time, 2),
            'duration':          round(buildup_end_time - buildup_start_time, 2),
            'duration_bars':     round((buildup_end_time - buildup_start_time) / bar_duration, 1),
            # Buildup precedes its drop. Anchor the peak inside the buildup
            # window (the rising edge), not at the drop peak — otherwise the
            # peak-in-window dedup filter would reject every buildup.
            'peak_time':         round(buildup_end_time - bar_duration, 2),
            'score':             round(drop['score'] * 0.80, 4),  # slightly below its drop
            'type':              'buildup',
            'bpm':               bpm,
            'bar_duration':      round(bar_duration, 4),
            'bars_before':       bars_before,
            'bars_after':        bars_after,
            'energy_contrast':   drop.get('energy_contrast', 0),
            'linked_drop_index': drop.get('index'),
        })

    if buildups:
        print(f"  Pass 2 complete: {len(buildups)} buildups found")
    else:
        print("  Pass 2: no clear buildup sections found before detected drops")

    return buildups


def _dedupe_clips(clips, min_gap=4.0, min_duration=None, min_bars=8):
    """
    Strong dedup pass that runs on EVERY analyzer return path.

    Removes:
      - Clips whose `peak_time` falls outside their own `[start, end]` window
        (with one bar of slack). When that happens it means the bar-snap math
        misaligned the cut window relative to the actual drop — the cutter
        would write a slice that doesn't contain the drop. Drop them here so
        no garbage clip ever reaches the user. This is the safety net for the
        "many of the same videos" bug class.
      - Clips whose (start, end) windows overlap or sit within `min_gap`
        seconds of each other — keeps the higher-scored one.
      - Clips shorter than `min_duration` seconds (these are usually
        artefacts of bar-snap clamping or chunk-boundary slivers and they
        produce the "48 identical 7-second drops" failure mode).

    The previous _dedup() only filtered by peak_time proximity inside
    chunked analysis, which let identical (start, end) pairs slip through
    when peaks landed on the same frame. This is the belt-and-braces fix.
    """
    if not clips:
        return clips

    # Sanity: peak_time should sit inside [start, end] (with one bar of slack
    # for snap rounding). If it doesn't, the snap or chunk math went wrong —
    # the resulting mp4 wouldn't contain the actual drop.
    def _peak_in_window(c):
        peak = c.get('peak_time')
        if peak is None:
            return True  # nothing to verify
        # Allow one bar of slack on each side. bar_duration is stored on each
        # clip via _detect_drops; fall back to 2.0 s if absent.
        slack = c.get('bar_duration') or 2.0
        try:
            slack = float(slack)
        except (TypeError, ValueError):
            slack = 2.0
        return (c['start'] - slack) <= peak <= (c['end'] + slack)

    rejected_by_peak = sum(1 for c in clips if not _peak_in_window(c))
    if rejected_by_peak:
        print(f"  Dedup: dropped {rejected_by_peak} clip(s) where peak_time fell outside [start, end] — snap math misalignment")
    clips = [c for c in clips if _peak_in_window(c)]
    if not clips:
        return clips

    # Drop micro-clips first.
    # SPEC (2026-04-26): clip lengths are bar-driven. The minimum survives
    # as a *bar-count* floor (default 8 bars) instead of a fixed seconds
    # threshold — so a 140-BPM clip of 13.7s is no longer rejected.
    def _bar_dur(c):
        bd = c.get('bar_duration')
        try:
            bd = float(bd)
        except (TypeError, ValueError):
            return 2.0
        return bd if bd and bd > 0 else 2.0
    if min_duration is not None:
        # Caller asked for a hard seconds floor — honour it (e.g. tooling
        # that needs export-grade duration). Default path uses bars instead.
        clips = [c for c in clips if (c.get('end', 0) - c.get('start', 0)) >= min_duration]
    else:
        clips = [c for c in clips
                 if (c.get('end', 0) - c.get('start', 0)) >= _bar_dur(c) * min_bars * 0.95]
    if not clips:
        return clips
    # Sort by score (best first) so the survivor of any collision is the strongest
    clips.sort(key=lambda c: c.get('score', 0), reverse=True)
    kept = []
    for c in clips:
        cs, ce = c['start'], c['end']
        clash = False
        for k in kept:
            ks, ke = k['start'], k['end']
            # Overlap or within min_gap seconds counts as a duplicate
            if not (ce + min_gap <= ks or cs >= ke + min_gap):
                clash = True
                break
        if not clash:
            kept.append(c)
    kept.sort(key=lambda c: c['start'])
    return kept


def _merge_drops_and_buildups(drops, buildups, duration):
    """
    Combine drops and buildups into a single chronologically-indexed list.
    Drops come first (sorted by start time), then buildups (sorted by start time).
    This matches what the dashboard displays — drops at top, buildups below.
    """
    # Hard dedupe each group BEFORE ranking so duplicates can't all win the
    # top ranks. min_gap=4s ≈ one bar at 120 BPM. SPEC (2026-04-26): no
    # fixed seconds floor — minimum length is now `min_bars=8` bars so the
    # window scales with tempo (~13.7 s @140 BPM, ~19.2 s @100 BPM).
    drops    = _dedupe_clips(drops,    min_gap=4.0, min_bars=8)
    buildups = _dedupe_clips(buildups, min_gap=4.0, min_bars=8)

    # Rank each group by score independently
    for group in (drops, buildups):
        group.sort(key=lambda c: c['score'], reverse=True)
        for i, c in enumerate(group):
            c['rank'] = i + 1
        group.sort(key=lambda c: c['start'])

    # Assign global chronological indices: drops first, then buildups
    combined = drops + buildups
    for i, c in enumerate(combined):
        c['index'] = i + 1

    n_drops    = len(drops)
    n_buildups = len(buildups)
    print(f"  Found {len(combined)} moments total ({n_drops} drops, {n_buildups} buildups)")
    return combined


# ---------------------------------------------------------------------------
# Main analysis entry points
# ---------------------------------------------------------------------------

def analyze_dj_set(audio_path, sr=22050, clip_duration=45, min_gap=30,
                   sensitivity=0.5, bars_before=4, bars_after=4, bpm_info=None,
                   chunk_minutes=15):
    """
    Analyze a DJ set audio file using HPSS and bar-aware detection.

    Uses 11025 Hz for analysis (faster HPSS/onset — 2× less data) while
    output timestamps remain frame-accurate.  For files longer than
    chunk_minutes the audio is processed in overlapping segments to cap
    peak RAM usage — critical for 3–4 hour / 7–10 GB DJ sets.

    Args:
        audio_path: Path to audio file (WAV)
        sr: Sample rate — overridden to 11025 for speed
        clip_duration: Legacy — ignored; determined by bars_before + bars_after
        min_gap: Minimum gap between detections in seconds
        sensitivity: 0.0 (conservative) to 1.0 (aggressive)
        bars_before: Bars to include before the drop moment
        bars_after: Bars to include after the drop moment
        bpm_info: Optional pre-computed BPM info dict (skips re-detection)
        chunk_minutes: Max segment length for RAM-limited processing (default 15 min)

    Returns:
        List of clip dicts
    """
    import soundfile as sf

    analysis_sr = 11025
    info = sf.info(audio_path)
    file_sr = info.samplerate
    total_frames = info.frames
    duration = total_frames / file_sr

    print(f"  Audio file: {duration/60:.1f} min ({duration:.0f}s) @ {file_sr} Hz")

    # -------------------------------------------------------
    # Decide whether to use chunked or single-pass loading.
    # Threshold: > chunk_minutes → chunked to save RAM.
    # -------------------------------------------------------
    chunk_sec = chunk_minutes * 60
    use_chunked = duration > chunk_sec

    if use_chunked:
        print(f"  Large file ({duration/60:.0f} min) — using chunked analysis ({chunk_minutes} min segments)")
        return _analyze_chunked(
            audio_path, analysis_sr, duration,
            min_gap, sensitivity, bars_before, bars_after,
            bpm_info, chunk_sec
        )

    # Single-pass (short files or files within threshold)
    print(f"  Loading audio for analysis at {analysis_sr}Hz (optimized)...")
    y, sr_loaded = librosa.load(audio_path, sr=analysis_sr, mono=True)
    sr = analysis_sr
    print(f"  Audio loaded: {len(y)/1e6:.1f}M samples ({duration:.1f}s)")

    if bpm_info is not None:
        print(f"  Using pre-computed BPM: {bpm_info['bpm']} (skipping re-detection)")
    else:
        print("  Detecting BPM and beat grid...")
        bpm_samples = int(180 * sr)
        bpm_info = detect_bpm(None, sr=sr, y_audio=y[:bpm_samples] if len(y) > bpm_samples else y)
    print(f"  BPM: {bpm_info['bpm']}, Bar duration: {bpm_info['bar_duration']:.3f}s")

    features = _compute_features(y, sr)

    bar_duration = bpm_info['bar_duration']
    min_gap_bars = max(4, int(min_gap / bar_duration))

    drops = _detect_drops(
        features, bpm_info,
        sensitivity=sensitivity,
        bars_before=bars_before,
        bars_after=bars_after,
        min_gap_bars=min_gap_bars,
        duration=duration,
    )

    buildups = _detect_buildups_from_drops(
        drops, features, bpm_info, duration,
        bars_before=bars_before,
        bars_after=bars_after,
        time_offset=0.0,
    )

    return _merge_drops_and_buildups(drops, buildups, duration)


def _analyze_chunked(audio_path, analysis_sr, total_duration,
                     min_gap, sensitivity, bars_before, bars_after,
                     bpm_info, chunk_sec=900):
    """
    Chunked analysis for large files.  Processes audio in overlapping
    segments of chunk_sec seconds (default 15 min) to keep peak RAM low.

    Overlap = 30 s each side so drops at chunk boundaries are not missed.
    Results are deduplicated by peak_time proximity (> 2 s apart).
    """
    import soundfile as sf

    OVERLAP = 30  # seconds overlap on each side

    # --- First, detect BPM from a 3-minute sample in the middle ---
    if bpm_info is None:
        mid_start = max(0, total_duration / 2 - 90)
        print(f"  Detecting BPM from 3-min sample at {mid_start:.0f}s...")
        y_bpm, _ = librosa.load(audio_path, sr=analysis_sr, mono=True,
                                offset=mid_start, duration=180)
        bpm_info = detect_bpm(None, sr=analysis_sr, y_audio=y_bpm)
        del y_bpm
        print(f"  BPM: {bpm_info['bpm']}, bar_duration: {bpm_info['bar_duration']:.3f}s")

    all_drops = []
    all_buildups = []
    chunk_start = 0.0
    chunk_idx = 0

    while chunk_start < total_duration:
        # Load chunk with overlap on both sides
        load_start = max(0.0, chunk_start - OVERLAP)
        load_dur = chunk_sec + OVERLAP * 2
        load_dur = min(load_dur, total_duration - load_start)

        print(f"  Chunk {chunk_idx + 1}: loading {load_start:.0f}s – {load_start + load_dur:.0f}s "
              f"({load_dur/60:.1f} min)...")

        y_chunk, _ = librosa.load(audio_path, sr=analysis_sr, mono=True,
                                  offset=load_start, duration=load_dur)
        chunk_actual_dur = len(y_chunk) / analysis_sr

        # Build a local bpm_info — bar_times must tile the FULL chunk in chunk-local
        # time. The previous filter retained only bars that happened to land in
        # [0, chunk_actual_dur] from the global list; but `bpm_info['bar_times']`
        # only spans the first ~180 s of audio (BPM was sampled there), so for any
        # chunk longer than 180 s _snap_to_bar collapsed every later peak to the
        # last anchor. That's the bug behind "many of the same videos" — every
        # peak past second 180 of a chunk produced an identical (start, end)
        # window and the cutter wrote the wrong slice.
        #
        # Synthesise a bar grid for the chunk from bar_duration, anchored to the
        # phase of the first known bar so we keep the BPM's downbeat alignment.
        local_bpm_info = dict(bpm_info)
        chunk_bar_dur = bpm_info.get('bar_duration', 0) or 0
        global_bars = bpm_info.get('bar_times', []) or []
        if chunk_bar_dur > 0:
            phase = (global_bars[0] % chunk_bar_dur) if global_bars else 0.0
            n_bars = int(chunk_actual_dur / chunk_bar_dur) + 2
            local_bpm_info['bar_times'] = [
                round(phase + i * chunk_bar_dur, 3) for i in range(n_bars)
            ]
        else:
            local_bpm_info['bar_times'] = []

        features = _compute_features(y_chunk, analysis_sr)
        del y_chunk  # free RAM immediately

        bar_duration = bpm_info['bar_duration']
        min_gap_bars = max(4, int(min_gap / bar_duration))

        # Pass 1 — drops (times relative to chunk start = 0)
        chunk_drops = _detect_drops(
            features, local_bpm_info,
            sensitivity=sensitivity,
            bars_before=bars_before,
            bars_after=bars_after,
            min_gap_bars=min_gap_bars,
            duration=chunk_actual_dur,
        )

        # Pass 2 — buildups (uses same features; times still chunk-local)
        chunk_buildups = _detect_buildups_from_drops(
            chunk_drops, features, local_bpm_info, chunk_actual_dur,
            bars_before=bars_before,
            bars_after=bars_after,
            time_offset=0.0,  # chunk times are 0-based here
        )

        # Offset all timestamps by load_start so they become global positions,
        # then keep only clips whose peak falls in the non-overlap core window.
        for clip in chunk_drops + chunk_buildups:
            for key in ('start', 'end', 'peak_time'):
                if key in clip:
                    clip[key] = round(clip[key] + load_start, 2)
                    if key in ('start', 'end'):
                        clip[key] = max(0.0, min(total_duration, clip[key]))

            peak = clip.get('peak_time', clip['start'])
            in_core = (
                peak >= chunk_start and
                peak < (chunk_start + chunk_sec)
            )
            if in_core or (chunk_idx == 0 and peak < OVERLAP):
                if clip['type'] == 'drop':
                    all_drops.append(clip)
                else:
                    all_buildups.append(clip)

        chunk_start += chunk_sec
        chunk_idx += 1
        print(f"  Chunk {chunk_idx}: found {len(chunk_drops)} drops, {len(chunk_buildups)} buildups")

    # De-duplicate drops by peak_time proximity (> 2 s apart)
    def _dedup(clips):
        clips.sort(key=lambda c: c.get('peak_time', c['start']))
        out, last_peak = [], -9999.0
        for c in clips:
            peak = c.get('peak_time', c['start'])
            if peak - last_peak > 2.0:
                out.append(c)
                last_peak = peak
        return out

    all_drops    = _dedup(all_drops)
    all_buildups = _dedup(all_buildups)

    result = _merge_drops_and_buildups(all_drops, all_buildups, total_duration)
    print(f"  Chunked analysis complete: {len(result)} clips from {total_duration/60:.1f} min set")
    return result


def analyze_with_demucs(audio_path, sr=22050, clip_duration=45, min_gap=30,
                        sensitivity=0.5, bars_before=4, bars_after=4):
    """
    Analyze using Demucs AI source separation for highest accuracy.
    Falls back to HPSS-based analysis if Demucs is not installed.
    """
    try:
        import torch
        from demucs.api import Separator
    except ImportError:
        print("  Demucs/torch not available, falling back to HPSS analysis...")
        return analyze_dj_set(audio_path, sr=sr, clip_duration=clip_duration,
                              min_gap=min_gap, sensitivity=sensitivity,
                              bars_before=bars_before, bars_after=bars_after)

    # Pick the fastest available device: Apple Metal (mps) on Apple Silicon,
    # CUDA on Nvidia rigs, CPU as the safe fallback. Demucs is 5-10x faster
    # on MPS than CPU on M-series chips.
    if torch.cuda.is_available():
        device = "cuda"
    elif getattr(torch.backends, "mps", None) and torch.backends.mps.is_available():
        device = "mps"
    else:
        device = "cpu"
    print(f"  Running Demucs AI separation (htdemucs) on {device}...")
    separator = Separator(model="htdemucs", device=device)
    # separator.separate_audio_file handles its own audio loading — no need
    # to pre-load with librosa.load (that was wasting memory on long sets).
    origin, separated = separator.separate_audio_file(audio_path)

    # Demucs exposes its working sample rate on the separator instance.
    sr_orig = getattr(separator, 'samplerate', 44100)

    # separated is a dict with keys: drums, bass, other, vocals
    drums = separated['drums'].mean(dim=0).numpy()  # Mono
    bass_stem = separated['bass'].mean(dim=0).numpy()
    other = separated['other'].mean(dim=0).numpy()
    vocals = separated['vocals'].mean(dim=0).numpy()

    # Resample to analysis sr
    if sr_orig != sr:
        drums = librosa.resample(drums, orig_sr=sr_orig, target_sr=sr)
        bass_stem = librosa.resample(bass_stem, orig_sr=sr_orig, target_sr=sr)
        other = librosa.resample(other, orig_sr=sr_orig, target_sr=sr)

    duration = librosa.get_duration(y=drums, sr=sr)
    print(f"  Demucs separation complete: {duration:.1f}s ({duration/60:.1f} min)")

    # Detect BPM from drums (most accurate)
    print("  Detecting BPM from drum track...")
    bpm_info = detect_bpm(None, sr=sr, y_audio=drums)
    print(f"  BPM: {bpm_info['bpm']}, Bar duration: {bpm_info['bar_duration']:.3f}s")

    # Compute features from separated stems
    features = _compute_features_demucs(drums, bass_stem, other, sr)

    bar_duration = bpm_info['bar_duration']
    min_gap_bars = max(4, int(min_gap / bar_duration))

    drops = _detect_drops(
        features, bpm_info,
        sensitivity=sensitivity,
        bars_before=bars_before,
        bars_after=bars_after,
        min_gap_bars=min_gap_bars,
        duration=duration,
    )

    buildups = _detect_buildups_from_drops(
        drops, features, bpm_info, duration,
        bars_before=bars_before,
        bars_after=bars_after,
        time_offset=0.0,
    )

    return _merge_drops_and_buildups(drops, buildups, duration)


# ---------------------------------------------------------------------------
# Utilities (used by app.py)
# ---------------------------------------------------------------------------

def create_manual_clip(peak_time, clip_duration, total_duration):
    """
    Create a manually-specified clip centered on `peak_time`.

    Clamps to [0, total_duration]. If `clip_duration` exceeds the available
    span (rare — very short videos), we just use the whole thing.
    """
    if clip_duration >= total_duration:
        start, end = 0.0, float(total_duration)
    else:
        half_clip = clip_duration / 2
        # Tentative window centered on peak
        start = peak_time - half_clip
        end = peak_time + half_clip
        # Shift right if we underflow the start
        if start < 0:
            end += -start
            start = 0.0
        # Shift left if we overflow the end
        if end > total_duration:
            start -= end - total_duration
            end = float(total_duration)
        start = max(0.0, start)

    return {
        'start': round(start, 2),
        'end': round(end, 2),
        'duration': round(end - start, 2),
        'peak_time': round(peak_time, 2),
        'score': 1.0,
        'type': 'manual',
        'bpm': 0.0,
    }


def get_waveform_data(audio_path, sr=22050, num_points=2000):
    """
    Get downsampled waveform data for visualization.
    Uses a fast block-RMS approach. Returns list of {time, amplitude} points.
    """
    import soundfile as sf

    info = sf.info(audio_path)
    total_frames = info.frames
    file_sr = info.samplerate
    duration = total_frames / file_sr

    chunk_size = max(1, total_frames // num_points)
    points = []
    with sf.SoundFile(audio_path) as f:
        block_idx = 0
        while f.tell() < total_frames and len(points) < num_points:
            data = f.read(chunk_size, dtype='float32')
            if len(data) == 0:
                break
            if data.ndim > 1:
                data = data.mean(axis=1)
            amplitude = float(np.sqrt(np.mean(data ** 2)))
            time_sec = (block_idx * chunk_size + chunk_size // 2) / file_sr
            points.append({'time': round(time_sec, 2), 'amplitude': round(amplitude, 4)})
            block_idx += 1

    return points, duration
