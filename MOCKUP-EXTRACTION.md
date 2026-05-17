# Clip Live Redesign — Mockup Extraction

## File Map

| Scene | Name | Line Range | Section ID | Classes |
|-------|------|-----------|-----------|---------|
| 1 | Library | 821–960 | `s1` | `.scene-header`, `.canvas`, `.landing` |
| 2 | Upload | 963–1003 | `s2` | `.scene-header`, `.canvas`, `.upload` |
| 3 | AI Detection | 1006–1064 | `s3` | `.scene-header`, `.canvas`, `.processing` |
| 4 | Clip Picker | 1067–1165 | `s4` | `.scene-header`, `.canvas`, `.clip-pick` |
| 5 | Editor | 1168–1367 | `s5` | `.scene-header`, `.canvas`, `.editor` |
| 6 | Style Room | 1370–1475 | `s6` | `.scene-header`, `.canvas`, `.cap-room` |
| 7 | Export | 1478–1574 | `s7` | `.scene-header`, `.canvas`, `.export` |
| 8 | Ship It | 1577–1623 | `s8` | `.scene-header`, `.canvas`, `.share` |

---

## Design Tokens

### CSS Variables (`:root` block, lines 12–43)

```css
:root{
  --ink-0:#0a0805;       /* near-black, warm */
  --ink-1:#13100b;
  --ink-2:#1c1812;
  --ink-3:#26201a;
  --ink-4:#332b22;
  --line: rgba(255,210,150,0.08);
  --line-2: rgba(255,210,150,0.16);
  --paper:#f6efe2;       /* warm off-white */
  --paper-dim:#cdc3b0;
  --mute:#7a7065;

  --amber:#e8b766;       /* primary accent */
  --amber-2:#f4cf8a;
  --amber-deep:#a8782e;
  --gold:#d4a548;
  --copper:#c2864a;
  --rose:#e0967a;        /* secondary warm */

  --ok:#7fb685;
  --warn:#e8b766;
  --bad:#cf6b58;

  --r-sm:8px; --r-md:14px; --r-lg:20px; --r-xl:28px;
  --shadow-1: 0 1px 0 rgba(255,255,255,0.04) inset, 0 30px 60px -30px rgba(0,0,0,0.7);
  --shadow-2: 0 1px 0 rgba(255,255,255,0.06) inset, 0 60px 120px -40px rgba(0,0,0,0.8);
  --glow: 0 0 0 1px rgba(232,183,102,0.25), 0 20px 60px -20px rgba(232,183,102,0.35);

  --serif: "Fraunces", "Iowan Old Style", Georgia, serif;
  --sans:  "Inter", -apple-system, BlinkMacSystemFont, "Helvetica Neue", Arial, sans-serif;
  --mono:  "JetBrains Mono", ui-monospace, SFMono-Regular, Menlo, monospace;
}
```

### Global Utility Classes

#### Button Styles (lines 102–116)

```css
.btn{
  display:inline-flex;align-items:center;justify-content:center;gap:8px;
  padding:10px 16px;border-radius:12px;font-size:13px;font-weight:500;
  border:1px solid var(--line-2);background:rgba(255,255,255,0.03);color:var(--paper);
  transition:.2s ease;
}
.btn:hover{background:rgba(255,255,255,0.06);border-color:rgba(232,183,102,0.4)}
.btn-primary{
  background:linear-gradient(180deg, var(--amber-2), var(--amber));
  color:#1a1208;border-color:transparent;font-weight:600;
  box-shadow: 0 10px 30px -10px rgba(232,183,102,0.6), inset 0 1px 0 rgba(255,255,255,0.4);
}
.btn-primary:hover{filter:brightness(1.05)}
.btn-ghost{background:transparent}
.btn-icon{width:38px;height:38px;padding:0;border-radius:10px}
```

#### Chip / Badge Styles (lines 330–334, 217–221)

```css
.chip{
  padding:8px 12px;font-size:12px;border-radius:999px;border:1px solid var(--line-2);color:var(--paper-dim);
  background:rgba(0,0,0,0.25);cursor:pointer;
}
.chip.on{background:linear-gradient(180deg, rgba(232,183,102,0.18), rgba(232,183,102,0.08));color:var(--amber-2);border-color:rgba(232,183,102,0.4)}

.badge{
  position:absolute;top:12px;left:12px;font-family:var(--mono);font-size:10px;letter-spacing:.18em;
  padding:5px 9px;border-radius:6px;background:rgba(0,0,0,0.55);border:1px solid var(--line-2);text-transform:uppercase;
  backdrop-filter:blur(8px);color:var(--amber-2);
}
```

#### Sidebar Styles (lines 157–178)

```css
.sidebar{
  border-right:1px solid var(--line);padding:24px 18px;
  background:linear-gradient(180deg, rgba(0,0,0,0.25), rgba(0,0,0,0));
  display:flex;flex-direction:column;gap:6px;
}
.sidebar .label{font-family:var(--mono);font-size:10px;letter-spacing:.25em;color:var(--mute);text-transform:uppercase;margin:18px 10px 6px}
.side-item{
  display:flex;align-items:center;gap:12px;padding:10px 12px;border-radius:10px;color:var(--paper-dim);font-size:13.5px;
  transition:.15s;
}
.side-item:hover{background:rgba(255,255,255,0.04);color:var(--paper)}
.side-item.active{background:linear-gradient(90deg, rgba(232,183,102,0.14), rgba(232,183,102,0));color:var(--amber-2);box-shadow:inset 2px 0 0 var(--amber)}
.side-item .ico{width:18px;height:18px;display:grid;place-items:center;color:currentColor}
```

#### Animated Rings (lines 284–301)

```css
.ring{position:absolute;inset:0;border-radius:50%;border:1px solid rgba(232,183,102,0.18)}
.ring.r2{inset:30px;border-color:rgba(232,183,102,0.25)}
.ring.r3{inset:64px;border-color:rgba(232,183,102,0.32)}
.ring.spin1{animation:spin 22s linear infinite}
.ring.spin2{animation:spin 14s linear infinite reverse}
.ring.spin3{animation:spin 9s linear infinite}
.ring::before{
  content:"";position:absolute;width:8px;height:8px;border-radius:50%;background:var(--amber);
  top:-4px;left:50%;transform:translateX(-50%);box-shadow:0 0 16px var(--amber);
}
.ring.r2::before{background:var(--copper);box-shadow:0 0 14px var(--copper);width:6px;height:6px;top:-3px}
.ring.r3::before{background:var(--amber-2);width:5px;height:5px;top:-2.5px;box-shadow:0 0 10px var(--amber-2)}

@keyframes spin{to{transform:rotate(360deg)}}
```

#### Dashed Dropzone (lines 252–267)

```css
.dropzone{
  border:2px dashed rgba(232,183,102,0.35);border-radius:24px;padding:48px;text-align:center;
  background:
    radial-gradient(80% 80% at 50% 0%, rgba(232,183,102,0.08), transparent 70%),
    rgba(0,0,0,0.3);
  position:relative;overflow:hidden;
}
.dropzone::before{
  content:"";position:absolute;inset:-2px;border-radius:24px;
  background:conic-gradient(from 0deg, rgba(232,183,102,0.3), transparent 30%, rgba(232,183,102,0.3) 60%, transparent 90%);
  -webkit-mask: linear-gradient(#000 0 0) content-box, linear-gradient(#000 0 0);
  -webkit-mask-composite: xor; mask-composite: exclude;
  padding:2px; opacity:.6; pointer-events:none;
  animation: spin 14s linear infinite;
}
```

#### Canvas Container (lines 141–153)

```css
.canvas{
  position:relative;border:1px solid var(--line);border-radius:var(--r-xl);
  background:
    linear-gradient(180deg, rgba(255,255,255,0.02), rgba(0,0,0,0.25)),
    var(--ink-1);
  overflow:hidden;box-shadow:var(--shadow-2);
}
.canvas .scrim{
  position:absolute;inset:0;pointer-events:none;
  background:
    radial-gradient(800px 400px at 90% -10%, rgba(232,183,102,0.10), transparent 60%),
    radial-gradient(700px 400px at 0% 110%, rgba(194,134,74,0.10), transparent 60%);
}
```

#### Scene Header (lines 119–138)

```css
.scene-header{
  display:flex;align-items:flex-end;justify-content:space-between;gap:24px;
  margin:64px 0 18px;
}
.scene-num{
  font-family:var(--mono);font-size:11px;letter-spacing:.3em;color:var(--amber);
  text-transform:uppercase;
}
.scene-title{
  font-family:var(--serif);font-size:42px;line-height:1.05;letter-spacing:-.5px;
  margin:6px 0 10px;font-weight:500;
}
.scene-title em{font-style:italic;color:var(--amber-2);font-weight:400}
.scene-sub{color:var(--paper-dim);font-size:14.5px;max-width:62ch;line-height:1.55}
```

---

## Scene 1: Library

**Line range:** 821–960

### Markup

```html
<div class="scene-header" id="s1">
  <div>
    <div class="scene-num">Scene 01 — Library</div>
    <h2 class="scene-title">A library that <em>sets the tone.</em></h2>
    <p class="scene-sub">Replaces the cluttered list view with a calm editorial dashboard. Warm typography, big media, and the next obvious action always within reach.</p>
  </div>
  <div class="scene-tags">
    <span class="tag">Fraunces · Inter</span>
    <span class="tag">Ink + Amber</span>
    <span class="tag">8pt Grid</span>
  </div>
</div>

<div class="canvas">
  <div class="scrim"></div>
  <div class="landing">
    <!-- SIDEBAR -->
    <aside class="sidebar">
      <div class="label">Workspace</div>
      <div class="side-item active">
        <span class="ico"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><rect x="3" y="3" width="7" height="9" rx="1.5"/><rect x="14" y="3" width="7" height="5" rx="1.5"/><rect x="14" y="12" width="7" height="9" rx="1.5"/><rect x="3" y="16" width="7" height="5" rx="1.5"/></svg></span>
        Library
      </div>
      <div class="side-item">
        <span class="ico"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M3 12c2-6 16-6 18 0M3 12c2 6 16 6 18 0"/><circle cx="12" cy="12" r="2.5"/></svg></span>
        Discover
      </div>
      <div class="side-item">
        <span class="ico"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><rect x="3" y="4" width="18" height="14" rx="2"/><path d="M3 9h18M8 4v14"/></svg></span>
        Watched folders
      </div>
      <div class="side-item">
        <span class="ico"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><circle cx="12" cy="12" r="3"/><path d="M19 12a7 7 0 0 0-.2-1.7l2.1-1.6-2-3.5-2.5 1a7 7 0 0 0-3-1.7L13 2h-2l-.4 2.5a7 7 0 0 0-3 1.7l-2.5-1-2 3.5 2.1 1.6A7 7 0 0 0 5 12c0 .6.1 1.1.2 1.7L3.1 15.3l2 3.5 2.5-1a7 7 0 0 0 3 1.7L11 22h2l.4-2.5a7 7 0 0 0 3-1.7l2.5 1 2-3.5-2.1-1.6c.1-.6.2-1.1.2-1.7Z"/></svg></span>
        Settings
      </div>

      <div class="label">Recent</div>
      <div class="side-item">
        <span class="ico"><svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><circle cx="12" cy="12" r="4"/></svg></span>
        YAP · Creator Series
      </div>
      <div class="side-item">
        <span class="ico"><svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><circle cx="12" cy="12" r="4"/></svg></span>
        Sjuul Studios — Q2
      </div>
      <div class="side-item">
        <span class="ico"><svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><circle cx="12" cy="12" r="4"/></svg></span>
        Tomas livestream
      </div>

      <div class="upgrade-card">
        <span class="pill" style="padding:4px 10px;font-size:10.5px"><span class="dot" style="background:var(--amber);box-shadow:0 0 10px var(--amber)"></span>Studio plan</span>
        <div class="h">Unlock 4K & batch render</div>
        <div class="p">Render up to 12 clips in parallel using Metal acceleration.</div>
        <button class="btn btn-primary" style="width:100%">Upgrade</button>
      </div>
    </aside>

    <!-- MAIN -->
    <main class="main-area">
      <div class="greet">
        <div>
          <h1>Good evening, <em>Sjuul.</em></h1>
          <p>Drop a set anywhere on screen, pick a file from this Mac, or let a watched folder do it for you.</p>
        </div>
        <div class="row">
          <button class="btn"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="7"/><path d="m20 20-4-4"/></svg> Search library</button>
          <button class="btn btn-primary">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><path d="M12 16V4M6 10l6-6 6 6M4 20h16"/></svg>
            Upload set
          </button>
        </div>
      </div>

      <div class="quick-row" style="grid-template-columns:repeat(3,1fr)">
        <div class="quick">
          <div class="ico-lg"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 16V4M6 10l6-6 6 6M4 20h16"/></svg></div>
          <h3>Drop a DJ set</h3>
          <p>Long-form recording, MP4 / MOV / WAV / MP3.</p>
        </div>
        <div class="quick">
          <div class="ico-lg"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 12 12 4l9 8M5 11v9h14v-9"/></svg></div>
          <h3>Choose from this Mac</h3>
          <p>Open the file picker — anywhere on disk.</p>
        </div>
        <div class="quick">
          <div class="ico-lg"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 13h18M5 13 9 5h6l4 8M5 13v6h14v-6"/></svg></div>
          <h3>Watch a folder</h3>
          <p>Drop sets into a Dropbox / Drive / local folder — Clip Live cuts them automatically.</p>
        </div>
      </div>

      <div class="section-h">
        <h2>Recent projects</h2>
        <a href="#">View all →</a>
      </div>
      <div class="projects">
        <div class="proj">
          <div class="thumb th-1">
            <span class="badge">● Edited</span>
            <div class="play"><span><svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><path d="M8 5v14l11-7Z"/></svg></span></div>
          </div>
          <div class="meta">
            <div>
              <div class="t">YAP · Launching a New Product</div>
              <div class="s">12 clips · Edited 2h ago</div>
            </div>
            <button class="mini-btn"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="1"/><circle cx="19" cy="12" r="1"/><circle cx="5" cy="12" r="1"/></svg></button>
          </div>
        </div>
        <div class="proj">
          <div class="thumb th-2">
            <span class="badge">● Processing</span>
            <div class="play"><span><svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><path d="M8 5v14l11-7Z"/></svg></span></div>
          </div>
          <div class="meta">
            <div>
              <div class="t">Tomas — Mindset Reset</div>
              <div class="s">Analyzing · 64% complete</div>
            </div>
            <button class="mini-btn"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="1"/><circle cx="19" cy="12" r="1"/><circle cx="5" cy="12" r="1"/></svg></button>
          </div>
        </div>
        <div class="proj">
          <div class="thumb th-3">
            <span class="badge">● Ready</span>
            <div class="play"><span><svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><path d="M8 5v14l11-7Z"/></svg></span></div>
          </div>
          <div class="meta">
            <div>
              <div class="t">Linkin · Daily Drop #042</div>
              <div class="s">8 clips · Yesterday</div>
            </div>
            <button class="mini-btn"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="1"/><circle cx="19" cy="12" r="1"/><circle cx="5" cy="12" r="1"/></svg></button>
          </div>
        </div>
      </div>
    </main>
  </div>
</div>
```

### Scoped CSS (lines 156–200)

```css
.landing{padding:0;display:grid;grid-template-columns:280px 1fr;min-height:760px}

.main-area{padding:34px 40px 40px;display:flex;flex-direction:column;gap:28px;position:relative}
.greet{display:flex;align-items:flex-end;justify-content:space-between;gap:24px;flex-wrap:wrap}
.greet h1{font-family:var(--serif);font-size:46px;line-height:1.05;margin:0;font-weight:500;letter-spacing:-.5px}
.greet h1 em{font-style:italic;color:var(--amber-2);font-weight:400}
.greet p{margin:8px 0 0;color:var(--paper-dim);max-width:54ch;font-size:14px;line-height:1.6}

.quick-row{display:grid;grid-template-columns:repeat(4,1fr);gap:14px}
.quick{
  padding:18px;border-radius:16px;border:1px solid var(--line-2);
  background:linear-gradient(180deg, rgba(255,255,255,0.03), rgba(0,0,0,0.2));
  display:flex;flex-direction:column;gap:10px;min-height:120px;cursor:pointer;
  transition:.2s;
}
.quick:hover{border-color:rgba(232,183,102,0.4);transform:translateY(-2px)}
.quick .ico-lg{width:32px;height:32px;border-radius:10px;display:grid;place-items:center;background:rgba(232,183,102,0.12);color:var(--amber)}
.quick h3{margin:0;font-family:var(--serif);font-size:18px;font-weight:500}
.quick p{margin:0;font-size:12.5px;color:var(--paper-dim);line-height:1.5}

.section-h{display:flex;align-items:baseline;justify-content:space-between;margin:6px 0 -8px}
.section-h h2{font-family:var(--serif);font-size:22px;font-weight:500;margin:0}
.section-h a{font-size:12.5px;color:var(--amber-2)}

.projects{display:grid;grid-template-columns:repeat(3,1fr);gap:18px}
.proj{
  border:1px solid var(--line);border-radius:16px;overflow:hidden;background:rgba(0,0,0,0.25);
  cursor:pointer;transition:.2s;
}
.proj:hover{border-color:rgba(232,183,102,0.35)}
.proj .thumb{
  aspect-ratio: 16/9;position:relative;
  background:#222;background-size:cover;background-position:center;
}
.proj .thumb::after{
  content:"";position:absolute;inset:0;background:linear-gradient(180deg, rgba(0,0,0,0) 50%, rgba(0,0,0,0.65));
}
.proj .meta{padding:14px 16px;display:flex;align-items:flex-end;justify-content:space-between;gap:10px}
.proj .meta .t{font-family:var(--serif);font-size:16px;font-weight:500}
.proj .meta .s{font-size:11.5px;color:var(--paper-dim);margin-top:4px}
.proj .play{
  position:absolute;inset:0;display:grid;place-items:center;opacity:0;transition:.2s;
}
.proj:hover .play{opacity:1}
.proj .play span{
  width:54px;height:54px;border-radius:50%;background:rgba(0,0,0,0.55);border:1px solid var(--line-2);
  display:grid;place-items:center;color:var(--amber-2);backdrop-filter:blur(10px);
}

/* gradient placeholders for thumbs */
.th-1{background:linear-gradient(135deg,#3a2618,#7a4a23 40%,#c2864a)}
.th-2{background:linear-gradient(135deg,#1f1a14,#4a3c2a 50%,#a8782e)}
.th-3{background:linear-gradient(135deg,#241813,#6a3825 50%,#cf6b58)}
.th-4{background:linear-gradient(135deg,#22150e,#553a25 60%,#d4a548)}
.th-5{background:linear-gradient(135deg,#1a1410,#3a2c1f 50%,#8a623a)}
.th-6{background:linear-gradient(135deg,#1d1610,#5a3e22 50%,#e8b766)}
```

### Scoped JS

None (scene-header is keyed for scroll spy via global JS at end of file).

---

## Scene 2: Upload

**Line range:** 963–1003

### Markup

```html
<div class="scene-header" id="s2">
  <div>
    <div class="scene-num">Scene 02 — Upload</div>
    <h2 class="scene-title">Bring your <em>raw material.</em></h2>
    <p class="scene-sub">A focused upload moment, not a dialog. Big drop target, gentle motion, and a row of importers that feel like editorial buttons rather than form widgets.</p>
  </div>
  <div class="scene-tags">
    <span class="tag">Single Focal Point</span>
    <span class="tag">Animated Border</span>
    <span class="tag">No Modal</span>
  </div>
</div>

<div class="canvas">
  <div class="scrim"></div>
  <div class="upload">
    <div class="upload-copy">
      <h2>Drop in your <em>DJ set.</em><br/>We do the rest.</h2>
      <p>Long-form recordings up to 4 hours. Audio is analyzed on-device — drops, transitions, and bar-aware cuts detected with no upload required.</p>
      <div class="source-grid">
        <div class="source"><span class="ico"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 12 12 4l9 8M5 11v9h14v-9"/></svg></span> Choose from this Mac</div>
        <div class="source"><span class="ico"><svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor"><path d="M6 2 2 8l4 6 4-6-4-6Zm12 0-4 6 4 6 4-6-4-6Zm-6 9-4 6 4 5 4-5-4-6Z"/></svg></span> From Dropbox</div>
        <div class="source"><span class="ico"><svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor"><path d="m12 2 5 9H7l5-9Zm-7 11 5 9-5-9Zm14 0-5 9 10-9H19Zm-12 0h10l-5 9-5-9Z"/></svg></span> From Google Drive</div>
        <div class="source"><span class="ico"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="4" width="18" height="14" rx="2"/><path d="M3 9h18M8 4v14"/></svg></span> Watch a folder</div>
      </div>
      <div style="margin-top:22px;padding:14px 16px;border:1px solid var(--line-2);border-radius:14px;background:rgba(232,183,102,0.06);max-width:440px">
        <div style="font-family:var(--mono);font-size:10.5px;letter-spacing:.2em;color:var(--amber);text-transform:uppercase;margin-bottom:6px">● Watched folder</div>
        <div style="font-size:13.5px;color:var(--paper);line-height:1.5"><b style="color:var(--amber-2)">Dropbox / DJ Sets / Recorded</b> — Clip Live is monitoring. Any new <code style="font-family:var(--mono);font-size:12px;color:var(--paper-dim)">.wav</code> or <code style="font-family:var(--mono);font-size:12px;color:var(--paper-dim)">.mp4</code> dropped here will be cut into shorts automatically.</div>
      </div>
    </div>
    <div class="dropzone">
      <div class="big-ico">
        <svg width="34" height="34" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M12 16V4M6 10l6-6 6 6"/><rect x="3" y="16" width="18" height="5" rx="2"/></svg>
      </div>
      <h3>Drop a set here</h3>
      <p>or <a href="#" style="color:var(--amber-2);text-decoration:underline">browse files</a></p>
      <button class="btn btn-primary">Choose file</button>
      <div class="formats">MP4 · MOV · WAV · MP3 · FLAC — up to 8GB</div>
    </div>
  </div>
</div>
```

### Scoped CSS (lines 239–276)

```css
.upload{padding:60px 60px 70px;min-height:680px;display:grid;grid-template-columns:1fr 1fr;gap:60px;align-items:center}
.upload-copy h2{font-family:var(--serif);font-size:50px;line-height:1.05;font-weight:500;margin:0 0 18px;letter-spacing:-.6px}
.upload-copy h2 em{font-style:italic;color:var(--amber-2);font-weight:400}
.upload-copy p{color:var(--paper-dim);font-size:15.5px;line-height:1.65;max-width:46ch;margin:0 0 24px}
.source-grid{display:grid;grid-template-columns:repeat(2,1fr);gap:10px;max-width:440px}
.source{
  display:flex;align-items:center;gap:10px;padding:12px 14px;border-radius:12px;border:1px solid var(--line-2);
  background:rgba(255,255,255,0.02);font-size:13px;color:var(--paper-dim);cursor:pointer;transition:.2s;
}
.source:hover{border-color:rgba(232,183,102,0.4);color:var(--paper)}
.source .ico{width:22px;height:22px;display:grid;place-items:center;color:var(--amber-2)}

.dropzone{
  border:2px dashed rgba(232,183,102,0.35);border-radius:24px;padding:48px;text-align:center;
  background:
    radial-gradient(80% 80% at 50% 0%, rgba(232,183,102,0.08), transparent 70%),
    rgba(0,0,0,0.3);
  position:relative;overflow:hidden;
}
.dropzone::before{
  content:"";position:absolute;inset:-2px;border-radius:24px;
  background:conic-gradient(from 0deg, rgba(232,183,102,0.3), transparent 30%, rgba(232,183,102,0.3) 60%, transparent 90%);
  -webkit-mask: linear-gradient(#000 0 0) content-box, linear-gradient(#000 0 0);
  -webkit-mask-composite: xor; mask-composite: exclude;
  padding:2px; opacity:.6; pointer-events:none;
  animation: spin 14s linear infinite;
}
.dropzone .big-ico{
  width:78px;height:78px;border-radius:24px;margin:0 auto 18px;display:grid;place-items:center;
  background:linear-gradient(180deg, rgba(232,183,102,0.18), rgba(232,183,102,0.04));
  color:var(--amber-2);box-shadow:inset 0 0 0 1px rgba(232,183,102,0.35);
}
.dropzone h3{font-family:var(--serif);font-size:26px;margin:0 0 6px;font-weight:500}
.dropzone p{color:var(--paper-dim);font-size:13.5px;margin:0 0 18px}
.dropzone .formats{font-family:var(--mono);font-size:10.5px;letter-spacing:.2em;color:var(--mute);text-transform:uppercase;margin-top:18px}
```

### Scoped JS

None.

---

## Scene 3: AI Detection

**Line range:** 1006–1064

### Markup

```html
<div class="scene-header" id="s3">
  <div>
    <div class="scene-num">Scene 03 — AI Detection</div>
    <h2 class="scene-title">A processor that <em>hears the drops.</em></h2>
    <p class="scene-sub">Instead of a flat progress bar, three concentric rings track waveform analysis, drop &amp; transition detection, and bar-aware clip composition. Each step is its own line — you can see exactly where Metal and Demucs are being put to work.</p>
  </div>
  <div class="scene-tags">
    <span class="tag">Bar-aware cuts</span>
    <span class="tag">Drop detection</span>
    <span class="tag">GPU usage live</span>
  </div>
</div>

<div class="canvas">
  <div class="scrim"></div>
  <div class="processing">
    <div class="proc-visual">
      <div class="ring spin1"></div>
      <div class="ring r2 spin2"></div>
      <div class="ring r3 spin3"></div>
      <div class="core">
        <div>
          <div class="pct">62<em>%</em></div>
          <div class="lbl">Analyzing · ~38s left</div>
        </div>
      </div>
    </div>
    <div class="proc-list">
      <h2>Listening for the <em>moments.</em></h2>
      <p class="lead">Demucs separates the stems on Apple Metal, then bar-aware analysis locks every cut to the downbeat. Drops and transitions are scored, ranked, and composed into vertical clips automatically.</p>

      <div class="step done">
        <div class="num">✓</div>
        <div class="t">Decode &amp; load audio<small>FFmpeg · VideoToolbox</small></div>
        <div class="meta">9s</div>
      </div>
      <div class="step done">
        <div class="num">✓</div>
        <div class="t">Beat &amp; bar grid<small>librosa · onset + tempogram</small></div>
        <div class="meta">14s</div>
      </div>
      <div class="step now">
        <div class="num">3</div>
        <div class="t">Stem separation &amp; drop detection<small>Demucs htdemucs · Metal</small></div>
        <div class="meta">running…</div>
      </div>
      <div class="step">
        <div class="num">4</div>
        <div class="t">Score transitions &amp; energy peaks<small>RMS + spectral flux ranking</small></div>
        <div class="meta">queued</div>
      </div>
      <div class="step">
        <div class="num">5</div>
        <div class="t">Compose vertical clips on the bar<small>9:16 framing · clean cuts</small></div>
        <div class="meta">queued</div>
      </div>
    </div>
  </div>
</div>
```

### Scoped CSS (lines 277–321)

```css
.processing{padding:60px;min-height:660px;display:grid;grid-template-columns:1.1fr 1fr;gap:60px;align-items:center}
.proc-visual{
  aspect-ratio:1;border-radius:50%;position:relative;margin:auto;width:min(100%,460px);
  background:
    radial-gradient(circle at 50% 50%, rgba(232,183,102,0.18), transparent 60%);
}
.core{
  position:absolute;inset:0;display:grid;place-items:center;text-align:center;
}
.core .pct{font-family:var(--serif);font-size:64px;font-weight:500;letter-spacing:-1px}
.core .pct em{font-style:italic;color:var(--amber-2);font-weight:400}
.core .lbl{font-family:var(--mono);font-size:11px;letter-spacing:.3em;color:var(--paper-dim);text-transform:uppercase;margin-top:6px}

.proc-list{display:flex;flex-direction:column;gap:14px}
.proc-list h2{font-family:var(--serif);font-size:38px;font-weight:500;margin:0 0 6px;letter-spacing:-.4px}
.proc-list h2 em{font-style:italic;color:var(--amber-2);font-weight:400}
.proc-list .lead{color:var(--paper-dim);margin:0 0 10px;font-size:14.5px;line-height:1.6;max-width:46ch}
.step{
  display:flex;align-items:center;gap:14px;padding:14px 16px;border-radius:14px;
  border:1px solid var(--line);background:rgba(0,0,0,0.25);
}
.step .num{
  width:28px;height:28px;border-radius:8px;display:grid;place-items:center;
  font-family:var(--mono);font-size:12px;color:var(--paper-dim);
  background:rgba(255,255,255,0.04);border:1px solid var(--line-2);
}
.step.done .num{background:rgba(127,182,133,0.15);color:var(--ok);border-color:rgba(127,182,133,0.3)}
.step.now{border-color:rgba(232,183,102,0.4);background:linear-gradient(90deg, rgba(232,183,102,0.10), transparent 70%)}
.step.now .num{background:rgba(232,183,102,0.2);color:var(--amber-2);border-color:rgba(232,183,102,0.4)}
.step .t{flex:1;font-size:13.5px;color:var(--paper)}
.step .t small{display:block;color:var(--paper-dim);font-size:11.5px;margin-top:2px}
.step .meta{font-family:var(--mono);font-size:11px;color:var(--mute)}
```

### Scoped JS

None.

---

## Scene 4: Clip Picker

**Line range:** 1067–1165

### Markup

```html
<div class="scene-header" id="s4">
  <div>
    <div class="scene-num">Scene 04 — Clip Picker</div>
    <h2 class="scene-title">Twelve clips. <em>Pick the keepers.</em></h2>
    <p class="scene-sub">Vertical poster cards with auto-generated captions baked into the thumbnail, a virality score in the corner, and filters tuned for short-form work.</p>
  </div>
  <div class="scene-tags">
    <span class="tag">Vertical 9:16</span>
    <span class="tag">Hook score</span>
    <span class="tag">Smart filters</span>
  </div>
</div>

<div class="canvas">
  <div class="scrim"></div>
  <div class="clip-pick">
    <div class="pick-head">
      <div>
        <h2>12 clips cut from <em>Boiler Room — Live Set, April</em></h2>
        <p>Sorted by energy score · 58 min set · Last analyzed just now</p>
      </div>
      <div class="filter-row">
        <button class="chip on">All 12</button>
        <button class="chip">Drops (8)</button>
        <button class="chip">Transitions</button>
        <button class="chip">Under 30s</button>
        <button class="chip">Crowd reaction</button>
        <button class="btn btn-primary" style="margin-left:8px"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M5 12h14M13 5l7 7-7 7"/></svg> Edit selected</button>
      </div>
    </div>

    <div class="clip-grid">
      <div class="clip">
        <div class="ph th-1">
          <div class="duration">0:34</div>
          <div class="score">★ 94</div>
          <div class="cap">"I'm <b>time-rich</b> — I have to make something on Linkin <b>every day</b>."</div>
        </div>
        <div class="info"><div class="l">Tanya · 02:14</div><div class="r"><button class="mini-btn">★</button><button class="mini-btn">↗</button></div></div>
      </div>
      <div class="clip">
        <div class="ph th-2">
          <div class="duration">0:48</div>
          <div class="score">★ 91</div>
          <div class="cap">The first thing I do is <b>figure out what type of creator</b> I am.</div>
        </div>
        <div class="info"><div class="l">Tanya · 04:02</div><div class="r"><button class="mini-btn">★</button><button class="mini-btn">↗</button></div></div>
      </div>
      <div class="clip">
        <div class="ph th-3">
          <div class="duration">0:27</div>
          <div class="score">★ 88</div>
          <div class="cap">Three <b>cold-start</b> tactics that got us to a million.</div>
        </div>
        <div class="info"><div class="l">Tanya · 11:18</div><div class="r"><button class="mini-btn">★</button><button class="mini-btn">↗</button></div></div>
      </div>
      <div class="clip">
        <div class="ph th-4">
          <div class="duration">0:55</div>
          <div class="score">★ 85</div>
          <div class="cap">Why <b>posting daily</b> beats posting perfectly.</div>
        </div>
        <div class="info"><div class="l">Tomas · 18:32</div><div class="r"><button class="mini-btn">★</button><button class="mini-btn">↗</button></div></div>
      </div>
      <div class="clip">
        <div class="ph th-5">
          <div class="duration">0:31</div>
          <div class="score">★ 82</div>
          <div class="cap">The mistake <b>every new podcaster</b> makes.</div>
        </div>
        <div class="info"><div class="l">James · 22:04</div><div class="r"><button class="mini-btn">★</button><button class="mini-btn">↗</button></div></div>
      </div>
      <div class="clip">
        <div class="ph th-6">
          <div class="duration">0:42</div>
          <div class="score">★ 80</div>
          <div class="cap">My <b>$0 launch</b> playbook for episode one.</div>
        </div>
        <div class="info"><div class="l">Tanya · 27:51</div><div class="r"><button class="mini-btn">★</button><button class="mini-btn">↗</button></div></div>
      </div>
      <div class="clip">
        <div class="ph th-2">
          <div class="duration">0:39</div>
          <div class="score">★ 78</div>
          <div class="cap">How to find <b>your first 1,000</b> listeners.</div>
        </div>
        <div class="info"><div class="l">Tomas · 31:20</div><div class="r"><button class="mini-btn">★</button><button class="mini-btn">↗</button></div></div>
      </div>
      <div class="clip">
        <div class="ph th-1">
          <div class="duration">0:29</div>
          <div class="score">★ 75</div>
          <div class="cap">"It's not about <b>being early</b>, it's about being there."</div>
        </div>
        <div class="info"><div class="l">James · 38:08</div><div class="r"><button class="mini-btn">★</button><button class="mini-btn">↗</button></div></div>
      </div>
    </div>
  </div>
</div>
```

### Scoped CSS (lines 323–365)

```css
.clip-pick{padding:34px 40px 40px;display:flex;flex-direction:column;gap:22px;min-height:760px}
.pick-head{display:flex;align-items:flex-end;justify-content:space-between;gap:16px;flex-wrap:wrap}
.pick-head h2{font-family:var(--serif);font-size:34px;font-weight:500;margin:0;letter-spacing:-.3px}
.pick-head h2 em{font-style:italic;color:var(--amber-2);font-weight:400}
.pick-head p{color:var(--paper-dim);margin:6px 0 0;font-size:13.5px}
.filter-row{display:flex;align-items:center;gap:8px;flex-wrap:wrap}

.clip-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:16px}
.clip{
  border:1px solid var(--line);border-radius:18px;overflow:hidden;background:rgba(0,0,0,0.3);
  display:flex;flex-direction:column;cursor:pointer;transition:.2s;position:relative;
}
.clip:hover{border-color:rgba(232,183,102,0.4);transform:translateY(-3px)}
.clip .ph{aspect-ratio:9/16;position:relative;overflow:hidden}
.clip .ph::after{content:"";position:absolute;inset:0;background:linear-gradient(180deg,transparent 40%,rgba(0,0,0,.85))}
.clip .score{
  position:absolute;top:10px;right:10px;display:flex;align-items:center;gap:6px;
  padding:6px 10px;border-radius:999px;background:rgba(0,0,0,0.6);border:1px solid var(--line-2);backdrop-filter:blur(8px);
  font-family:var(--mono);font-size:11px;color:var(--amber-2);z-index:2;
}
.clip .duration{
  position:absolute;top:10px;left:10px;font-family:var(--mono);font-size:10.5px;
  padding:5px 8px;border-radius:6px;background:rgba(0,0,0,0.6);color:var(--paper);z-index:2;
}
.clip .cap{
  position:absolute;left:14px;right:14px;bottom:14px;z-index:2;
  font-family:var(--serif);font-weight:500;font-size:15px;line-height:1.25;
}
.clip .cap b{color:var(--amber-2);font-weight:600}
.clip .info{padding:12px 14px;display:flex;align-items:center;justify-content:space-between;gap:8px;border-top:1px solid var(--line)}
.clip .info .l{font-size:11.5px;color:var(--paper-dim)}
.clip .info .r{display:flex;gap:6px}
.mini-btn{
  width:30px;height:30px;border-radius:8px;display:grid;place-items:center;color:var(--paper-dim);
  border:1px solid var(--line-2);background:rgba(255,255,255,0.02);
}
.mini-btn:hover{color:var(--amber-2);border-color:rgba(232,183,102,0.4)}
```

### Scoped JS

None.

---

## Scene 5: Editor

**Line range:** 1168–1367

### Markup (excerpt — full 200+ lines)

```html
<div class="scene-header" id="s5">
  <div>
    <div class="scene-num">Scene 05 — Editor</div>
    <h2 class="scene-title">An editor that breathes — <em>and listens.</em></h2>
    <p class="scene-sub">Three columns, none of them shouting. Cue-points and clip queue on the left, the clip itself in a calm centre stage, and tools tucked into a single-icon rail. Timeline reads like a music score, not a spreadsheet.</p>
  </div>
  <div class="scene-tags">
    <span class="tag">Bar-aware trim</span>
    <span class="tag">Multi-track</span>
    <span class="tag">GPU thumbnails</span>
    <span class="tag">9:16 / 1:1 / 16:9</span>
  </div>
</div>

<div class="canvas">
  <div class="scrim"></div>
  <div class="editor">
    <div class="ed-top">
      <div class="crumbs">
        <span>Boiler Room — Live Set, April</span>
        <span style="color:var(--mute)">›</span>
        <b>Clip 01 · Drop @ 12:34</b>
        <span class="pill" style="margin-left:10px;font-size:11px">● Autosaved 2s ago</span>
      </div>
      <div class="ed-tools">
        <button class="t on">Edit</button>
        <button class="t">Style</button>
        <button class="t">Brand</button>
        <button class="t" style="border-color:rgba(232,183,102,0.4);color:var(--amber-2)">Export →</button>
      </div>
    </div>

    <div class="ed-body">
      <!-- LEFT: CLIP QUEUE / CUE POINTS -->
      <div class="ed-left">
        <div class="panel-h">
          <div class="ti">Cue points</div>
          <div class="ct">12 detected · 124 BPM</div>
        </div>
        <div class="transcript">
          <div class="cue-list">
            <div class="cue active">
              <span class="cue-time">12:34</span>
              <div class="cue-body">
                <div class="cue-title">Drop · ID #1</div>
                <div class="cue-meta">Energy ★ 94 · 8 bars in</div>
              </div>
              <span class="cue-tag">DROP</span>
            </div>
            <div class="cue">
              <span class="cue-time">17:02</span>
              <div class="cue-body">
                <div class="cue-title">Transition</div>
                <div class="cue-meta">Filter sweep · 4 bars</div>
              </div>
              <span class="cue-tag tx">TRANS</span>
            </div>
            <div class="cue">
              <span class="cue-time">22:48</span>
              <div class="cue-body">
                <div class="cue-title">Drop · ID #2</div>
                <div class="cue-meta">Energy ★ 91 · crowd peak</div>
              </div>
              <span class="cue-tag">DROP</span>
            </div>
            <div class="cue">
              <span class="cue-time">28:15</span>
              <div class="cue-body">
                <div class="cue-title">Build-up</div>
                <div class="cue-meta">16 bars · snare roll</div>
              </div>
              <span class="cue-tag bu">BUILD</span>
            </div>
            <div class="cue">
              <span class="cue-time">31:09</span>
              <div class="cue-body">
                <div class="cue-title">Drop · ID #3</div>
                <div class="cue-meta">Energy ★ 88 · bass-heavy</div>
              </div>
              <span class="cue-tag">DROP</span>
            </div>
            <div class="cue">
              <span class="cue-time">37:22</span>
              <div class="cue-body">
                <div class="cue-title">Vocal hook</div>
                <div class="cue-meta">Acapella stem · 8 bars</div>
              </div>
              <span class="cue-tag tx">HOOK</span>
            </div>
            <div class="cue">
              <span class="cue-time">42:51</span>
              <div class="cue-body">
                <div class="cue-title">Drop · ID #4</div>
                <div class="cue-meta">Energy ★ 85 · double-time</div>
              </div>
              <span class="cue-tag">DROP</span>
            </div>
          </div>
        </div>
      </div>

      <!-- CENTER: PREVIEW -->
      <div class="ed-canvas">
        <div class="ratio-rail">
          <button class="on">9:16</button>
          <button>1:1</button>
          <button>16:9</button>
          <button>4:5</button>
        </div>
        <div class="preview-stage">
          <div class="stage-tag">● Live preview</div>
          <div class="stage-cap">When the <b>drop</b> hits at <em>Boiler Room</em> 🔥</div>
        </div>
        <div class="stage-controls">
          <button title="back"><svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><path d="M19 5v14l-11-7Z"/></svg></button>
          <button class="play" title="play"><svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><path d="M8 5v14l11-7Z"/></svg></button>
          <button title="fwd"><svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><path d="M5 5v14l11-7Z"/></svg></button>
          <span class="stage-time">00:02 / 00:34</span>
        </div>
      </div>

      <!-- RIGHT: TOOL RAIL -->
      <div class="ed-right">
        <button class="tool-btn on">
          <div class="ico"><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M4 6h16M4 12h16M4 18h10"/></svg></div>
          Text
        </button>
        <button class="tool-btn">
          <div class="ico"><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><circle cx="6" cy="6" r="3"/><circle cx="6" cy="18" r="3"/><path d="m20 4-12 14M14 11l6 9"/></svg></div>
          Trim
        </button>
        <button class="tool-btn">
          <div class="ico"><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M12 16V4M6 10l6-6 6 6"/><rect x="3" y="16" width="18" height="5" rx="2"/></svg></div>
          Upload
        </button>
        <button class="tool-btn">
          <div class="ico"><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M9 18V5l12-2v13"/><circle cx="6" cy="18" r="3"/><circle cx="18" cy="16" r="3"/></svg></div>
          Music
        </button>
      </div>
    </div>

    <!-- TIMELINE -->
    <div class="timeline">
      <div class="tl-toolbar">
        <div class="l">
          <button class="btn btn-icon" title="split"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 3v18M5 7l7 5-7 5M19 7l-7 5 7 5"/></svg></button>
          <button class="btn btn-icon" title="trim"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="6" cy="6" r="3"/><circle cx="6" cy="18" r="3"/><path d="m20 4-12 14M14 11l6 9"/></svg></button>
          <button class="btn btn-icon" title="delete"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 7h16M9 7V4h6v3M6 7l1 13h10l1-13"/></svg></button>
          <button class="btn btn-icon" title="undo"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 14 4 9l5-5"/><path d="M4 9h11a5 5 0 0 1 0 10h-2"/></svg></button>
        </div>
        <div class="time"><b>00:02.00</b> / 00:58.03 · 60 fps</div>
        <div class="l">
          <button class="btn btn-icon" title="zoom out"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M5 12h14"/></svg></button>
          <div style="width:120px;height:4px;border-radius:999px;background:rgba(255,255,255,0.08);position:relative">
            <div style="position:absolute;left:60%;top:-6px;width:14px;height:14px;border-radius:50%;background:linear-gradient(180deg,var(--amber-2),var(--amber));box-shadow:0 0 0 3px rgba(232,183,102,0.18)"></div>
          </div>
          <button class="btn btn-icon" title="zoom in"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M5 12h14M12 5v14"/></svg></button>
        </div>
      </div>

      <div class="ruler"></div>
      <div class="ruler-labels">
        <span>0</span><span>5</span><span>10</span><span>15</span><span>20</span><span>25</span><span>30</span><span>35</span><span>40</span><span>45</span><span>50</span><span>55</span><span>60</span>
      </div>

      <div class="tracks">
        <div class="playhead" style="left:18%"></div>

        <div class="track">
          <span class="label">Video · 9:16</span>
          <div class="clip-block" style="left:1%;right:1%"><span class="lbl">YAP · creator series · Tanya</span><div class="frames"></div></div>
        </div>

        <div class="track caption-track">
          <span class="label">Captions</span>
          <div class="cap-piece" style="left:2%;width:18%">DROP INCOMING</div>
          <div class="cap-piece" style="left:21%;width:14%">3 · 2 · 1</div>
          <div class="cap-piece" style="left:36%;width:22%">@boilerroom · LIVE</div>
          <div class="cap-piece" style="left:60%;width:18%">TURN IT UP</div>
          <div class="cap-piece" style="left:80%;width:18%">FULL SET → LINK</div>
        </div>

        <div class="track broll-track">
          <span class="label">Cue markers</span>
          <div class="b-piece" style="left:18%;width:6%;background:linear-gradient(180deg,rgba(232,183,102,0.45),rgba(168,120,46,0.4));border-color:rgba(232,183,102,0.55);color:#1a1208">🔥 DROP</div>
          <div class="b-piece" style="left:42%;width:10%;background:linear-gradient(180deg,rgba(224,150,122,0.35),rgba(194,134,74,0.25));border-color:rgba(224,150,122,0.5)">↻ TRANSITION</div>
          <div class="b-piece" style="left:74%;width:8%;background:linear-gradient(180deg,rgba(232,183,102,0.45),rgba(168,120,46,0.4));border-color:rgba(232,183,102,0.55);color:#1a1208">🔥 DROP</div>
        </div>

        <div class="track audio-track">
          <span class="label">Music</span>
          <div class="wave">
            <script>document.write(Array(140).fill(0).map((_,i)=>`<i style="height:${20+Math.abs(Math.sin(i/3))*22+Math.random()*8}px"></i>`).join(''))</script>
          </div>
        </div>
      </div>
    </div>
  </div>
</div>
```

### Scoped CSS (lines 367–584)

```css
.editor{padding:0;display:grid;grid-template-rows:auto 1fr auto;min-height:820px}
.ed-top{
  display:flex;align-items:center;justify-content:space-between;gap:14px;
  padding:14px 20px;border-bottom:1px solid var(--line);
  background:linear-gradient(180deg, rgba(0,0,0,0.35), rgba(0,0,0,0));
}
.ed-top .crumbs{display:flex;align-items:center;gap:10px;font-size:13px;color:var(--paper-dim)}
.ed-top .crumbs b{color:var(--paper);font-weight:500}
.ed-tools{display:flex;gap:6px}
.ed-tools .t{
  padding:8px 12px;font-size:12.5px;border-radius:10px;border:1px solid var(--line-2);
  color:var(--paper-dim);background:rgba(0,0,0,0.25);cursor:pointer;
}
.ed-tools .t.on{color:var(--amber-2);border-color:rgba(232,183,102,0.4);background:rgba(232,183,102,0.08)}

.ed-body{display:grid;grid-template-columns:340px 1fr 88px;gap:0;min-height:520px}
.ed-left{
  border-right:1px solid var(--line);padding:18px;overflow:hidden;
  background:linear-gradient(180deg, rgba(0,0,0,0.2), rgba(0,0,0,0));
  display:flex;flex-direction:column;gap:14px;
}
.panel-h{display:flex;align-items:center;justify-content:space-between;gap:10px}
.panel-h .ti{font-family:var(--serif);font-size:18px;font-weight:500}
.panel-h .ct{font-family:var(--mono);font-size:11px;color:var(--mute)}

.transcript{
  flex:1;overflow:auto;padding-right:6px;font-size:14.5px;line-height:1.7;color:var(--paper-dim);
}
.transcript p{margin:0 0 12px}
.transcript .speaker{
  font-family:var(--mono);font-size:10.5px;letter-spacing:.18em;color:var(--amber);
  text-transform:uppercase;margin-bottom:4px;display:block;
}
.transcript mark{
  background:linear-gradient(180deg, rgba(232,183,102,0.18), rgba(232,183,102,0.08));
  color:var(--paper);padding:2px 4px;border-radius:4px;border-bottom:1px solid rgba(232,183,102,0.4);
}
.transcript .keep{
  background:rgba(127,182,133,0.10);color:var(--paper);padding:1px 3px;border-radius:3px;
}
.transcript .cut{
  color:var(--mute);text-decoration:line-through;text-decoration-color:rgba(207,107,88,0.5);
}

/* cue-points list */
.cue-list{display:flex;flex-direction:column;gap:6px;padding-right:4px}
.cue{
  display:flex;align-items:center;gap:12px;padding:10px 12px;border-radius:10px;
  border:1px solid var(--line);background:rgba(255,255,255,0.02);cursor:pointer;transition:.15s;
}
.cue:hover{border-color:rgba(232,183,102,0.35);background:rgba(255,255,255,0.04)}
.cue.active{
  border-color:rgba(232,183,102,0.5);
  background:linear-gradient(90deg, rgba(232,183,102,0.14), rgba(232,183,102,0));
  box-shadow:inset 2px 0 0 var(--amber);
}
.cue-time{
  font-family:var(--mono);font-size:11px;color:var(--paper-dim);letter-spacing:.05em;
  width:42px;flex:none;
}
.cue.active .cue-time{color:var(--amber-2)}
.cue-body{flex:1;min-width:0}
.cue-title{font-family:var(--serif);font-size:14px;font-weight:500;color:var(--paper);line-height:1.2}
.cue-meta{font-size:11px;color:var(--paper-dim);margin-top:2px}
.cue-tag{
  font-family:var(--mono);font-size:9.5px;letter-spacing:.18em;text-transform:uppercase;
  padding:4px 7px;border-radius:5px;background:rgba(232,183,102,0.16);color:var(--amber-2);
  border:1px solid rgba(232,183,102,0.3);
}
.cue-tag.tx{background:rgba(224,150,122,0.16);color:var(--rose);border-color:rgba(224,150,122,0.3)}
.cue-tag.bu{background:rgba(127,182,133,0.16);color:var(--ok);border-color:rgba(127,182,133,0.3)}

.ed-canvas{
  position:relative;display:grid;place-items:center;padding:30px;
  background:
    radial-gradient(800px 500px at 50% 30%, rgba(232,183,102,0.06), transparent 60%),
    var(--ink-1);
}
.preview-stage{
  position:relative;width:min(100%, 320px);aspect-ratio:9/16;border-radius:18px;overflow:hidden;
  background:linear-gradient(135deg,#3b2716,#7a4a23 50%,#c2864a);
  box-shadow: 0 60px 120px -30px rgba(0,0,0,0.7), 0 0 0 1px rgba(255,255,255,0.05);
}
.preview-stage::after{
  content:"";position:absolute;inset:0;
  background:radial-gradient(circle at 60% 60%, rgba(0,0,0,0) 30%, rgba(0,0,0,0.55));
}
.stage-cap{
  position:absolute;left:14px;right:14px;bottom:24px;text-align:center;z-index:3;
  font-family:var(--serif);font-weight:600;font-size:24px;line-height:1.15;letter-spacing:-.3px;
  text-shadow: 0 4px 12px rgba(0,0,0,0.7);
}
.stage-cap b{color:var(--amber-2)}
.stage-cap em{font-style:italic;color:var(--rose)}
.stage-tag{
  position:absolute;top:14px;left:14px;font-family:var(--mono);font-size:10px;letter-spacing:.2em;
  padding:5px 9px;border-radius:6px;background:rgba(0,0,0,0.6);border:1px solid var(--line-2);text-transform:uppercase;
  z-index:3;color:var(--amber-2);
}
.stage-controls{
  position:absolute;left:50%;bottom:-30px;transform:translateX(-50%);display:flex;gap:8px;align-items:center;
  padding:8px 12px;border-radius:999px;background:rgba(10,8,5,0.85);border:1px solid var(--line-2);backdrop-filter:blur(12px);
  z-index:5;
}
.stage-controls button{
  width:36px;height:36px;border-radius:50%;display:grid;place-items:center;color:var(--paper);
}
.stage-controls .play{
  background:linear-gradient(180deg,var(--amber-2),var(--amber));color:#1a1208;
  box-shadow:0 6px 20px -4px rgba(232,183,102,0.6);
}
.stage-time{font-family:var(--mono);font-size:11px;color:var(--paper-dim);padding:0 8px}

.ratio-rail{
  position:absolute;top:50%;right:18px;transform:translateY(-50%);display:flex;flex-direction:column;gap:6px;
}
.ratio-rail button{
  padding:8px 10px;font-size:11px;border-radius:8px;border:1px solid var(--line-2);background:rgba(0,0,0,0.5);
  color:var(--paper-dim);font-family:var(--mono);
}
.ratio-rail button.on{color:var(--amber-2);border-color:rgba(232,183,102,0.4);background:rgba(232,183,102,0.1)}

.ed-right{
  border-left:1px solid var(--line);padding:14px 6px;
  background:linear-gradient(180deg, rgba(0,0,0,0.2), rgba(0,0,0,0));
  display:flex;flex-direction:column;gap:6px;align-items:center;
}
.tool-btn{
  width:64px;padding:14px 6px;border-radius:14px;text-align:center;color:var(--paper-dim);font-size:11px;
  border:1px solid transparent;cursor:pointer;transition:.15s;
}
.tool-btn:hover{background:rgba(255,255,255,0.04);color:var(--paper)}
.tool-btn.on{
  color:var(--amber-2);background:linear-gradient(180deg, rgba(232,183,102,0.14), rgba(232,183,102,0.04));
  border-color:rgba(232,183,102,0.3);
}
.tool-btn .ico{width:22px;height:22px;margin:0 auto 6px;display:grid;place-items:center}

/* TIMELINE */
.timeline{
  border-top:1px solid var(--line);padding:14px 20px 18px;
  background:linear-gradient(180deg, rgba(0,0,0,0.2), rgba(0,0,0,0.45));
}
.tl-toolbar{display:flex;align-items:center;justify-content:space-between;gap:14px;margin-bottom:10px}
.tl-toolbar .l{display:flex;align-items:center;gap:8px}
.tl-toolbar .time{font-family:var(--mono);font-size:12px;color:var(--paper-dim)}
.tl-toolbar .time b{color:var(--amber-2)}
.ruler{
  height:16px;position:relative;border-radius:6px;background:rgba(255,255,255,0.02);overflow:hidden;
  margin-bottom:8px;
}
.ruler::before,.ruler::after{content:"";position:absolute;inset:0}
.ruler::before{
  background-image:
    repeating-linear-gradient(90deg, rgba(255,255,255,0.06) 0 1px, transparent 1px 40px);
}
.ruler::after{
  background-image:
    repeating-linear-gradient(90deg, rgba(232,183,102,0.18) 0 1px, transparent 1px 200px);
}
.ruler-labels{display:flex;justify-content:space-between;font-family:var(--mono);font-size:10px;color:var(--mute);margin-bottom:8px}

.tracks{display:flex;flex-direction:column;gap:8px;position:relative}
.track{height:54px;border-radius:10px;background:rgba(255,255,255,0.025);position:relative;border:1px solid var(--line);overflow:hidden}
.track .label{
  position:absolute;left:8px;top:8px;font-family:var(--mono);font-size:10px;letter-spacing:.18em;color:var(--mute);text-transform:uppercase;z-index:3;
}
.clip-block{
  position:absolute;top:6px;bottom:6px;border-radius:8px;
  background:linear-gradient(180deg, rgba(232,183,102,0.45), rgba(168,120,46,0.5));
  border:1px solid rgba(232,183,102,0.55);
  box-shadow: inset 0 0 0 1px rgba(255,255,255,0.1);
  overflow:hidden;
}
.clip-block .frames{
  position:absolute;inset:0;
  background:
    linear-gradient(90deg, rgba(0,0,0,0.15) 1px, transparent 1px) 0 0/40px 100%,
    linear-gradient(90deg, #5a3a1d, #8a5a2c, #b27a3e, #8a5a2c, #5a3a1d);
  opacity:.85;
}
.clip-block .lbl{
  position:absolute;left:8px;top:6px;font-family:var(--mono);font-size:10.5px;color:#1a1208;font-weight:600;z-index:2;
}

.audio-track{
  position:relative;
}
.wave{
  position:absolute;inset:8px 4px;display:flex;align-items:center;gap:1.5px;
}
.wave i{
  flex:1;background:linear-gradient(180deg, var(--amber), var(--copper));
  border-radius:1px;opacity:.85;display:block;
}

.caption-track .cap-piece{
  position:absolute;top:8px;bottom:8px;border-radius:6px;
  background:linear-gradient(180deg, rgba(224,150,122,0.35), rgba(194,134,74,0.25));
  border:1px solid rgba(224,150,122,0.5);
  display:flex;align-items:center;padding:0 8px;font-size:11px;font-family:var(--mono);color:var(--paper);
  overflow:hidden;white-space:nowrap;text-overflow:ellipsis;
}
.broll-track .b-piece{
  position:absolute;top:8px;bottom:8px;border-radius:6px;
  background:linear-gradient(180deg, rgba(127,182,133,0.30), rgba(70,120,80,0.25));
  border:1px solid rgba(127,182,133,0.45);
  display:flex;align-items:center;padding:0 8px;font-size:11px;font-family:var(--mono);color:var(--paper);
}
.playhead{
  position:absolute;top:-4px;bottom:-4px;width:1.5px;background:var(--amber);z-index:5;
  box-shadow: 0 0 16px rgba(232,183,102,0.6);
}
.playhead::before{
  content:"";position:absolute;top:-4px;left:-6px;width:14px;height:8px;
  background:var(--amber);clip-path:polygon(0 0,100% 0,50% 100%);
}
```

### Scoped JS (inline in timeline waveform, line 1361)

```javascript
<script>
  document.write(Array(140).fill(0).map((_,i)=>
    `<i style="height:${20+Math.abs(Math.sin(i/3))*22+Math.random()*8}px"></i>`
  ).join(''))
</script>
```

---

## Scene 6: Style Room

**Line range:** 1370–1475

### Markup

```html
<div class="scene-header" id="s6">
  <div>
    <div class="scene-num">Scene 06 — Style Room</div>
    <h2 class="scene-title">Captions and visuals <em>that match your brand.</em></h2>
    <p class="scene-sub">A dedicated style step — pick a caption preset, lock in colours from your brand kit, and choose music-visual overlays (waveforms, EQ bars, logos) that pulse with the track. Everything previews live on the centre stage.</p>
  </div>
  <div class="scene-tags">
    <span class="tag">Brand kits</span>
    <span class="tag">Beat-synced overlays</span>
    <span class="tag">Bar-aligned timing</span>
  </div>
</div>

<div class="canvas">
  <div class="scrim"></div>
  <div class="cap-room">
    <div class="cap-left">
      <h2>Caption <em>presets</em></h2>
      <p>Beat-synced reveals lock to the bar grid detected during analysis. All four presets respect your brand kit colours.</p>
      <div class="preset-grid">
        <div class="preset on">
          <div class="demo"><span class="cap-style-1">EVERY <b>DAY</b></span></div>
          <div class="name">YAP · Bold Stack</div>
          <div class="meta">Inter Black · drop shadow</div>
        </div>
        <div class="preset">
          <div class="demo"><span class="cap-style-2">time-<b>rich</b></span></div>
          <div class="name">Editorial Italic</div>
          <div class="meta">Fraunces · accent word</div>
        </div>
        <div class="preset">
          <div class="demo"><span class="cap-style-3">[ TANYA · 02:14 ]</span></div>
          <div class="name">Subtitle Mono</div>
          <div class="meta">JetBrains · documentary</div>
        </div>
        <div class="preset">
          <div class="demo"><span class="cap-style-4">DAILY</span></div>
          <div class="name">Karaoke Block</div>
          <div class="meta">High-contrast · TikTok</div>
        </div>
      </div>
    </div>

    <div class="cap-right">
      <div class="panel-h">
        <div class="ti">Style: YAP · Bold Stack</div>
        <button class="btn" style="padding:6px 10px;font-size:12px">Save as preset</button>
      </div>

      <div class="style-row">
        <label>Accent colour</label>
        <div class="swatches">
          <div class="sw on" style="background:#e8b766"></div>
          <div class="sw" style="background:#cf6b58"></div>
          <div class="sw" style="background:#7fb685"></div>
          <div class="sw" style="background:#7aa6e0"></div>
          <div class="sw" style="background:#f6efe2"></div>
        </div>
      </div>
      <div class="style-row">
        <label>Highlight word</label>
        <div class="toggle"><div class="switch on"></div><span style="font-size:12px;color:var(--paper-dim)">On</span></div>
      </div>
      <div class="style-row">
        <label>Word-level reveal</label>
        <div class="toggle"><div class="switch on"></div><span style="font-size:12px;color:var(--paper-dim)">On</span></div>
      </div>
      <div class="style-row">
        <label>Background fill</label>
        <div class="toggle"><div class="switch"></div><span style="font-size:12px;color:var(--paper-dim)">Off</span></div>
      </div>

      <div style="margin-top:8px">
        <div class="panel-h">
          <div class="ti" style="font-size:16px">Music-visual overlays</div>
          <div class="ct">Pulses with the beat grid</div>
        </div>
        <div class="broll-strip">
          <div class="broll-thumb b-1"><span class="l">🎚️ EQ bars</span></div>
          <div class="broll-thumb b-2"><span class="l">🌊 Waveform</span></div>
          <div class="broll-thumb b-3"><span class="l">⭕ Logo pulse</span></div>
          <div class="broll-thumb b-4"><span class="l">💿 Vinyl spin</span></div>
        </div>
        <button class="btn" style="margin-top:10px;width:100%">+ Upload custom overlay</button>
      </div>

      <div style="margin-top:14px;padding-top:14px;border-top:1px solid var(--line)">
        <div class="panel-h">
          <div class="ti" style="font-size:16px">Brand kit</div>
          <div class="ct">Sjuul Studios · default</div>
        </div>
        <div class="style-row">
          <label>Logo</label>
          <div style="display:flex;gap:8px;align-items:center">
            <div style="width:36px;height:36px;border-radius:8px;background:linear-gradient(135deg,var(--amber-2),var(--copper));display:grid;place-items:center;font-family:var(--serif);font-weight:700;color:#1a1208">S</div>
            <button class="btn" style="padding:6px 10px;font-size:12px">Replace</button>
          </div>
        </div>
        <div class="style-row">
          <label>Brand font</label>
          <span style="font-family:var(--serif);font-size:14px;color:var(--paper)">Fraunces · Italic</span>
        </div>
      </div>
    </div>
  </div>
</div>
```

### Scoped CSS (lines 586–645)

```css
.cap-room{padding:30px 40px 40px;display:grid;grid-template-columns:1fr 1.1fr;gap:32px;min-height:760px;align-items:start}
.cap-left h2{font-family:var(--serif);font-size:34px;font-weight:500;margin:0 0 6px;letter-spacing:-.3px}
.cap-left h2 em{font-style:italic;color:var(--amber-2);font-weight:400}
.cap-left p{color:var(--paper-dim);font-size:13.5px;margin:0 0 18px;line-height:1.6;max-width:48ch}
.preset-grid{display:grid;grid-template-columns:repeat(2,1fr);gap:12px}
.preset{
  border:1px solid var(--line);border-radius:14px;padding:18px 14px 14px;text-align:center;background:rgba(0,0,0,0.25);
  cursor:pointer;transition:.2s;position:relative;
}
.preset:hover{border-color:rgba(232,183,102,0.35)}
.preset.on{border-color:rgba(232,183,102,0.5);background:linear-gradient(180deg, rgba(232,183,102,0.10), rgba(0,0,0,0.25))}
.preset .demo{
  aspect-ratio:9/12;border-radius:10px;margin-bottom:10px;
  display:grid;place-items:center;padding:14px;
  background:linear-gradient(135deg,#2a1c12,#5a3a23 60%,#8a5a2c);
  position:relative;overflow:hidden;
}
.preset .demo::after{content:"";position:absolute;inset:0;background:radial-gradient(circle at 50% 60%, transparent 30%, rgba(0,0,0,0.6))}
.preset .demo span{position:relative;z-index:2;text-align:center}
.preset .name{font-family:var(--serif);font-size:14px;font-weight:500}
.preset .meta{font-size:11px;color:var(--paper-dim);margin-top:2px}

.cap-style-1{font-family:var(--sans);font-weight:800;color:#ffffff;text-shadow:0 3px 0 #1a1208;font-size:18px;line-height:1.1;letter-spacing:-.5px}
.cap-style-1 b{color:var(--amber-2)}
.cap-style-2{font-family:var(--serif);font-weight:600;font-style:italic;color:var(--paper);font-size:18px;line-height:1.1}
.cap-style-2 b{color:var(--amber-2);font-style:normal}
.cap-style-3{font-family:var(--mono);font-weight:500;color:var(--amber);font-size:13px;letter-spacing:.05em;background:rgba(0,0,0,0.6);padding:6px 8px;border-radius:4px}
.cap-style-4{font-family:var(--sans);font-weight:700;color:#1a1208;background:var(--amber);padding:4px 8px;border-radius:4px;font-size:16px;line-height:1.2;display:inline-block}

.cap-right{
  border:1px solid var(--line);border-radius:18px;padding:22px;background:rgba(0,0,0,0.25);
  display:flex;flex-direction:column;gap:18px;
}
.style-row{display:flex;gap:10px;align-items:center;justify-content:space-between}
.style-row label{font-size:12px;color:var(--paper-dim);font-family:var(--mono);letter-spacing:.1em;text-transform:uppercase}
.swatches{display:flex;gap:6px}
.sw{width:24px;height:24px;border-radius:6px;border:1px solid var(--line-2);cursor:pointer}
.sw.on{box-shadow:0 0 0 2px var(--amber)}
.toggle{display:inline-flex;align-items:center;gap:8px}
.switch{
  width:36px;height:20px;border-radius:999px;background:rgba(255,255,255,0.08);position:relative;border:1px solid var(--line-2);
}
.switch::after{content:"";position:absolute;top:2px;left:2px;width:14px;height:14px;border-radius:50%;background:var(--paper);transition:.2s}
.switch.on{background:linear-gradient(90deg, var(--amber), var(--copper));border-color:transparent}
.switch.on::after{left:18px;background:#1a1208}

.broll-strip{
  display:grid;grid-template-columns:repeat(4,1fr);gap:8px;margin-top:6px;
}
.broll-thumb{
  aspect-ratio:1;border-radius:8px;border:1px solid var(--line-2);
  background-size:cover;background-position:center;position:relative;cursor:pointer;
}
.broll-thumb::after{content:"";position:absolute;inset:0;border-radius:8px;background:linear-gradient(180deg,transparent 50%,rgba(0,0,0,0.6))}
.broll-thumb .l{position:absolute;left:6px;bottom:6px;font-size:10px;font-family:var(--mono);color:var(--paper);z-index:2}
.b-1{background:linear-gradient(135deg,#2a1c12,#5a3a23,#8a5a2c)}
.b-2{background:linear-gradient(135deg,#1a1410,#3a2c1f,#a8782e)}
.b-3{background:linear-gradient(135deg,#241813,#6a3825,#cf6b58)}
.b-4{background:linear-gradient(135deg,#22150e,#553a25,#d4a548)}
```

### Scoped JS

None.

---

## Scene 7: Export

**Line range:** 1478–1574

### Markup

```html
<div class="scene-header" id="s7">
  <div>
    <div class="scene-num">Scene 07 — Export</div>
    <h2 class="scene-title">Render with the <em>full Metal stack.</em></h2>
    <p class="scene-sub">A rendering panel that also tells you why it's fast — live GPU and ANE meters, codec choice, and a queue that can run multiple clips in parallel.</p>
  </div>
  <div class="scene-tags">
    <span class="tag">VideoToolbox</span>
    <span class="tag">H.265 / ProRes</span>
    <span class="tag">Batch queue</span>
  </div>
</div>

<div class="canvas">
  <div class="scrim"></div>
  <div class="export">
    <div class="export-left">
      <h2>Export <em>this set.</em></h2>
      <p class="lead">8 clips · estimated 2 min 14s on your M2 Pro using VideoToolbox H.265 hardware encoder. Render queue runs 3 clips in parallel.</p>

      <div style="font-family:var(--mono);font-size:11px;letter-spacing:.18em;color:var(--mute);text-transform:uppercase;margin-bottom:8px">Resolution</div>
      <div class="opt-row">
        <div class="opt"><span class="v">1080 × 1920</span><span class="s">9:16 · standard</span></div>
        <div class="opt on"><span class="v">2160 × 3840</span><span class="s">9:16 · 4K master</span></div>
        <div class="opt"><span class="v">Source res</span><span class="s">Match input</span></div>
      </div>

      <div style="font-family:var(--mono);font-size:11px;letter-spacing:.18em;color:var(--mute);text-transform:uppercase;margin-bottom:8px">Codec</div>
      <div class="opt-row">
        <div class="opt on"><span class="v">H.265 HW</span><span class="s">VideoToolbox</span></div>
        <div class="opt"><span class="v">H.264 HW</span><span class="s">Universal</span></div>
        <div class="opt"><span class="v">ProRes 422</span><span class="s">Master quality</span></div>
      </div>

      <div style="font-family:var(--mono);font-size:11px;letter-spacing:.18em;color:var(--mute);text-transform:uppercase;margin-bottom:8px">Frame rate</div>
      <div class="opt-row">
        <div class="opt"><span class="v">30 fps</span><span class="s">Web standard</span></div>
        <div class="opt on"><span class="v">60 fps</span><span class="s">Smooth captions</span></div>
        <div class="opt"><span class="v">Match source</span><span class="s">Auto</span></div>
      </div>

      <button class="btn btn-primary" style="margin-top:18px;padding:14px 22px;font-size:14px">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4"><path d="M5 12h14M13 5l7 7-7 7"/></svg>
        Render 8 clips
      </button>
    </div>

    <div class="export-right">
      <div style="font-family:var(--mono);font-size:11px;letter-spacing:.2em;color:var(--paper-dim);text-transform:uppercase;margin-bottom:10px">Render queue · 3/8 done</div>

      <div class="render-card">
        <div class="pv th-1"></div>
        <div class="info">
          <div class="t">Time-rich daily creator</div>
          <div class="s">★ 94 · 0:34 · H.265 4K</div>
          <div class="progress"><span style="width:100%"></span></div>
        </div>
        <div style="font-family:var(--mono);font-size:11px;color:var(--ok)">DONE</div>
      </div>
      <div class="render-card">
        <div class="pv th-2"></div>
        <div class="info">
          <div class="t">What type of creator</div>
          <div class="s">★ 91 · 0:48 · H.265 4K</div>
          <div class="progress"><span style="width:100%"></span></div>
        </div>
        <div style="font-family:var(--mono);font-size:11px;color:var(--ok)">DONE</div>
      </div>
      <div class="render-card">
        <div class="pv th-3"></div>
        <div class="info">
          <div class="t">Cold-start tactics</div>
          <div class="s">★ 88 · 0:27 · H.265 4K</div>
          <div class="progress"><span style="width:64%"></span></div>
        </div>
        <div style="font-family:var(--mono);font-size:11px;color:var(--amber-2)">64%</div>
      </div>
      <div class="render-card">
        <div class="pv th-4"></div>
        <div class="info">
          <div class="t">Posting daily beats perfect</div>
          <div class="s">★ 85 · 0:55 · H.265 4K</div>
          <div class="progress"><span style="width:12%"></span></div>
        </div>
        <div style="font-family:var(--mono);font-size:11px;color:var(--amber-2)">12%</div>
      </div>

      <div class="gpu-meter">
        <h4>Live hardware utilisation</h4>
        <div class="meter-row"><span class="lbl">GPU (Metal)</span><div class="meter"><span style="width:78%"></span></div><span class="v">78%</span></div>
        <div class="meter-row"><span class="lbl">ANE (Neural)</span><div class="meter"><span style="width:42%"></span></div><span class="v">42%</span></div>
        <div class="meter-row"><span class="lbl">Media engine</span><div class="meter"><span style="width:64%"></span></div><span class="v">64%</span></div>
        <div class="meter-row"><span class="lbl">CPU</span><div class="meter"><span style="width:23%"></span></div><span class="v">23%</span></div>
      </div>
    </div>
  </div>
</div>
```

### Scoped CSS (lines 647–690)

```css
.export{padding:50px 60px;display:grid;grid-template-columns:1.05fr 1fr;gap:50px;min-height:680px;align-items:center}
.export-left h2{font-family:var(--serif);font-size:48px;font-weight:500;margin:0 0 16px;letter-spacing:-.5px}
.export-left h2 em{font-style:italic;color:var(--amber-2);font-weight:400}
.export-left .lead{color:var(--paper-dim);font-size:15px;line-height:1.65;max-width:46ch;margin:0 0 24px}
.opt-row{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin-bottom:14px}
.opt{
  padding:14px;border-radius:12px;border:1px solid var(--line-2);background:rgba(0,0,0,0.25);
  cursor:pointer;text-align:center;
}
.opt.on{border-color:rgba(232,183,102,0.45);background:linear-gradient(180deg, rgba(232,183,102,0.12), rgba(0,0,0,0.25))}
.opt .v{font-family:var(--serif);font-size:16px;font-weight:500;display:block}
.opt .s{font-size:11px;color:var(--paper-dim);margin-top:2px;display:block}

.export-right{
  border:1px solid var(--line);border-radius:24px;padding:30px;background:rgba(0,0,0,0.3);position:relative;overflow:hidden;
}
.export-right::before{
  content:"";position:absolute;inset:0;background:radial-gradient(600px 300px at 100% 0%, rgba(232,183,102,0.12), transparent 60%);pointer-events:none;
}
.render-card{
  display:flex;align-items:center;gap:16px;padding:14px;border-radius:14px;background:rgba(0,0,0,0.4);border:1px solid var(--line);margin-bottom:12px;
}
.render-card .pv{
  width:64px;aspect-ratio:9/16;border-radius:8px;flex:none;
  background:linear-gradient(135deg,#3a2618,#7a4a23,#c2864a);
}
.render-card .info{flex:1;min-width:0}
.render-card .info .t{font-family:var(--serif);font-size:15px;font-weight:500;margin:0 0 2px}
.render-card .info .s{font-size:11px;color:var(--paper-dim)}
.progress{
  height:6px;border-radius:999px;background:rgba(255,255,255,0.08);overflow:hidden;margin-top:8px;
}
.progress span{display:block;height:100%;background:linear-gradient(90deg,var(--amber),var(--copper));border-radius:999px}

.gpu-meter{
  margin-top:18px;padding:16px;border:1px solid var(--line);border-radius:14px;background:rgba(0,0,0,0.35);
}
.gpu-meter h4{margin:0 0 10px;font-family:var(--mono);font-size:11px;letter-spacing:.2em;color:var(--paper-dim);text-transform:uppercase}
.meter-row{display:flex;align-items:center;gap:10px;margin-bottom:8px;font-size:12px;font-family:var(--mono);color:var(--paper-dim)}
.meter-row .lbl{width:90px}
.meter{flex:1;height:6px;border-radius:999px;background:rgba(255,255,255,0.06);overflow:hidden}
.meter span{display:block;height:100%;background:linear-gradient(90deg, var(--amber), var(--rose))}
.meter-row .v{width:48px;text-align:right;color:var(--amber-2)}
```

### Scoped JS

None.

---

## Scene 8: Ship It

**Line range:** 1577–1623

### Markup

```html
<div class="scene-header" id="s8">
  <div>
    <div class="scene-num">Scene 08 — Ship It</div>
    <h2 class="scene-title">From timeline <em>to feed.</em></h2>
    <p class="scene-sub">Don't make people leave the app to ship. Direct publish to TikTok, Reels, Shorts, LinkedIn, and Snapchat — or schedule a whole batch as a content drop.</p>
  </div>
  <div class="scene-tags">
    <span class="tag">Multi-platform</span>
    <span class="tag">Schedule batch</span>
    <span class="tag">Per-platform tweaks</span>
  </div>
</div>

<div class="canvas">
  <div class="scrim"></div>
  <div class="share">
    <div class="share-left">
      <div class="pv-stage">
        <div class="cap">I'm <b>time-rich</b>, I gotta make something <b>every day.</b></div>
      </div>
    </div>
    <div class="share-right">
      <h2>Publish <em>everywhere.</em></h2>
      <p>Captions, aspect, and hashtags adapt per platform. Drop one batch, hit four feeds — or send it to your scheduling stack.</p>

      <div class="dest-grid">
        <div class="dest"><div class="ico">🎵</div><div><div class="n">TikTok</div><div class="s">9:16 · captions burned</div></div></div>
        <div class="dest"><div class="ico">📸</div><div><div class="n">Instagram Reels</div><div class="s">9:16 · cover frame</div></div></div>
        <div class="dest"><div class="ico">▶️</div><div><div class="n">YouTube Shorts</div><div class="s">9:16 · 60s max</div></div></div>
        <div class="dest"><div class="ico">💼</div><div><div class="n">LinkedIn</div><div class="s">1:1 · open captions</div></div></div>
        <div class="dest"><div class="ico">👻</div><div><div class="n">Snapchat</div><div class="s">9:16 · Spotlight ready</div></div></div>
        <div class="dest"><div class="ico">📅</div><div><div class="n">Buffer / Later</div><div class="s">Send to scheduler</div></div></div>
      </div>

      <div class="schedule-card">
        <div>
          <div class="ti">Schedule this batch</div>
          <div class="s">Drop one clip every weekday at 8:00 AM CET, starting tomorrow.</div>
        </div>
        <div style="display:flex;gap:8px">
          <button class="btn">Edit schedule</button>
          <button class="btn btn-primary">Schedule all 8</button>
        </div>
      </div>
    </div>
  </div>
</div>
```

### Scoped CSS (lines 692–723)

```css
.share{padding:50px 60px;display:grid;grid-template-columns:1fr 1.1fr;gap:50px;align-items:center;min-height:640px}
.share-left .pv-stage{
  width:min(100%,300px);aspect-ratio:9/16;border-radius:20px;margin:0 auto;
  background:linear-gradient(135deg,#3b2716,#7a4a23 50%,#c2864a);position:relative;overflow:hidden;
  box-shadow:var(--shadow-2);
}
.share-left .pv-stage::after{content:"";position:absolute;inset:0;background:radial-gradient(circle at 50% 50%, transparent 30%, rgba(0,0,0,0.55))}
.share-left .pv-stage .cap{
  position:absolute;left:14px;right:14px;bottom:36px;text-align:center;font-family:var(--serif);font-weight:600;font-size:22px;line-height:1.15;text-shadow:0 4px 12px rgba(0,0,0,0.7);z-index:2;
}
.share-left .pv-stage .cap b{color:var(--amber-2)}

.share-right h2{font-family:var(--serif);font-size:42px;font-weight:500;margin:0 0 12px;letter-spacing:-.4px}
.share-right h2 em{font-style:italic;color:var(--amber-2);font-weight:400}
.share-right p{color:var(--paper-dim);font-size:14.5px;line-height:1.65;max-width:48ch;margin:0 0 24px}
.dest-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin-bottom:18px}
.dest{
  padding:14px;border:1px solid var(--line-2);border-radius:12px;background:rgba(0,0,0,0.25);
  display:flex;flex-direction:column;align-items:flex-start;gap:6px;cursor:pointer;
}
.dest:hover{border-color:rgba(232,183,102,0.4)}
.dest .ico{width:30px;height:30px;border-radius:8px;display:grid;place-items:center;background:rgba(232,183,102,0.12);color:var(--amber-2)}
.dest .n{font-size:13px;font-weight:500}
.dest .s{font-size:11px;color:var(--paper-dim)}

.schedule-card{
  padding:16px;border-radius:14px;border:1px solid var(--line);background:rgba(0,0,0,0.3);
  display:flex;align-items:center;justify-content:space-between;gap:12px;
}
.schedule-card .ti{font-family:var(--serif);font-size:16px;font-weight:500}
.schedule-card .s{font-size:12px;color:var(--paper-dim);margin-top:2px}
```

### Scoped JS

None.

---

## Cross-Scene Reusable Components

### Topbar (lines 61–93)

```css
.topbar{
  display:flex;align-items:center;justify-content:space-between;gap:24px;
  padding:14px 18px;border:1px solid var(--line);
  background:linear-gradient(180deg, rgba(255,255,255,0.02), rgba(0,0,0,0.2));
  border-radius:var(--r-lg);
  backdrop-filter: blur(14px);
  position:sticky;top:14px;z-index:50;
}
.brand{display:flex;align-items:center;gap:12px}
.brand-mark{
  width:34px;height:34px;border-radius:10px;
  background:
    conic-gradient(from 200deg, var(--amber), var(--copper), var(--amber-deep), var(--amber));
  box-shadow: 0 6px 20px -6px rgba(232,183,102,0.6), inset 0 0 0 1px rgba(255,255,255,0.2);
  position:relative;
}
.brand-mark::after{
  content:"";position:absolute;inset:6px;border-radius:6px;
  background:radial-gradient(circle at 30% 30%, rgba(255,255,255,0.7), rgba(255,255,255,0) 50%), var(--ink-0);
}
.brand-name{font-family:var(--serif);font-weight:600;font-size:20px;letter-spacing:.2px}
.brand-name em{color:var(--amber);font-style:normal}

.nav-tabs{display:flex;gap:4px;padding:4px;border:1px solid var(--line);border-radius:999px;background:rgba(0,0,0,0.3)}
.nav-tabs button{
  padding:8px 14px;border-radius:999px;font-size:12.5px;letter-spacing:.2px;color:var(--paper-dim);
  transition:.2s ease;
}
.nav-tabs button:hover{color:var(--paper)}
.nav-tabs button.active{
  background:linear-gradient(180deg, rgba(232,183,102,0.18), rgba(232,183,102,0.08));
  color:var(--amber-2);box-shadow: inset 0 0 0 1px rgba(232,183,102,0.35);
}

.top-actions{display:flex;align-items:center;gap:10px}
.pill{
  display:inline-flex;align-items:center;gap:8px;
  padding:8px 14px;border-radius:999px;border:1px solid var(--line-2);
  font-size:12.5px;color:var(--paper-dim);background:rgba(255,255,255,0.02);
}
.pill .dot{width:6px;height:6px;border-radius:50%;background:var(--ok);box-shadow:0 0 10px var(--ok)}
```

### Frame / Container (lines 58–60)

```css
.frame{
  max-width:1440px;margin:0 auto;padding:28px 28px 80px;
}
```

### Upgrade Card (lines 170–177)

```css
.upgrade-card{
  margin-top:auto;padding:16px;border-radius:14px;border:1px solid var(--line-2);
  background:
    radial-gradient(120% 120% at 0% 0%, rgba(232,183,102,0.18), rgba(0,0,0,0) 60%),
    rgba(0,0,0,0.3);
}
.upgrade-card .h{font-family:var(--serif);font-size:18px;margin:4px 0 4px}
.upgrade-card .p{font-size:12px;color:var(--paper-dim);margin-bottom:12px;line-height:1.5}
```

### Global JavaScript (lines 1772–1795)

```javascript
<script>
  function scrollToScene(id){
    const el = document.getElementById(id);
    if(!el) return;
    el.scrollIntoView({behavior:'smooth', block:'start'});
    document.querySelectorAll('.nav-tabs button').forEach(b=>b.classList.remove('active'));
    const idx = ['s1','s2','s3','s4','s5','s6','s7','s8','gpu'].indexOf(id);
    if(idx>=0){ document.querySelectorAll('.nav-tabs button')[idx].classList.add('active'); }
  }
  // Scroll spy
  const ids = ['s1','s2','s3','s4','s5','s6','s7','s8','gpu'];
  const obs = new IntersectionObserver((entries)=>{
    entries.forEach(e=>{
      if(e.isIntersecting){
        const i = ids.indexOf(e.target.id);
        if(i>=0){
          document.querySelectorAll('.nav-tabs button').forEach(b=>b.classList.remove('active'));
          document.querySelectorAll('.nav-tabs button')[i].classList.add('active');
        }
      }
    });
  },{rootMargin:'-40% 0px -55% 0px'});
  ids.forEach(id=>{ const el = document.getElementById(id); if(el) obs.observe(el); });
</script>
```

---

## Summary

**Total markdown line count:** 1,127 lines

**All 8 scenes found and extracted:** ✓
- Scene 1: Library (sidebar + editorial dashboard)
- Scene 2: Upload (drop zone with source buttons)
- Scene 3: AI Detection (concentric rings + 5-stage pipeline)
- Scene 4: Clip Picker (vertical cards with scores)
- Scene 5: Editor (3-column layout + timeline)
- Scene 6: Style Room (caption presets + brand kit)
- Scene 7: Export (resolution/codec/fps cards + hardware meters)
- Scene 8: Ship It (platform cards + batch schedule)

**Structural surprises:**
- Scene 5 (Editor) is by far the largest: 200+ lines including a multi-track timeline with waveform generation via inline JS.
- All scenes wrap in `.canvas` (position relative + overflow hidden + 1px border) with an inner `.scrim` (radial gradients for lighting).
- Timeline in Scene 5 uses inline `<script>` to generate waveform bar heights procedurally.
- Scene 6 (Style Room) has 4 caption style variants (`.cap-style-1` through `.cap-style-4`) used as demo text in preset cards.
- Scene 8 does NOT have a preview on the right side like Scene 5; instead the preview is centered on the left with a single caption overlay.
- Global scroll-spy JS uses IntersectionObserver to track which scene is in view and highlight the nav tab.

