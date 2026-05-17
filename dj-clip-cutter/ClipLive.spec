# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller-specfile voor Clip Live (macOS).

Bouw met:    pyinstaller --noconfirm ClipLive.spec

Resultaat:   dist/Clip Live.app   (open met `open dist/Clip\\ Live.app`)

Vereiste vooraf:
    pip install pyinstaller dmgbuild

Belangrijk:
    - FFmpeg wordt NIET door deze spec gebundeld. De build_macos.sh
      kopieert ffmpeg + ffprobe binaries naar de bundle. Dit zorgt dat
      eindgebruikers niet zelf "brew install ffmpeg" hoeven te draaien.
    - Optionele zware deps (torch, demucs, ultralytics) zijn UITGESLOTEN
      — dat scheelt 2 GB en de app fallt graceful terug als ze afwezig zijn.
    - Code-signing en notarization gebeuren ná de PyInstaller-stap, zie
      INSTALLER-RUNBOOK.md.
"""

from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

# --------------------------------------------------------------------------- #
# Hidden imports — modules die librosa/scipy/numba dynamisch laden en die
# PyInstaller's static analysis daarom mist.
# --------------------------------------------------------------------------- #
hiddenimports = []
hiddenimports += collect_submodules("librosa")
hiddenimports += collect_submodules("scipy")
hiddenimports += collect_submodules("scipy.signal")
hiddenimports += collect_submodules("scipy.special")
hiddenimports += collect_submodules("numba")
hiddenimports += collect_submodules("soundfile")
hiddenimports += collect_submodules("audioread")
hiddenimports += collect_submodules("pooch")
hiddenimports += collect_submodules("sklearn.utils._cython_blas")
hiddenimports += [
    "sklearn.neighbors._typedefs",
    "sklearn.neighbors._quad_tree",
    "sklearn.tree",
    "sklearn.tree._utils",
    "lazy_loader",
    "scipy._lib.array_api_compat.numpy.fft",
    "supabase",
    "stripe",
    "ffmpeg",  # ffmpeg-python wrapper, niet de binary
    "watch_folder",
    "analyzer",
    "cutter",
    "uploader",
    "auth",
    "billing",
]

# --------------------------------------------------------------------------- #
# Data files — meegelift in de bundle.
# --------------------------------------------------------------------------- #
datas = []
datas += collect_data_files("librosa")
datas += collect_data_files("soundfile")
datas += collect_data_files("pooch")
datas += [
    ("static", "static"),         # UI + assets
    ("app.py", "."),              # nodig omdat launcher.py via runpy aanroept
    ("brand_kit", "brand_kit"),   # huis-fonts en brand defaults
    ("config.json", "."),
]

# --------------------------------------------------------------------------- #
# Excludes — zware optionele deps die we NIET bundelen.
# --------------------------------------------------------------------------- #
excludes = [
    "torch",
    "demucs",
    "ultralytics",
    "tensorflow",
    "matplotlib",        # librosa heeft het optioneel
    "IPython",
    "jupyter",
    "notebook",
]

a = Analysis(
    ["launcher.py"],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="Clip Live",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,            # UPX breekt vaak met librosa shared libs
    console=False,        # GUI-app: geen Terminal-venster
    disable_windowed_traceback=False,
    target_arch=None,     # universal2 vereist universal Python — apart pad
    codesign_identity=None,  # signing doen we via build_macos.sh
    entitlements_file="entitlements.plist",
    icon="static/icon.icns" if __import__("os").path.exists("static/icon.icns") else None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="Clip Live",
)

app = BUNDLE(
    coll,
    name="Clip Live.app",
    icon="static/icon.icns" if __import__("os").path.exists("static/icon.icns") else None,
    bundle_identifier="com.sjuulstudios.cliplive",
    version="0.1.0",
    info_plist={
        "CFBundleName": "Clip Live",
        "CFBundleDisplayName": "Clip Live",
        "CFBundleShortVersionString": "0.1.0",
        "CFBundleVersion": "0.1.0",
        "NSHighResolutionCapable": "True",
        "LSMinimumSystemVersion": "11.0",
        "NSHumanReadableCopyright": "© 2026 Sjuul Studios",
        # Toegang die het OS aan de user vraagt bij eerste gebruik:
        "NSMicrophoneUsageDescription": "Clip Live needs audio access to analyse your DJ sets.",
        "NSDocumentsFolderUsageDescription": "Clip Live needs access to read your DJ sets.",
        "NSDesktopFolderUsageDescription": "Clip Live needs access to read your DJ sets.",
        "NSDownloadsFolderUsageDescription": "Clip Live needs access to read your DJ sets.",
        "NSAppleEventsUsageDescription": "Clip Live opens your browser to show the app UI.",
    },
)
