"""Build the ofcourseduh.com preview site (Remotely Local). Run: python3 build.py && git add -A && git commit && git push
Episodes are unlisted YouTube embeds; Remotely Local shorts are copied as web mp4s from _videouse/review-shorts/media."""
import html, json, re, shutil, subprocess
from pathlib import Path
OUT = Path(__file__).parent
RLV = Path('/mnt/work/videos/Remotely Local/_videouse')
esc = html.escape

def yid(u): m = re.search(r'([\w-]{11})$', u or ''); return m.group(1) if m else ''
def dur(p):
    return float(subprocess.run(['ffprobe','-v','error','-show_entries','format=duration','-of','csv=p=0',str(p)],capture_output=True,text=True).stdout or 0)
def mmss(s): s=int(round(s)); return f'{s//60}:{s%60:02d}'
def chapters_html(txt, vid):
    out=[]
    for line in txt.strip().splitlines():
        m=re.match(r'(\d+):(\d\d)\s+(.*)',line.strip())
        if m: t=int(m[1])*60+int(m[2]); out.append(f'<li><a href="https://youtu.be/{vid}?t={t}" target="_blank" rel="noopener">{m[1]}:{m[2]}</a> {esc(m[3])}</li>')
    return '<ol class="ch">'+''.join(out)+'</ol>' if out else ''

def episode(title, vid, desc_md, chapters, length, extra=''):
    paras=[p.strip() for p in desc_md.strip().split('\n\n') if p.strip()]
    hook, body = (paras[0], paras[1:]) if paras else ('', [])
    player = (f'<div class="yt"><iframe src="https://www.youtube-nocookie.com/embed/{vid}?rel=0" title="{esc(title)}" loading="lazy" '
              f'allow="accelerometer; encrypted-media; gyroscope; picture-in-picture; fullscreen" allowfullscreen></iframe></div>') if vid else '<div class="yt pending">Uploading to YouTube…</div>'
    return f'''<article class="ep">{player}<div class="info"><h3>{esc(title)}</h3><p class="len">{length}{(' · <a href="https://youtu.be/'+vid+'" target="_blank" rel="noopener">Open on YouTube</a>') if vid else ''}</p>
<p class="hook">{esc(hook)}</p>{''.join(f'<p>{esc(p)}</p>' for p in body)}{extra}
<details><summary>Chapters</summary>{chapters_html(chapters, vid) if vid else ''}</details></div></article>'''

# ---------- Remotely Local ----------
rlu = json.loads((RLV/'youtube'/'rl_uploads.json').read_text()) if (RLV/'youtube'/'rl_uploads.json').exists() else {}
RL_EPS = [('backstory','backstory/edit/final.mp4'),('music','music/edit/final.mp4'),('batfast','batfast/edit/final.mp4'),('span','span/edit/final-audiofix2.mp4')]
TITLES = {'backstory':'Defying Entropy: Mike Johnson on the Group 42 CD, Anchor ID and AI Attribution',
          'music':'Making Music with AI: Mike Johnson on a Playa Gift, Chronosonics and a Clear Lake Album',
          'batfast':'Bringing AI to Batting Practice with Jignesh Patel of BatFast',
          'span':'Data Centers in Your Backyard with Josh Mustill of SPAN'}
rl_eps=[]
for key, rel in RL_EPS:
    d=(RLV/rel).parent; u=rlu.get(key,{})
    rl_eps.append(episode(u.get('title',TITLES[key]), yid(u.get('url','')), (d/'description.md').read_text(), (d/'chapters.txt').read_text(), mmss(dur(RLV/rel))))

# shorts
RLD = OUT/'remotelylocal'; RLD.mkdir(exist_ok=True)
M = RLD/'media'; M.mkdir(exist_ok=True)
src = RLV/'review-shorts'
shorts = json.loads((src/'shorts.json').read_text()); sh=[]
for ep in shorts:
    sh.append(f'<h3 class="sub">{esc(ep["label"])} <span>{esc(ep["title"])}</span></h3><div class="grid">')
    for s in ep['shorts']:
        for ext in ('mp4','jpg'):
            f=src/'media'/f'{s["code"]}.{ext}'
            if f.exists() and (not (M/f.name).exists() or (M/f.name).stat().st_size!=f.stat().st_size): shutil.copy2(f, M/f.name)
        d=dur(M/f'{s["code"]}.mp4') if (M/f'{s["code"]}.mp4').exists() else 0
        sh.append(f'''<div class="card"><video controls playsinline preload="none" poster="media/{s["code"]}.jpg" src="media/{s["code"]}.mp4"></video>
<div class="meta"><b>{s["code"]}</b> · {d:.0f}s<h4><span class="p">&gt;</span> {esc(s["hook"])}<span class="p">_</span></h4><p>{esc(s["what"])}</p><p class="cap">{esc(s["caption"])}</p></div></div>''')
    sh.append('</div>')

CSS = '''*{box-sizing:border-box}body{margin:0;background:#05070d;color:#F4F3F6;font:16px/1.55 'IBM Plex Sans',system-ui,sans-serif}
main{max-width:1180px;margin:0 auto;padding:28px 18px 70px}a{color:#4fb3f0}
header h1{font-family:'IBM Plex Mono',monospace;font-size:32px;margin:0}.p{color:#0094E6}
nav{display:flex;gap:18px;margin:14px 0 6px;font-family:'IBM Plex Mono',monospace;font-size:14px}nav a{text-decoration:none}
.note{color:#9fb2c8;font-size:14px}
h2{font-family:'IBM Plex Mono',monospace;color:#0094E6;border-top:1px solid #12305a;padding-top:22px;margin:44px 0 18px;font-size:15px;letter-spacing:.12em;text-transform:uppercase}
h3.sub{font-family:'IBM Plex Mono',monospace;color:#0094E6;font-size:14px;letter-spacing:.1em;margin:30px 0 12px}h3.sub span{display:block;color:#F4F3F6;font-family:'IBM Plex Sans',sans-serif;letter-spacing:0;font-size:18px}
.ep{display:grid;grid-template-columns:minmax(0,1.25fr) minmax(0,1fr);gap:22px;margin:0 0 34px;background:#0b1322;border:1px solid #16263f;border-radius:10px;padding:16px}
@media(max-width:860px){.ep{grid-template-columns:1fr}}
.yt{position:relative;aspect-ratio:16/9;background:#000;border-radius:6px;overflow:hidden}.yt iframe{position:absolute;inset:0;width:100%;height:100%;border:0}
.yt.pending{display:grid;place-items:center;color:#9fb2c8;font-family:'IBM Plex Mono',monospace}
.info h3{margin:0 0 4px;font-size:20px;line-height:1.3}.len{margin:0 0 10px;color:#9fb2c8;font-size:14px}.hook{font-weight:600}.info p{margin:0 0 10px;font-size:15px}
details summary{cursor:pointer;color:#4fb3f0;font-family:'IBM Plex Mono',monospace;font-size:14px}.ch{padding-left:18px;font-size:14px}.ch li{margin:3px 0}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(230px,1fr));gap:18px}.card{background:#0c1424;border:1px solid #16263f;border-radius:8px;overflow:hidden}
video{width:100%;aspect-ratio:9/16;background:#000;display:block}.meta{padding:10px 12px;font-size:14px}.meta h4{font-family:'IBM Plex Mono',monospace;margin:6px 0;font-size:15px}.meta p{margin:4px 0}.cap{color:#9fb2c8}
.gw{border-color:#5a1a1a}.gwh{color:#e8b7a8}.btn{display:inline-block;margin:6px 10px 0 0;padding:8px 14px;border:1px solid #0094E6;border-radius:6px;text-decoration:none;font-family:'IBM Plex Mono',monospace;font-size:14px}'''

def page(title, nav, body):
    return f'''<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex,nofollow"><title>{title}</title>
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@500;700&family=IBM+Plex+Sans:wght@400;600&display=swap" rel="stylesheet">
<style>{CSS}</style></head><body><main>
<header><h1><span class="p">❯</span>{title}<span class="p">_</span></h1><nav>{nav}</nav>
<p class="note">Work in progress, for review. Episodes are unlisted on YouTube; please don't share the links publicly yet.</p></header>
{body}</main></body></html>'''
rl_body = f'''<h2 id="episodes">New episodes</h2>{''.join(rl_eps)}<h2 id="shorts">Shorts</h2>{''.join(sh)}'''
(RLD/'index.html').write_text(page('remotely.local', '<a href="#episodes">Episodes</a><a href="#shorts">Shorts</a>', rl_body))
print('built;', sum(1 for _ in M.glob('*.mp4')), 'shorts')
