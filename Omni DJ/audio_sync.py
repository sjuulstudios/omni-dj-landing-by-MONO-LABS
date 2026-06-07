"""audio_sync.py - Spoor D: match a loose camera/GoPro video against a clean
audio recording of the same DJ set, then mux the clean audio under the video.

DESIGN (zie PLAN-COMBINED... sectie 4e):
- Volledig LOS van analyzer.py/cutter.py. Deze module raakt de bestaande
  analyse/cut/export-pipeline NIET aan. Hij produceert EEN gewoon (gemuxed)
  videobestand dat daarna de bestaande pipeline in kan.
- Offset: cross-correlatie van de onset-envelopes (librosa, zit al in de stack)
  van het camera-boordgeluid en de schone audio -> begin-offset, volautomatisch.
- Drift: vergelijk de offset aan het begin met die aan het eind (camera- en
  recorder-klok lopen uiteen over lange sets) -> drift in seconden + een milde,
  geclampte atempo-correctie. Buiten een veilige marge: alleen WAARSCHUWEN.
- Confidence: genormaliseerde cross-correlatie-piek in [0,1].
- Output: de schone audio als hoofdspoor (offset + drift toegepast); het
  camera-boordgeluid blijft als tweede audiospoor bewaard (voor crowd/ambient
  inmix in de editor, D5). Video wordt gekopieerd (geen re-encode).

CONVENTIES (verifieer op de eerste echte run, sign/drift zijn lastig blind):
- offset_s > 0  : de schone audio moet LATER beginnen -> we vertragen 'm (adelay).
- offset_s < 0  : de schone audio loopt voor -> we knippen het begin eraf (atrim).
- drift_s       : (offset_eind - offset_begin). > 0 = schone audio loopt aan het
                  eind verder achter -> we versnellen 'm minimaal (atempo > 1).

Alle ffmpeg/ffprobe-calls krijgen het binary-pad mee van de caller (app.py lost
de gebundelde static binaries al op); default valt terug op PATH.
"""

import json
import os
import subprocess
import tempfile

import numpy as np

try:
    import librosa
except Exception:  # pragma: no cover - librosa hoort in de stack te zitten
    librosa = None


# Analyse-samplerate voor de envelope-match. Laag genoeg om snel te zijn, hoog
# genoeg voor transient-precisie op ~10ms-schaal.
_SR = 22050
_HOP = 256  # ~11.6ms per frame bij 22050 Hz


class AudioSyncError(Exception):
    """Nette fout zodat de endpoint 'm in JSON kan vertalen i.p.v. een 500."""


def _run(cmd):
    """Draai een subprocess, raise AudioSyncError met stderr-staart bij falen."""
    try:
        p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except FileNotFoundError as e:
        raise AudioSyncError("binary not found: %s" % e)
    if p.returncode != 0:
        tail = (p.stderr or b"").decode("utf-8", "replace")[-800:]
        raise AudioSyncError("command failed (%d): %s" % (p.returncode, tail))
    return p


def probe_duration(path, ffprobe_bin="ffprobe"):
    """Duur in seconden via ffprobe; 0.0 als onbekend."""
    try:
        p = _run([
            ffprobe_bin, "-v", "quiet", "-print_format", "json",
            "-show_format", path,
        ])
        data = json.loads(p.stdout.decode("utf-8", "replace") or "{}")
        return float(data.get("format", {}).get("duration") or 0.0)
    except Exception:
        return 0.0


def extract_audio(src_path, out_wav, ffmpeg_bin="ffmpeg", sr=_SR):
    """Trek een mono WAV op `sr` uit een willekeurig media-bestand (video of audio)."""
    _run([
        ffmpeg_bin, "-y", "-i", src_path,
        "-vn", "-ac", "1", "-ar", str(sr), "-f", "wav", out_wav,
    ])
    return out_wav


def _onset_env(wav_path, sr=_SR, hop=_HOP):
    """Onset-strength envelope (genormaliseerd) als 1D float32-array."""
    if librosa is None:
        raise AudioSyncError("librosa not available")
    y, _sr = librosa.load(wav_path, sr=sr, mono=True)
    if y.size == 0:
        raise AudioSyncError("empty audio track")
    env = librosa.onset.onset_strength(y=y, sr=sr, hop_length=hop)
    env = np.asarray(env, dtype=np.float32)
    # Normaliseer (centreer + schaal) zodat de cross-correlatie betekenisvol is.
    env = env - env.mean()
    n = np.linalg.norm(env)
    if n > 0:
        env = env / n
    return env


def _xcorr_lag(ref, sig):
    """Lag (in frames) die `sig` t.o.v. `ref` het best uitlijnt, plus een
    confidence in [0,1] uit de genormaliseerde piek. Positieve lag = `sig` moet
    naar later (begint eerder dan ref)."""
    if ref.size == 0 or sig.size == 0:
        return 0, 0.0
    full = np.correlate(ref, sig, mode="full")  # lengte len(ref)+len(sig)-1
    idx = int(np.argmax(full))
    peak = float(full[idx])
    lag = idx - (len(sig) - 1)
    # Confidence: piek t.o.v. de energie van de kortste reeks (beide al unit-norm,
    # dus de piek ligt ~[0,1]); clamp voor de zekerheid.
    conf = max(0.0, min(1.0, peak))
    return lag, conf


def estimate_offset(onboard_wav, clean_wav, sr=_SR, hop=_HOP):
    """Begin-offset (seconden) + confidence tussen camera-boordgeluid en schone
    audio, via onset-envelope cross-correlatie over (max) de eerste ~3 minuten."""
    env_on = _onset_env(onboard_wav, sr, hop)
    env_cl = _onset_env(clean_wav, sr, hop)
    # Beperk tot een venster aan het begin voor snelheid + omdat de begin-offset
    # daar het meest betrouwbaar is.
    win = int((180 * sr) / hop)  # ~3 min aan frames
    a = env_on[:win]
    b = env_cl[:win]
    lag, conf = _xcorr_lag(a, b)
    offset_s = (lag * hop) / float(sr)
    return offset_s, conf


def estimate_drift(onboard_wav, clean_wav, duration_s, sr=_SR, hop=_HOP,
                   win_s=60.0):
    """Schat klok-drift: offset in een venster aan het BEGIN vs aan het EIND.
    Returnt drift_s = (offset_eind - offset_begin). Best-effort: 0.0 als de set
    te kort is of de match te zwak."""
    if duration_s < (3 * win_s):
        return 0.0  # te kort om drift betrouwbaar te meten
    env_on = _onset_env(onboard_wav, sr, hop)
    env_cl = _onset_env(clean_wav, sr, hop)
    fwin = int((win_s * sr) / hop)
    n = min(len(env_on), len(env_cl))
    if n < (2 * fwin):
        return 0.0
    # Begin-venster en eind-venster.
    a0, b0 = env_on[:fwin], env_cl[:fwin]
    a1, b1 = env_on[n - fwin:n], env_cl[n - fwin:n]
    lag0, c0 = _xcorr_lag(a0, b0)
    lag1, c1 = _xcorr_lag(a1, b1)
    if c0 < 0.05 or c1 < 0.05:
        return 0.0  # te onzeker -> geen drift-claim
    drift_s = ((lag1 - lag0) * hop) / float(sr)
    return drift_s


def _clean_filter(offset_s, tempo_ratio):
    """Bouw de ffmpeg-audiofilter voor de schone audio: offset (adelay/atrim) +
    optionele milde tempo-correctie voor drift."""
    parts = []
    if offset_s >= 0.0:
        ms = int(round(offset_s * 1000))
        if ms > 0:
            parts.append("adelay=%d:all=1" % ms)
    else:
        parts.append("atrim=start=%.3f" % (abs(offset_s)))
        parts.append("asetpts=PTS-STARTPTS")
    if tempo_ratio and abs(tempo_ratio - 1.0) > 1e-4:
        parts.append("atempo=%.6f" % tempo_ratio)
    if not parts:
        parts.append("anull")
    return "[1:a]" + ",".join(parts) + "[ca]"


def _drift_to_tempo(drift_s, dur, drift_safe_s=0.25, tempo_clamp=0.03):
    """Zet gemeten drift om in een (geclampte) atempo-ratio + waarschuwingen.
    Identieke logica als de auto-tak van sync_and_mux, gedeeld zodat analyze()
    en sync_and_mux niet uiteenlopen."""
    warnings = []
    tempo_ratio = 1.0
    if dur > 0 and abs(drift_s) >= drift_safe_s:
        denom = dur - drift_s
        # denom <= 0 (drift >= duur, pathologisch) -> 0.0 valt buiten de clamp,
        # dus we waarschuwen i.p.v. misleidend "gecorrigeerd" te melden.
        tempo_ratio = (dur / denom) if denom > 0 else 0.0
        lo, hi = 1.0 - tempo_clamp, 1.0 + tempo_clamp
        if tempo_ratio < lo or tempo_ratio > hi:
            warnings.append(
                "Drift of %.2fs measured over the set; that is outside the safe "
                "auto-correction range. No tempo correction applied; check the "
                "end of the clip and align manually if needed." % drift_s)
            tempo_ratio = 1.0
        else:
            warnings.append(
                "Corrected %.2fs of drift over the set; check the end." % drift_s)
    return tempo_ratio, warnings


def _downsample_env(env, frames, points):
    """Neem de eerste `frames` van een envelope en hervat naar `points` waarden,
    genormaliseerd naar 0..1, als lichte JSON-vriendelijke lijst voor de UI."""
    seg = env[:frames] if (frames and frames < len(env)) else env
    if seg.size == 0:
        return []
    if seg.size > points:
        xs = np.linspace(0, seg.size - 1, points)
        seg = np.interp(xs, np.arange(seg.size), seg)
    mn = float(seg.min())
    mx = float(seg.max())
    rng = (mx - mn) or 1.0
    return [round(float((v - mn) / rng), 4) for v in seg]


def _run_mux(video_path, clean_audio_path, out_path, ffmpeg_bin, offset_s, tempo_ratio):
    """De daadwerkelijke mux: video copy, schone audio = spoor 0 (default),
    camera-audio = spoor 1. Gedeeld door sync_and_mux (auto) en de manual-flow."""
    flt = _clean_filter(offset_s, tempo_ratio)
    cmd = [
        ffmpeg_bin, "-y",
        "-i", video_path,
        "-i", clean_audio_path,
        "-filter_complex", flt,
        "-map", "0:v:0",
        "-map", "[ca]",
        "-map", "0:a:0?",
        "-c:v", "copy",
        "-c:a", "aac", "-b:a", "256k",
        "-metadata:s:a:0", "title=Clean mix",
        "-metadata:s:a:1", "title=Camera (crowd)",
        "-disposition:a:0", "default",
        "-shortest",
        out_path,
    ]
    _run(cmd)
    if not os.path.exists(out_path) or os.path.getsize(out_path) == 0:
        raise AudioSyncError("mux did not produce a valid file")


def analyze(video_path, clean_audio_path, ffmpeg_bin="ffmpeg", ffprobe_bin="ffprobe",
            drift_safe_s=0.25, tempo_clamp=0.03, window_s=120.0, points=600):
    """Bereken offset/confidence/drift ZONDER te muxen, plus lichte downsampled
    waveforms (de eerste `window_s` seconden) voor de manuele uitlijn-UI (D4).
    Spoor D, fail-gedrag: de endpoint gebruikt dit om bij lage confidence eerst
    handmatig te laten uitlijnen i.p.v. stil een slechte sync te bakken."""
    if not os.path.exists(video_path):
        raise AudioSyncError("video does not exist: %s" % video_path)
    if not os.path.exists(clean_audio_path):
        raise AudioSyncError("audio does not exist: %s" % clean_audio_path)
    tmpd = tempfile.mkdtemp(prefix="omnidj_an_")
    try:
        onboard_wav = os.path.join(tmpd, "onboard.wav")
        clean_wav = os.path.join(tmpd, "clean.wav")
        try:
            extract_audio(video_path, onboard_wav, ffmpeg_bin)
        except AudioSyncError:
            raise AudioSyncError(
                "no camera audio found in the video; sync needs the onboard sound")
        extract_audio(clean_audio_path, clean_wav, ffmpeg_bin)

        env_on = _onset_env(onboard_wav)
        env_cl = _onset_env(clean_wav)
        win = int((180 * _SR) / _HOP)
        lag, conf = _xcorr_lag(env_on[:win], env_cl[:win])
        offset_s = (lag * _HOP) / float(_SR)
        dur = probe_duration(video_path, ffprobe_bin) or probe_duration(clean_audio_path, ffprobe_bin)
        drift_s = estimate_drift(onboard_wav, clean_wav, dur)
        tempo_ratio, warnings = _drift_to_tempo(drift_s, dur, drift_safe_s, tempo_clamp)
        if conf < 0.15:
            warnings.append(
                "Low match confidence (%.0f%%). Possibly silence at the start or the "
                "wrong file; check the sync or align manually." % (conf * 100))
        frames = int((window_s * _SR) / _HOP)
        return {
            "offset_s": round(offset_s, 3),
            "confidence": round(conf, 3),
            "drift_s": round(drift_s, 3),
            "tempo_ratio": round(tempo_ratio, 6),
            "window_s": window_s,
            "onboard": _downsample_env(env_on, frames, points),
            "clean": _downsample_env(env_cl, frames, points),
            "warnings": warnings,
        }
    finally:
        try:
            for f in os.listdir(tmpd):
                try:
                    os.remove(os.path.join(tmpd, f))
                except OSError:
                    pass
            os.rmdir(tmpd)
        except OSError:
            pass


def mux_with_offset(video_path, clean_audio_path, out_path,
                    ffmpeg_bin="ffmpeg", ffprobe_bin="ffprobe", offset_s=0.0):
    """Mux met een EXPLICIETE (handmatig gekozen) offset, geen drift-correctie.
    Gebruikt door de manual-align-flow (D4) nadat de gebruiker heeft uitgelijnd."""
    if not os.path.exists(video_path):
        raise AudioSyncError("video does not exist: %s" % video_path)
    if not os.path.exists(clean_audio_path):
        raise AudioSyncError("audio does not exist: %s" % clean_audio_path)
    _run_mux(video_path, clean_audio_path, out_path, ffmpeg_bin, float(offset_s), 1.0)
    return {
        "ok": True,
        "output_path": out_path,
        "offset_s": round(float(offset_s), 3),
        "drift_s": 0.0,
        "tempo_ratio": 1.0,
        "confidence": 1.0,
        "camera_audio_kept": True,
        "manual": True,
        "warnings": ["Manual alignment used (offset %.2fs)." % float(offset_s)],
    }


def sync_and_mux(video_path, clean_audio_path, out_path,
                 ffmpeg_bin="ffmpeg", ffprobe_bin="ffprobe",
                 drift_safe_s=0.25, tempo_clamp=0.03):
    """Volledige sync-stap. Returnt een dict met metrics + waarschuwingen.

    - drift_safe_s : drift kleiner dan dit negeren we (geen correctie nodig).
    - tempo_clamp  : maximale atempo-afwijking die we automatisch toepassen
                     (bv. 0.03 = 0.97..1.03). Daarbuiten: alleen waarschuwen.
    """
    if not os.path.exists(video_path):
        raise AudioSyncError("video does not exist: %s" % video_path)
    if not os.path.exists(clean_audio_path):
        raise AudioSyncError("audio does not exist: %s" % clean_audio_path)

    warnings = []
    tmpd = tempfile.mkdtemp(prefix="omnidj_sync_")
    try:
        onboard_wav = os.path.join(tmpd, "onboard.wav")
        clean_wav = os.path.join(tmpd, "clean.wav")
        # Camera-boordgeluid eruit; faalt als de video geen audiospoor heeft.
        try:
            extract_audio(video_path, onboard_wav, ffmpeg_bin)
        except AudioSyncError:
            raise AudioSyncError(
                "no camera audio found in the video; sync needs the onboard sound")
        extract_audio(clean_audio_path, clean_wav, ffmpeg_bin)

        offset_s, conf = estimate_offset(onboard_wav, clean_wav)
        dur = probe_duration(video_path, ffprobe_bin) or probe_duration(clean_audio_path, ffprobe_bin)
        drift_s = estimate_drift(onboard_wav, clean_wav, dur)

        # Drift -> (geclampte) tempo-correctie, gedeelde logica met analyze().
        tempo_ratio, _dwarn = _drift_to_tempo(drift_s, dur, drift_safe_s, tempo_clamp)
        warnings.extend(_dwarn)

        if conf < 0.15:
            warnings.append(
                "Low match confidence (%.0f%%). Possibly silence at the start or the "
                "wrong file; check the sync or align manually." % (conf * 100))

        _run_mux(video_path, clean_audio_path, out_path, ffmpeg_bin, offset_s, tempo_ratio)

        return {
            "ok": True,
            "output_path": out_path,
            "offset_s": round(offset_s, 3),
            "drift_s": round(drift_s, 3),
            "tempo_ratio": round(tempo_ratio, 6),
            "confidence": round(conf, 3),
            "camera_audio_kept": True,
            "warnings": warnings,
        }
    finally:
        # Tmp-WAVs opruimen (de output staat buiten tmpd).
        try:
            for f in os.listdir(tmpd):
                try:
                    os.remove(os.path.join(tmpd, f))
                except OSError:
                    pass
            os.rmdir(tmpd)
        except OSError:
            pass
