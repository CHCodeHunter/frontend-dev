#!/usr/bin/env python3
"""Build EP01 v3: motion beats cut like drama coverage -> vertical mp4.

Two things separate this from a slideshow. Beats carry real movement: each key
pose ships an A and B drawing, and the travel between them is either motion
interpolated (small moves) or hard cut (wide moves, which interpolation smears).
And beats are covered from several framings pulled out of the same plate, cut
hard, so the edit averages a cut every couple of seconds instead of one long
push per image.
"""

from __future__ import annotations

import asyncio
import shutil
import subprocess
import wave
from pathlib import Path

ROOT = Path("/workspace/production/episodes/ep01")
FRAMES = ROOT / "frames-v3"
AUDIO = ROOT / "audio-v2"
WORK = ROOT / "build-v3-tmp"
FINAL = ROOT / "final"
W, H, FPS = 1080, 1920, 30
SRC_W, SRC_H = 1536, 1024
BLINK = 4 / 30  # a real blink is a few frames, not a slow dissolve

# the plate is scaled to cover the vertical frame, leaving horizontal slack to
# choose what the "camera" is pointed at
BIG_W, BIG_H = int(W * 1.5), int(H * 1.5)
# past this the plate is upscaled far enough that faces go soft
MAX_ZOOM = 1.5

FONT = "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc"

# framing: (share of beat, zoom start, zoom end, pan x, pan y, shake)
# pan values are in output pixels; positive x looks right, positive y looks down
SHOTS: list[dict] = [
    dict(name="candle", a="s01-candle.png", b=None, motion="hold", move=0.0,
         dur=4.0, flicker=0.020, framings=[
             (0.55, 1.00, 1.06, -150, 0, 0),
             (0.45, 1.50, 1.60, -300, -200, 0),
         ]),
    dict(name="drink", a="s02-drink.png", b="s02b-drink.png", motion="morph", move=0.45,
         dur=5.0, flicker=0.014, framings=[
             (0.30, 1.00, 1.05, 100, 0, 0),
             (0.32, 1.35, 1.45, 250, -250, 0),
             (0.38, 1.15, 1.25, 200, -150, 0),
         ]),
    dict(name="collapse", a="s03-collapse.png", b="s03b-collapse.png", motion="cut", move=0.0,
         dur=7.0, flicker=0.012, framings=[
             (0.42, 1.00, 1.06, -200, 0, 0),
             (0.28, 1.50, 1.55, -320, -250, 5),
             (0.30, 1.15, 1.25, -150, 200, 3),
         ]),
    dict(name="fakecry", a="s04-fakecry.png", b="s04b-fakecry.png", motion="blink", move=0.0,
         dur=6.0, flicker=0.010, framings=[
             (0.45, 1.30, 1.35, -100, -150, 0),
             (0.25, 1.00, 1.05, 0, 0, 0),
             (0.30, 1.50, 1.60, -80, -200, 0),
         ]),
    dict(name="disdain", a="s05-disdain.png", b="s05b-disdain.png", motion="morph", move=0.40,
         dur=8.0, flicker=0.012, framings=[
             (0.36, 1.00, 1.06, 0, 0, 0),
             (0.20, 1.35, 1.40, -100, -250, 0),
             (0.44, 1.10, 1.20, -200, 0, 0),
         ]),
    dict(name="shadow", a="s06-shadow.png", b=None, motion="hold", move=0.0,
         dur=10.0, flicker=0.016, framings=[
             (0.35, 1.00, 1.08, 0, 0, 0),
             (0.30, 1.40, 1.50, 150, -200, 0),
             (0.35, 1.10, 1.25, -100, 150, 0),
         ]),
    dict(name="blackeye", a="s07-blackeye.png", b=None, motion="hold", move=0.0,
         dur=5.0, flicker=0.008, framings=[
             (0.50, 1.00, 1.05, 0, 0, 2),
             (0.50, 1.30, 1.40, 0, -100, 2),
         ]),
    dict(name="awake", a="s07-blackeye.png", b="s08-awake.png", motion="cut", move=0.0,
         dur=8.0, flicker=0.010, framings=[
             (0.42, 1.20, 1.30, 0, -100, 0),
             (0.25, 1.55, 1.60, 0, -150, 7),
             (0.33, 1.10, 1.20, 0, 0, 3),
         ]),
    dict(name="offer", a="s09-offer.png", b="s09b-offer.png", motion="morph", move=0.45,
         dur=9.0, flicker=0.012, framings=[
             (0.36, 1.00, 1.06, 150, 0, 0),
             (0.18, 1.45, 1.50, 300, 250, 0),
             (0.22, 1.30, 1.35, 250, -250, 0),
             (0.24, 1.10, 1.20, 100, 0, 0),
         ]),
    dict(name="poison", a="s10-poison.png", b=None, motion="hold", move=0.0,
         dur=6.0, flicker=0.014, framings=[
             (0.45, 1.20, 1.35, 0, 0, 0),
             (0.55, 1.60, 1.75, 50, 50, 0),
         ]),
    dict(name="coldlook", a="s11-coldlook.png", b="s11b-coldlook.png", motion="morph", move=0.35,
         dur=8.0, flicker=0.010, framings=[
             (0.365, 1.15, 1.20, 0, -150, 0),
             (0.150, 1.50, 1.55, 0, -200, 0),
             (0.240, 1.00, 1.08, 0, 0, 0),
             (0.245, 1.35, 1.45, 0, -180, 0),
         ]),
    dict(name="smile", a="s12-smile.png", b="s12b-smile.png", motion="morph", move=0.30,
         dur=6.0, flicker=0.008, framings=[
             (0.357, 1.20, 1.25, 0, 0, 0),
             (0.150, 1.60, 1.65, 0, 100, 0),
             (0.493, 1.30, 1.40, 0, 0, 0),
         ]),
    dict(name="push", a="s13-push.png", b="s13b-push.png", motion="morph", move=0.50,
         dur=10.0, flicker=0.010, framings=[
             (0.357, 1.00, 1.06, -100, 0, 0),
             (0.150, 1.50, 1.55, -50, 400, 4),
             (0.200, 1.35, 1.40, -250, -150, 0),
             (0.293, 1.10, 1.20, 0, 0, 0),
         ]),
    dict(name="shock", a="s14-shock.png", b="s14b-shock.png", motion="cut", move=0.0,
         dur=6.0, flicker=0.010, framings=[
             (0.42, 1.20, 1.25, -80, -100, 0),
             (0.25, 1.60, 1.65, -60, -150, 6),
             (0.33, 1.05, 1.15, 0, 0, 2),
         ]),
    dict(name="stare", a="s15-stare.png", b="s15b-stare.png", motion="blink", move=0.0,
         dur=6.0, flicker=0.010, framings=[
             (0.40, 1.15, 1.20, 0, -100, 0),
             (0.25, 1.50, 1.55, 0, -150, 0),
             (0.35, 1.05, 1.15, 0, 0, 0),
         ]),
]

# only time and consciousness shifts dissolve; everything else cuts
DISSOLVE_AFTER = {
    "disdain": ("fade", 0.5),
    "shadow": ("fade", 0.4),
    "blackeye": ("fadewhite", 0.25),
    "stare": ("fade", 0.4),
}
END_DUR = 6.0

LINES = [
    (0.4, "n1.wav", "前世，我跪着死在侯府寿宴上。"),
    (10.0, "w1.wav", "姐姐喝多了……"),
    (23.0, "c1.wav", "真是丢尽陆家的脸。"),
    (31.0, "n2.wav", "而我错过的那个人，终于来晚了。"),
    (54.5, "w2.wav", "姐姐，这杯贺寿酒，你先饮。"),
    (70.0, "q1.wav", "好啊。"),
    (83.0, "q2a.wav", "这酒烈，"),
    (86.2, "q2b.wav", "该你喝。"),
]

TTS = [
    ("n1.wav", "前世，我跪着死在侯府寿宴上。", "zh-CN-XiaoxiaoNeural", "-12%", "-4Hz"),
    ("n2.wav", "而我错过的那个人，终于来晚了。", "zh-CN-XiaoxiaoNeural", "-12%", "-4Hz"),
    ("w1.wav", "姐姐喝多了……", "zh-CN-XiaoxiaoNeural", "+8%", "+10Hz"),
    ("w2.wav", "姐姐，这杯贺寿酒，你先饮。", "zh-CN-XiaoxiaoNeural", "+6%", "+8Hz"),
    ("c1.wav", "真是丢尽陆家的脸。", "zh-CN-YunxiNeural", "+0%", "-2Hz"),
    ("q1.wav", "好啊。", "zh-CN-XiaoyiNeural", "-8%", "-6Hz"),
    ("q2a.wav", "这酒烈，", "zh-CN-XiaoyiNeural", "-10%", "-6Hz"),
    ("q2b.wav", "该你喝。", "zh-CN-XiaoyiNeural", "-12%", "-8Hz"),
    ("end.wav", "今生，换你们跪。", "zh-CN-XiaoyiNeural", "-10%", "-6Hz"),
]


def run(cmd: list[str]) -> None:
    print("+", " ".join(str(c) for c in cmd[:5]), "...", flush=True)
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def wav_duration(path: Path) -> float:
    with wave.open(str(path), "rb") as w:
        return w.getnframes() / float(w.getframerate())


async def gen_tts() -> None:
    """Synthesize any missing dialogue stem; committed stems are reused as-is."""
    AUDIO.mkdir(parents=True, exist_ok=True)
    missing = [t for t in TTS
               if not (AUDIO / t[0]).exists() or (AUDIO / t[0]).stat().st_size <= 1000]
    if not missing:
        return
    import edge_tts

    for name, text, voice, rate, pitch in missing:
        out = AUDIO / name
        tmp = out.with_suffix(".mp3")
        await edge_tts.Communicate(text, voice, rate=rate, pitch=pitch).save(str(tmp))
        run(["ffmpeg", "-y", "-i", str(tmp), "-ac", "1", "-ar", "48000", str(out)])
        tmp.unlink(missing_ok=True)


def still_clip(img: Path, dur: float, out: Path) -> None:
    run([
        "ffmpeg", "-y", "-loop", "1", "-i", str(img),
        "-t", f"{dur:.3f}", "-r", str(FPS),
        "-vf", f"scale={SRC_W}:{SRC_H},format=yuv420p",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "16", str(out),
    ])


def morph_clip(a: Path, b: Path, move: float, out: Path) -> float:
    """Motion-compensated move from A to B, held briefly at both ends.

    A 4-frame A,A,B,B source puts the travel in the middle third, so the clip
    runs three times the requested move. Frame averaging adds motion blur, which
    both reads as speed and hides interpolation smear.
    """
    total = move * 3
    seq = WORK / f"seq_{out.stem}"
    if seq.exists():
        shutil.rmtree(seq)
    seq.mkdir(parents=True)
    for idx, src in enumerate([a, a, b, b], start=1):
        shutil.copy(src, seq / f"f_{idx:02d}.png")
    run([
        "ffmpeg", "-y",
        "-framerate", f"{4 / total:.4f}", "-start_number", "1",
        "-i", str(seq / "f_%02d.png"),
        "-vf",
        "minterpolate=fps=60:mi_mode=mci:mc_mode=aobmc:me_mode=bidir:vsbmc=1,"
        "tmix=frames=3:weights='1 1 1',fps=30,"
        f"scale={SRC_W}:{SRC_H},format=yuv420p",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "16", str(out),
    ])
    return total


def concat(parts: list[Path], out: Path) -> None:
    listing = out.with_suffix(".txt")
    listing.write_text("".join(f"file '{p}'\n" for p in parts), encoding="utf-8")
    run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(listing),
         "-c", "copy", str(out)])


def build_plate(shot: dict, idx: int, dur: float, out: Path) -> None:
    """Render the beat's continuous action at source resolution."""
    a = FRAMES / shot["a"]
    b = FRAMES / shot["b"] if shot["b"] else None
    motion = shot["motion"]
    if motion == "hold" or b is None:
        still_clip(a, dur, out)
        return

    parts: list[Path] = []

    def still(src: Path, seconds: float, tag: str) -> None:
        path = WORK / f"part_{idx:02d}_{tag}.mp4"
        still_clip(src, seconds, path)
        parts.append(path)

    if motion == "blink":
        # close-open-close-open on hard cuts, spaced unevenly so it reads alive
        rest = dur - 2 * BLINK
        still(a, rest * 0.45, "a1")
        still(b, BLINK, "b1")
        still(a, rest * 0.30, "a2")
        still(b, BLINK, "b2")
        still(a, rest * 0.25, "a3")
    elif motion == "cut":
        still(a, dur * 0.42, "a1")
        still(b, dur * 0.58, "b1")
    else:
        morph = WORK / f"morph_{idx:02d}_{shot['name']}.mp4"
        span = morph_clip(a, b, shot["move"], morph)
        lead = max((dur - span) * 0.42, 0.2)
        still(a, lead, "a1")
        parts.append(morph)
        still(b, max(dur - span - lead, 0.2), "b1")

    concat(parts, out)


def render_framing(plate: Path, start: float, dur: float, z0: float, z1: float,
                   pan_x: int, pan_y: int, shake: int, flicker: float,
                   out: Path) -> None:
    """Cut one camera setup out of the plate: reframe, drift, sway, flicker, grain."""
    frames = max(int(dur * FPS), 1)
    z0, z1 = min(z0, MAX_ZOOM), min(z1, MAX_ZOOM)
    crop_x = f"max(0,min(in_w-{BIG_W},(in_w-{BIG_W})/2+{int(pan_x * 1.5)}))"
    sway_x = f"+{shake}*sin(on/4.5)" if shake else ""
    sway_y = f"+{shake}*sin(on/6.1)" if shake else ""
    zoom = f"{z0}+({z1}-{z0})*on/{frames}"
    zx = f"max(0,min(iw-iw/zoom,iw/2-(iw/zoom/2){sway_x}))"
    zy = f"max(0,min(ih-ih/zoom,ih/2-(ih/zoom/2)+{int(pan_y * 1.5)}{sway_y}))"
    vf = (
        f"trim=start={start:.3f}:duration={dur:.3f},setpts=PTS-STARTPTS,"
        f"tpad=stop_mode=clone:stop_duration=6,fps={FPS},"
        f"scale=-2:{BIG_H},crop={BIG_W}:{BIG_H}:x='{crop_x}':y=0,"
        f"zoompan=z='{zoom}':x='{zx}':y='{zy}':d=1:s={W}x{H}:fps={FPS},"
        "unsharp=5:5:0.7:5:5:0.0,"
        f"eq=brightness='{flicker}*sin(2*PI*t*2.7)+{flicker * 0.6}*sin(2*PI*t*5.3)':"
        "eval=frame,"
        "noise=alls=4:allf=t,format=yuv420p"
    )
    run([
        "ffmpeg", "-y", "-i", str(plate), "-vf", vf, "-t", f"{dur:.3f}",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", str(out),
    ])


def end_card(dur: float, out: Path) -> None:
    run([
        "ffmpeg", "-y", "-f", "lavfi",
        "-i", f"color=c=black:s={W}x{H}:r={FPS}:d={dur}",
        "-vf",
        f"drawtext=fontfile={FONT}:text='今生，换你们跪。':"
        "fontsize=64:fontcolor=white:x=(w-text_w)/2:y=(h-text_h)/2,"
        "noise=alls=3:allf=t,format=yuv420p",
        "-t", f"{dur:.3f}", "-r", str(FPS),
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", str(out),
    ])


def xfade_runs(runs: list[Path], durations: list[float],
               transitions: list[tuple[str, float]], out: Path) -> None:
    inputs: list[str] = []
    for clip in runs:
        inputs += ["-i", str(clip)]
    filters: list[str] = []
    label = "0:v"
    offset = 0.0
    for i in range(1, len(runs)):
        kind, span = transitions[i - 1]
        offset += durations[i - 1] - span
        new_label = f"x{i}"
        filters.append(
            f"[{label}][{i}:v]xfade=transition={kind}:"
            f"duration={span}:offset={offset:.3f}[{new_label}]"
        )
        label = new_label
    run([
        "ffmpeg", "-y", *inputs, "-filter_complex", ";".join(filters),
        "-map", f"[{label}]",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
        "-pix_fmt", "yuv420p", str(out),
    ])


def make_bgm(total: float, path: Path) -> None:
    run([
        "ffmpeg", "-y",
        "-f", "lavfi", "-i", f"sine=frequency=55:duration={total}",
        "-f", "lavfi", "-i", f"sine=frequency=110:duration={total}",
        "-f", "lavfi", "-i", f"sine=frequency=220:duration={total}",
        "-f", "lavfi", "-i", f"anoisesrc=color=pink:amplitude=0.015:duration={total}",
        "-filter_complex",
        "[0:a]volume=0.12[a0];[1:a]volume=0.05[a1];[2:a]volume=0.02[a2];"
        "[3:a]highpass=f=200,volume=0.35[a3];"
        "[a0][a1][a2][a3]amix=inputs=4:duration=longest:dropout_transition=0,"
        f"afade=t=in:st=0:d=1.5,afade=t=out:st={max(total - 2.2, 0):.2f}:d=2,"
        "volume='if(lt(t,45),0.7,if(lt(t,82),0.9,if(lt(t,86),0.35,1.1)))'",
        "-ac", "2", "-ar", "48000", str(path),
    ])
    strike = WORK / "strike.wav"
    run([
        "ffmpeg", "-y",
        "-f", "lavfi", "-i", "sine=frequency=180:duration=0.35",
        "-f", "lavfi", "-i", "anoisesrc=color=brown:amplitude=0.4:duration=0.25",
        "-filter_complex",
        "[0]volume=0.5[a];[1]volume=0.7[b];[a][b]amix=inputs=2,afade=t=out:st=0.05:d=0.3",
        str(strike),
    ])
    mixed = path.with_name("bgm_mixed.wav")
    run([
        "ffmpeg", "-y", "-i", str(path), "-i", str(strike),
        "-filter_complex",
        "[1]adelay=86200|86200,volume=1.4[s];"
        "[0][s]amix=inputs=2:duration=first:dropout_transition=0",
        str(mixed),
    ])
    mixed.replace(path)


def mix_audio(total: float, out: Path) -> None:
    inputs = ["-i", str(WORK / "bgm.wav")]
    filters = ["[0:a]volume=0.45[bg]"]
    labels = ["[bg]"]
    for i, (start, wav, _) in enumerate(LINES, start=1):
        inputs += ["-i", str(AUDIO / wav)]
        ms = int(start * 1000)
        filters.append(f"[{i}]adelay={ms}|{ms},volume=1.35[v{i}]")
        labels.append(f"[v{i}]")
    inputs += ["-i", str(AUDIO / "end.wav")]
    end_i = len(LINES) + 1
    filters.append(f"[{end_i}]adelay=104400|104400,volume=1.25[vend]")
    labels.append("[vend]")
    filters.append(
        f"{''.join(labels)}amix=inputs={len(labels)}:duration=first:"
        "dropout_transition=0:normalize=0[aout]"
    )
    run([
        "ffmpeg", "-y", *inputs, "-filter_complex", ";".join(filters),
        "-map", "[aout]", "-t", f"{total:.3f}", "-ac", "2", "-ar", "48000", str(out),
    ])


def fmt(t: float) -> str:
    return f"{int(t // 3600):d}:{int((t % 3600) // 60):02d}:{t % 60:05.2f}"


def burn_subs(video: Path, out: Path) -> None:
    header = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Sans,54,&H00FFFFFF,&H000000FF,&H00000000,&H80000000,0,0,0,0,100,100,0,0,1,3,0,2,40,40,160,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    events = [
        "Dialogue: 0,0:00:00.20,0:00:01.80,Default,,0,0,0,,{\\fs40}侯府嫡女：今生换你们跪"
    ]
    for start, wav, text in LINES:
        end = start + wav_duration(AUDIO / wav) + 0.15
        events.append(f"Dialogue: 0,{fmt(start)},{fmt(end)},Default,,0,0,0,,{text}")
    events.append("Dialogue: 0,0:01:44.40,0:01:48.50,Default,,0,0,0,,今生，换你们跪。")
    ass = WORK / "subs.ass"
    ass.write_text(header + "\n".join(events) + "\n", encoding="utf-8")
    run([
        "ffmpeg", "-y", "-i", str(video),
        "-vf", f"ass={ass}:fontsdir=/usr/share/fonts",
        "-c:a", "copy", "-c:v", "libx264", "-preset", "medium", "-crf", "23",
        "-maxrate", "6M", "-bufsize", "12M", "-profile:v", "high", "-level", "4.1",
        "-movflags", "+faststart", str(out),
    ])


def build_cover(out: Path) -> None:
    run([
        "ffmpeg", "-y", "-i", str(FRAMES / "s13-push.png"),
        "-vf",
        f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},"
        "drawbox=x=0:y=ih-280:w=iw:h=280:color=black@0.55:t=fill,"
        f"drawtext=fontfile={FONT}:text='重生后，她把毒酒推了回去':"
        "fontsize=52:fontcolor=white:x=(w-text_w)/2:y=h-180",
        "-frames:v", "1", "-update", "1", str(out),
    ])


def main() -> None:
    WORK.mkdir(parents=True, exist_ok=True)
    FINAL.mkdir(parents=True, exist_ok=True)
    asyncio.run(gen_tts())

    # Group beats into runs of hard cuts; runs are joined by the few dissolves.
    runs: list[list[Path]] = [[]]
    run_transitions: list[tuple[str, float]] = []
    pending_extra = 0.0
    cut_count = 0

    for idx, shot in enumerate(SHOTS):
        # a run that follows a dissolve absorbs the overlap it will lose
        dur = shot["dur"] + pending_extra
        pending_extra = 0.0
        plate = WORK / f"plate_{idx:02d}_{shot['name']}.mp4"
        build_plate(shot, idx, dur, plate)

        cursor = 0.0
        shares = shot["framings"]
        for j, (share, z0, z1, px, py, shake) in enumerate(shares):
            seg_dur = dur * share if j < len(shares) - 1 else dur - cursor
            seg = WORK / f"seg_{idx:02d}_{j}_{shot['name']}.mp4"
            render_framing(plate, cursor, seg_dur, z0, z1, px, py, shake,
                           shot["flicker"], seg)
            runs[-1].append(seg)
            cursor += seg_dur
            cut_count += 1

        if shot["name"] in DISSOLVE_AFTER:
            kind, span = DISSOLVE_AFTER[shot["name"]]
            run_transitions.append((kind, span))
            pending_extra = span
            runs.append([])

    end = WORK / "seg_99_end.mp4"
    end_card(END_DUR + pending_extra, end)
    runs[-1].append(end)

    joined: list[Path] = []
    durations: list[float] = []
    for i, segs in enumerate(runs):
        target = WORK / f"run_{i:02d}.mp4"
        if len(segs) == 1:
            shutil.copy(segs[0], target)
        else:
            concat(segs, target)
        joined.append(target)
        durations.append(float(subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=nw=1:nk=1", str(target)],
            capture_output=True, text=True, check=True).stdout.strip()))

    total = sum(s["dur"] for s in SHOTS) + END_DUR
    silent = WORK / "video_silent.mp4"
    xfade_runs(joined, durations, run_transitions, silent)

    make_bgm(total, WORK / "bgm.wav")
    mix_audio(total, WORK / "mix.wav")

    with_audio = WORK / "video_audio.mp4"
    run([
        "ffmpeg", "-y", "-i", str(silent), "-i", str(WORK / "mix.wav"),
        "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac",
        "-b:a", "192k", "-t", f"{total:.3f}", str(with_audio),
    ])

    out_mp4 = FINAL / "ep01-v3.mp4"
    burn_subs(with_audio, out_mp4)
    cover = FINAL / "cover-v3.png"
    build_cover(cover)
    shutil.copy(out_mp4, FINAL / "ep01.mp4")
    shutil.copy(cover, FINAL / "cover.png")
    print(f"DONE {total}s, {cut_count + 1} cuts -> {out_mp4}")


if __name__ == "__main__":
    main()
