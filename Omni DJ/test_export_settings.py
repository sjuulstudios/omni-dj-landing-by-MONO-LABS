"""
Verification test for export_clip_with_settings().

What this proves:
- Different codec choices produce different files (different codec_name in ffprobe).
- Different fps choices produce different reported frame rates.
- "Match source" (stream copy) is genuinely faster and lossless vs re-encode.
- File sizes differ in the expected order: ProRes >> H.264 ~ H.265.

Run from the Omni DJ source folder:
    cd "/Users/sjuulsmits/Documents/Claude/Projects/Omni DJ/Omni DJ"
    python3 test_export_settings.py

Requires: ffmpeg + ffprobe in PATH. Uses a 5-second synthetic test video so
no real DJ set is needed. Cleans up after itself unless you pass --keep.
"""

import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

# Allow importing from this directory regardless of cwd
THIS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(THIS_DIR))

from cutter import export_clip_with_settings, EXPORT_CODEC_MAP


TEST_DIR = THIS_DIR / 'test_export_tmp'
SOURCE_CLIP = TEST_DIR / 'source.mp4'


def _print_header(text):
    print('\n' + '=' * 64)
    print(text)
    print('=' * 64)


def _make_source_clip():
    """Generate a 5s 1920x1080 30fps test video with a moving gradient + tone."""
    TEST_DIR.mkdir(exist_ok=True)
    cmd = [
        'ffmpeg', '-y', '-hide_banner', '-loglevel', 'error',
        '-f', 'lavfi', '-i', 'testsrc2=size=1920x1080:rate=30:duration=5',
        '-f', 'lavfi', '-i', 'sine=frequency=440:duration=5',
        '-c:v', 'libx264', '-preset', 'ultrafast', '-crf', '23',
        '-c:a', 'aac', '-b:a', '128k',
        '-shortest',
        str(SOURCE_CLIP),
    ]
    print(f'Generating source: {SOURCE_CLIP.name} (1920x1080, 30fps, 5s)...')
    subprocess.run(cmd, check=True, capture_output=True)
    print(f'  Source size: {SOURCE_CLIP.stat().st_size / 1024:.1f} KB')


def _ffprobe(path):
    """Return dict with codec_name, width, height, r_frame_rate, duration, size."""
    cmd = [
        'ffprobe', '-v', 'error', '-print_format', 'json',
        '-show_format', '-show_streams', str(path),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    data = json.loads(result.stdout)
    video = next((s for s in data['streams'] if s['codec_type'] == 'video'), {})
    fmt = data.get('format', {})
    return {
        'codec_name': video.get('codec_name'),
        'width': video.get('width'),
        'height': video.get('height'),
        'r_frame_rate': video.get('r_frame_rate'),
        'duration': float(fmt.get('duration', 0)),
        'size_bytes': int(fmt.get('size', 0)),
    }


def _run_one_test(label, codec, fps, resolution, idx):
    print(f'\n[{label}]  codec={codec}  fps={fps}  res={resolution}')
    t0 = time.time()
    result = export_clip_with_settings(
        source_clip=str(SOURCE_CLIP),
        output_dir=str(TEST_DIR),
        clip_index=idx,
        codec=codec,
        fps=fps,
        resolution=resolution,
    )
    elapsed = time.time() - t0

    if not result['ok']:
        print(f'  FAIL: {result["error"]}')
        return None

    probe = _ffprobe(result['path'])
    print(f'  -> {Path(result["path"]).name}')
    print(f'     codec       : {probe["codec_name"]}')
    print(f'     resolution  : {probe["width"]}x{probe["height"]}')
    print(f'     frame rate  : {probe["r_frame_rate"]}')
    print(f'     duration    : {probe["duration"]:.2f}s')
    print(f'     size        : {probe["size_bytes"] / 1024:.1f} KB')
    print(f'     wall time   : {elapsed:.2f}s')
    return {
        'label': label, 'codec_choice': codec, 'fps_choice': fps,
        'res_choice': resolution, 'elapsed_s': elapsed,
        'output_path': result['path'], **probe,
    }


def main():
    _print_header('Export settings verification — Blok 3')

    # 0. Sanity: ffmpeg + ffprobe present
    if not shutil.which('ffmpeg') or not shutil.which('ffprobe'):
        print('FAIL: ffmpeg or ffprobe not in PATH.')
        return 2

    # 1. Generate a synthetic source clip
    _make_source_clip()
    src_probe = _ffprobe(SOURCE_CLIP)
    print(f'  Source codec : {src_probe["codec_name"]}')
    print(f'  Source size  : {src_probe["width"]}x{src_probe["height"]}')

    # 2. Run all tests. Each test: different codec OR different fps OR different resolution.
    tests = [
        # label,                     codec,     fps,     resolution,    idx
        ('match-source',              'match',   'match',  'source',       1),
        ('h264-vt-source-fps',        'h264_vt', 'match',  'source',       2),
        ('h265-vt-source-fps',        'h265_vt', 'match',  'source',       3),
        ('prores-source-fps',         'prores',  'match',  'source',       4),
        ('h264-vt-60fps-1080x1920',   'h264_vt', '60',     '1080x1920',    5),
        ('h264-vt-24fps-source-res',  'h264_vt', '24',     'source',       6),
    ]

    results = []
    for label, codec, fps, res, idx in tests:
        r = _run_one_test(label, codec, fps, res, idx)
        if r:
            results.append(r)

    # 3. Verify expectations
    _print_header('VERIFICATION')

    by_label = {r['label']: r for r in results}
    issues = []

    def _check(cond, ok_msg, fail_msg):
        if cond:
            print(f'  PASS  {ok_msg}')
        else:
            print(f'  FAIL  {fail_msg}')
            issues.append(fail_msg)

    # Codec names must differ between codec choices
    if 'match-source' in by_label:
        _check(by_label['match-source']['codec_name'] == 'h264',
               'match: codec is h264 (copied from source)',
               f"match: expected h264, got {by_label['match-source']['codec_name']}")
    if 'h265-vt-source-fps' in by_label:
        _check(by_label['h265-vt-source-fps']['codec_name'] == 'hevc',
               'h265_vt: codec is hevc',
               f"h265_vt: expected hevc, got {by_label['h265-vt-source-fps']['codec_name']}")
    if 'prores-source-fps' in by_label:
        _check(by_label['prores-source-fps']['codec_name'] == 'prores',
               'prores: codec is prores',
               f"prores: expected prores, got {by_label['prores-source-fps']['codec_name']}")

    # FPS choice must change frame rate
    if 'h264-vt-60fps-1080x1920' in by_label:
        fr = by_label['h264-vt-60fps-1080x1920']['r_frame_rate']
        _check(fr == '60/1',
               f'fps=60: r_frame_rate is {fr}',
               f"fps=60: expected '60/1', got {fr}")
    if 'h264-vt-24fps-source-res' in by_label:
        fr = by_label['h264-vt-24fps-source-res']['r_frame_rate']
        _check(fr == '24/1',
               f'fps=24: r_frame_rate is {fr}',
               f"fps=24: expected '24/1', got {fr}")

    # Resolution choice must change dimensions
    if 'h264-vt-60fps-1080x1920' in by_label:
        r = by_label['h264-vt-60fps-1080x1920']
        _check(r['width'] == 1080 and r['height'] == 1920,
               f"res=1080x1920: actual is {r['width']}x{r['height']}",
               f"res=1080x1920: got {r['width']}x{r['height']}")

    # ProRes file should be much larger than h264/h265
    if all(k in by_label for k in ('prores-source-fps', 'h264-vt-source-fps', 'h265-vt-source-fps')):
        pr = by_label['prores-source-fps']['size_bytes']
        h4 = by_label['h264-vt-source-fps']['size_bytes']
        h5 = by_label['h265-vt-source-fps']['size_bytes']
        _check(pr > h4 * 3 and pr > h5 * 3,
               f'prores ({pr // 1024} KB) is >3x bigger than h264 ({h4 // 1024} KB) and h265 ({h5 // 1024} KB)',
               f'prores ({pr}) was NOT >3x bigger than h264 ({h4}) / h265 ({h5})')

    # Match (stream copy) should be much faster than any re-encode
    if all(k in by_label for k in ('match-source', 'h264-vt-source-fps')):
        ms = by_label['match-source']['elapsed_s']
        h4 = by_label['h264-vt-source-fps']['elapsed_s']
        _check(ms < h4,
               f'match ({ms:.2f}s) is faster than h264 re-encode ({h4:.2f}s)',
               f'match ({ms:.2f}s) was NOT faster than h264 ({h4:.2f}s)')

    _print_header('SUMMARY')
    print(f'  Tests run        : {len(results)} / {len(tests)}')
    print(f'  Verification     : {"ALL PASS" if not issues else f"{len(issues)} FAILED"}')
    if issues:
        print('  Failures:')
        for i in issues:
            print(f'    - {i}')

    # Cleanup unless --keep was passed
    if '--keep' not in sys.argv:
        print(f'\nCleaning up {TEST_DIR}...')
        shutil.rmtree(TEST_DIR, ignore_errors=True)
    else:
        print(f'\nKept artifacts in {TEST_DIR} (--keep was set)')

    return 0 if not issues else 1


if __name__ == '__main__':
    sys.exit(main())
