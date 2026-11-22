"""Helpers behind pv.sh: list scenes in file order, build contact sheets, join scene videos.

  pvtool.py scenes FILE.py
  pvtool.py sheets DIR OUTDIR SCENE...     one PNG grid of frames per scene, each frame stamped with its time;
                                           frames are taken just before each caption change when
                                           OUTDIR/beats/SCENE.txt exists (pv.sh low writes it)
  pvtool.py join DIR OUT.mp4 SCENE...      lossless join of DIR/SCENE.mp4 in the order given
  pvtool.py info VIDEO.mp4                 duration, resolution, frame rate and size
  pvtool.py frames VIDEO.mp4 OUTDIR T...   one PNG per time T (seconds), for spot checks of the joined video,
                                           and OUTDIR/<video>_strip.png: all of them in one image

Needs PyAV and Pillow, which every manim install has.
"""

import ast
import sys
from fractions import Fraction
from pathlib import Path

SCENE_BASES = {"Scene", "Captioned", "MovingCameraScene", "ThreeDScene", "ZoomedScene"}


def scenes(path):
    """Scene classes of a manim file, in source order (which is the video's order)."""
    tree = ast.parse(Path(path).read_text())
    known = set(SCENE_BASES)
    out = []
    for node in tree.body:
        if not isinstance(node, ast.ClassDef):
            continue
        bases = {b.id for b in node.bases if isinstance(b, ast.Name)}
        if bases & known:
            known.add(node.name)
            if node.name not in SCENE_BASES and not node.name.startswith("_"):
                out.append(node.name)
    # A class used only as a base for other scenes is not itself a scene of the video.
    used_as_base = {b.id for n in tree.body if isinstance(n, ast.ClassDef) for b in n.bases if isinstance(b, ast.Name)}
    return [n for n in out if n not in used_as_base]


def sheets(src, outdir, names):
    import av
    from PIL import Image, ImageDraw

    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    for name in names:
        path = Path(src) / f"{name}.mp4"
        if not path.exists():
            print(f"{name}: no {path}")
            continue
        with av.open(str(path)) as c:
            st = c.streams.video[0]
            dur = float(c.duration / 1_000_000) if c.duration else float(st.duration * st.time_base)
            beats = outdir / "beats" / f"{name}.txt"
            times = []
            if beats.exists():
                times = [float(x) - 0.1 for x in beats.read_text().split() if 0.3 < float(x)]
            if times:
                if len(times) > 18:
                    times = [times[round(i * (len(times) - 1) / 17)] for i in range(18)]
            else:
                n = max(6, min(15, round(dur / 4)))
                times = [(i + 0.85) * dur / n for i in range(n)]
            # Decode once and keep only the picked frames, so memory does not grow with the scene's length.
            times.sort()
            picks, last = [], None
            for f in c.decode(st):
                last = f
                while len(picks) < len(times) and float(f.time or 0) >= times[len(picks)]:
                    picks.append((float(f.time or 0), f.to_image()))
            if last is None:
                print(f"{name}: no frames in {path}")
                continue
            while len(picks) < len(times):
                picks.append((float(last.time or 0), last.to_image()))
        n = len(picks)
        w, h = picks[0][1].size
        cols = 3
        rows = (n + cols - 1) // cols
        sheet = Image.new("RGB", (w * cols, h * rows), "white")
        for i, (t, im) in enumerate(picks):
            im = im.copy()
            d = ImageDraw.Draw(im)
            d.rectangle([w - 70, 0, w, 18], fill="black")
            d.text((w - 66, 3), f"{t:6.1f}s", fill="yellow")
            # 1px grid lines so tiles are distinguishable
            d.rectangle([0, 0, w - 1, h - 1], outline="white")
            sheet.paste(im, ((i % cols) * w, (i // cols) * h))
        out = outdir / f"{name}.png"
        sheet.save(out)
        print(f"{name}: {dur:.1f}s -> {out}")


def join(src, out, names):
    import av

    paths = [Path(src) / f"{n}.mp4" for n in names]
    missing = [str(p) for p in paths if not p.exists()]
    if missing:
        sys.exit(f"missing: {', '.join(missing)}")
    oc = av.open(str(out), "w")
    ost = None
    offset = Fraction(0)  # seconds added to every timestamp of the current input
    last_dts = None  # seconds, of the last packet written
    total = Fraction(0)
    for p in paths:
        with av.open(str(p)) as ic:
            ist = ic.streams.video[0]
            tb = ist.time_base
            if ost is None:
                ost = oc.add_stream_from_template(ist)
            pkts = [k for k in ic.demux(ist) if k.dts is not None]
            if not pkts:
                continue
            tb = Fraction(tb.numerator, tb.denominator)
            rate = ist.average_rate
            frame = Fraction(rate.denominator, rate.numerator) if rate else Fraction(1, 60)
            first_dts = pkts[0].dts * tb
            if last_dts is not None:
                offset = max(total, last_dts + frame - first_dts)
            shift = round(offset / tb)
            end = Fraction(0)
            for k in pkts:
                end = max(end, (k.pts + (k.duration or 0)) * tb)
                k.pts += shift
                k.dts += shift
                k.stream = ost
                last_dts = k.dts * tb
                oc.mux(k)
            total = offset + end
    oc.close()
    print(f"{out}: {len(paths)} scenes, {float(total):.1f}s")


def info(video):
    import av

    with av.open(str(video)) as c:
        st = c.streams.video[0]
        dur = float(c.duration / 1_000_000) if c.duration else float(st.duration * st.time_base)
        rate = st.average_rate
        size = Path(video).stat().st_size
        print(f"{video}: {int(dur // 60)}m{dur % 60:04.1f}s ({dur:.1f} s), {st.codec_context.width}x"
              f"{st.codec_context.height}, {float(rate):.0f} fps, {size / 1e6:.1f} MB")


def frames(video, outdir, times):
    import av
    from PIL import Image, ImageDraw

    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    shots = []
    with av.open(str(video)) as c:
        st = c.streams.video[0]
        for t in sorted(float(x) for x in times):
            c.seek(int(t / st.time_base), stream=st, backward=True, any_frame=False)
            for f in c.decode(st):
                if f.time is not None and f.time >= t - 1e-3:
                    out = outdir / f"{Path(video).stem}_{t:07.1f}s.png"
                    im = f.to_image()
                    im.save(out)
                    shots.append((t, im))
                    print(out)
                    break
    if not shots:
        return
    # One image holding every frame, a third of full size, so a single look checks the order of the scenes.
    w, h = shots[0][1].width // 3, shots[0][1].height // 3
    cols = min(4, len(shots))
    strip = Image.new("RGB", (w * cols, h * ((len(shots) + cols - 1) // cols)), "white")
    for i, (t, im) in enumerate(shots):
        im = im.resize((w, h))
        d = ImageDraw.Draw(im)
        label = f"{t:.1f}s"
        lw = d.textlength(label) + 8
        d.rectangle([w - lw, 0, w, 16], fill="black")
        d.text((w - lw + 4, 2), label, fill="yellow")
        d.rectangle([0, 0, w - 1, h - 1], outline="white")
        strip.paste(im, ((i % cols) * w, (i // cols) * h))
    out = outdir / f"{Path(video).stem}_strip.png"
    strip.save(out)
    print(out)


def main():
    cmd, *args = sys.argv[1:] or [""]
    if cmd == "scenes":
        print("\n".join(scenes(args[0])))
    elif cmd == "sheets":
        sheets(args[0], args[1], args[2:])
    elif cmd == "join":
        join(args[0], args[1], args[2:])
    elif cmd == "info":
        info(args[0])
    elif cmd == "frames":
        frames(args[0], args[1], args[2:])
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main()
