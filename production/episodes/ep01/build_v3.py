#!/usr/bin/env python3
"""Build EP01 v3: motion-interpolated action beats + atmosphere -> vertical mp4.

Each key beat ships two drawn poses (A and B). Motion compensation between them
produces real in-between movement instead of a pan across one frozen image.
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
XFADE = 0.3
BLINK = 4 / 30  # a real blink is a few frames, not a slow dissolve

FONT = "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc"

# Interpolation smears when two poses sit far apart, so wide moves are cut, not
# morphed; morphs stay short so the action reads as a beat rather than a melt.
# name, A, B, motion, move_dur, duration, zoom_end, pan_x, pan_y, shake, flicker
SHOTS = [
    ("candle", "s01-candle.png", None, "hold", 0.0, 4.0, 1.10, 0, 0, 0, 0.020),
    ("drink", "s02-drink.png", "s02b-drink.png", "morph", 0.45, 5.0, 1.08, 20, 0, 0, 0.014),
    ("collapse", "s03-collapse.png", "s03b-collapse.png", "cut", 0.0, 7.0, 1.06, 0, 30, 4, 0.012),
    ("fakecry", "s04-fakecry.png", "s04b-fakecry.png", "blink", 0.0, 6.0, 1.12, 0, 0, 0, 0.010),
    ("disdain", "s05-disdain.png", "s05b-disdain.png", "morph", 0.40, 8.0, 1.08, -30, 0, 0, 0.012),
    ("shadow", "s06-shadow.png", None, "hold", 0.0, 10.0, 1.14, 0, -40, 0, 0.016),
    ("blackeye", "s07-blackeye.png", None, "hold", 0.0, 5.0, 1.05, 0, 0, 2, 0.008),
    ("awake", "s07-blackeye.png", "s08-awake.png", "cut", 0.0, 8.0, 1.16, 0, 0, 6, 0.010),
    ("offer", "s09-offer.png", "s09b-offer.png", "morph", 0.45, 9.0, 1.08, 25, 0, 0, 0.012),
    ("poison", "s10-poison.png", None, "hold", 0.0, 6.0, 1.18, 0, 0, 0, 0.014),
    ("coldlook", "s11-coldlook.png", "s11b-coldlook.png", "morph", 0.35, 8.0, 1.10, 0, 0, 0, 0.010),
    ("smile", "s12-smile.png", "s12b-smile.png", "morph", 0.30, 6.0, 1.12, 0, 0, 0, 0.008),
    ("push", "s13-push.png", "s13b-push.png", "morph", 0.50, 10.0, 1.08, 0, 0, 4, 0.010),
    ("shock", "s14-shock.png", "s14b-shock.png", "cut", 0.0, 6.0, 1.06, 0, 20, 4, 0.010),
    ("stare", "s15-stare.png", "s15b-stare.png", "blink", 0.0, 6.0, 1.12, 0, 0, 0, 0.010),
]

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
    print("+", " ".join(str(c) for c in cmd[:6]), "...", flush=True)
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def wav_duration(path: Path) -> float:
    with wave.open(str(path), "rb") as w:
        return w.getnframes() / float(w.getframerate())


async def gen_tts() -> None:
    """Synthesize any missing dialogue stem; committed stems are reused as-is."""
    AUDIO.mkdir(parents=True, exist_ok=True)
    missing = [t for t in TTS if not (AUDIO / t[0]).exists() or (AUDIO / t[0]).stat().st_size <= 1000]
    if not missing:
        return
    import edge_tts

    for name, text, voice, rate, pitch in missing:
        out = AUDIO / name
        tmp = out.with_suffix(".mp3")
        await edge_tts.Communicate(text, voice, rate=rate, pitch=pitch).save(str(tmp))
        run(["ffmpeg", "-y", "-i", str(tmp), "-ac", "1", "-ar", "48000", str(out)])
        tmp.unlink(missing_ok=True)


def morph_clip(a: Path, b: Path, move_dur: float, out: Path) -> float:
    """Motion-compensated move from A to B, held briefly at both ends.

    A 4-frame A,A,B,B source puts the travel in the middle third, so the clip
    runs three times the requested move. Frame averaging adds motion blur, which
    both reads as speed and hides interpolation smear.
    """
    total = move_dur * 3
    seq = WORK / f"seq_{out.stem}"
    if seq.exists():
        shutil.rmtree(seq)
    seq.mkdir(parents=True)
    for idx, src in enumerate([a, a, b, b], start=1):
        shutil.copy(src, seq / f"f_{idx:02d}.png")
    run(
        [
            "ffmpeg", "-y",
            "-framerate", f"{4 / total:.4f}",
            "-start_number", "1",
            "-i", str(seq / "f_%02d.png"),
            "-vf",
            "minterpolate=fps=60:mi_mode=mci:mc_mode=aobmc:me_mode=bidir:vsbmc=1,"
            "tmix=frames=3:weights='1 1 1',fps=30,"
            f"scale={SRC_W}:{SRC_H},format=yuv420p",
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "16",
            str(out),
        ]
    )
    return total


def still_clip(img: Path, dur: float, out: Path) -> None:
    run(
        [
            "ffmpeg", "-y", "-loop", "1", "-i", str(img),
            "-t", f"{dur:.3f}", "-r", str(FPS),
            "-vf", f"scale={SRC_W}:{SRC_H},format=yuv420p",
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "16",
            str(out),
        ]
    )


def build_beat(name: str, idx: int, a: Path, b: Path | None, motion: str,
               move_dur: float, dur: float, out: Path) -> None:
    """Assemble one beat's raw footage at source resolution."""
    if motion == "hold" or b is None:
        still_clip(a, dur, out)
        return

    parts: list[Path] = []

    def still(src: Path, seconds: float, tag: str) -> None:
        path = WORK / f"part_{idx:02d}_{tag}.mp4"
        still_clip(src, seconds, path)
        parts.append(path)

    if motion == "blink":
        # close-open-close-open, hard cuts, spaced unevenly so it reads as alive
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
        morph = WORK / f"morph_{idx:02d}_{name}.mp4"
        span = morph_clip(a, b, move_dur, morph)
        lead = max((dur - span) * 0.42, 0.2)
        still(a, lead, "a1")
        parts.append(morph)
        still(b, max(dur - span - lead, 0.2), "b1")

    concat(parts, out)


def concat(parts: list[Path], out: Path) -> None:
    listing = out.with_suffix(".txt")
    listing.write_text("".join(f"file '{p}'\n" for p in parts), encoding="utf-8")
    run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(listing), "-c", "copy", str(out)])


def finish_shot(raw: Path, dur: float, zoom: float, px: int, py: int,
                shake: int, flicker: float, out: Path) -> None:
    """Frame the raw beat vertically, add drift, handheld sway, candle flicker, grain."""
    frames = max(int(dur * FPS), 1)
    big_w, big_h = int(W * 1.5), int(H * 1.5)
    zx = f"iw/2-(iw/zoom/2)+{px}*on/{frames}"
    zy = f"ih/2-(ih/zoom/2)+{py}*on/{frames}"
    if shake:
        zx += f"+{shake}*sin(on/4.5)"
        zy += f"+{shake}*sin(on/6.1)"
    vf = (
        f"tpad=stop_mode=clone:stop_duration=6,fps={FPS},"
        f"scale={big_w}:{big_h}:force_original_aspect_ratio=increase,"
        f"crop={big_w}:{big_h},"
        f"zoompan=z='min(1+({zoom}-1)*on/{frames},{zoom})':x='{zx}':y='{zy}':"
        f"d=1:s={W}x{H}:fps={FPS},"
        f"eq=brightness='{flicker}*sin(2*PI*t*2.7)+{flicker * 0.6}*sin(2*PI*t*5.3)':eval=frame,"
        f"noise=alls=4:allf=t,format=yuv420p"
    )
    run(
        [
            "ffmpeg", "-y", "-i", str(raw), "-vf", vf, "-t", f"{dur:.3f}",
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", str(out),
        ]
    )


def end_card(dur: float, out: Path) -> None:
    run(
        [
            "ffmpeg", "-y", "-f", "lavfi",
            "-i", f"color=c=black:s={W}x{H}:r={FPS}:d={dur}",
            "-vf",
            f"drawtext=fontfile={FONT}:text='今生，换你们跪。':"
            f"fontsize=64:fontcolor=white:x=(w-text_w)/2:y=(h-text_h)/2,"
            f"noise=alls=3:allf=t,format=yuv420p",
            "-t", f"{dur:.3f}", "-r", str(FPS),
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", str(out),
        ]
    )


def xfade_chain(clips: list[Path], durations: list[float], out: Path) -> None:
    """Dissolve between beats; the rebirth beat gets a white flash instead."""
    inputs: list[str] = []
    for clip in clips:
        inputs += ["-i", str(clip)]
    filters: list[str] = []
    label = "0:v"
    offset = 0.0
    for i in range(1, len(clips)):
        offset += durations[i - 1] - XFADE
        transition = "fadewhite" if clips[i].stem.endswith("awake") else "fade"
        new_label = f"x{i}"
        filters.append(
            f"[{label}][{i}:v]xfade=transition={transition}:"
            f"duration={XFADE}:offset={offset:.3f}[{new_label}]"
        )
        label = new_label
    run(
        [
            "ffmpeg", "-y", *inputs,
            "-filter_complex", ";".join(filters),
            "-map", f"[{label}]",
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
            "-pix_fmt", "yuv420p", str(out),
        ]
    )


def make_bgm(total: float, path: Path) -> None:
    run(
        [
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
        ]
    )
    strike = WORK / "strike.wav"
    run(
        [
            "ffmpeg", "-y",
            "-f", "lavfi", "-i", "sine=frequency=180:duration=0.35",
            "-f", "lavfi", "-i", "anoisesrc=color=brown:amplitude=0.4:duration=0.25",
            "-filter_complex",
            "[0]volume=0.5[a];[1]volume=0.7[b];[a][b]amix=inputs=2,afade=t=out:st=0.05:d=0.3",
            str(strike),
        ]
    )
    mixed = path.with_name("bgm_mixed.wav")
    run(
        [
            "ffmpeg", "-y", "-i", str(path), "-i", str(strike),
            "-filter_complex",
            "[1]adelay=86200|86200,volume=1.4[s];"
            "[0][s]amix=inputs=2:duration=first:dropout_transition=0",
            str(mixed),
        ]
    )
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
    run(
        [
            "ffmpeg", "-y", *inputs, "-filter_complex", ";".join(filters),
            "-map", "[aout]", "-t", f"{total:.3f}", "-ac", "2", "-ar", "48000", str(out),
        ]
    )


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
    run(
        [
            "ffmpeg", "-y", "-i", str(video),
            "-vf", f"ass={ass}:fontsdir=/usr/share/fonts",
            "-c:a", "copy", "-c:v", "libx264", "-preset", "medium", "-crf", "23",
            "-maxrate", "6M", "-bufsize", "12M", "-profile:v", "high", "-level", "4.1",
            "-movflags", "+faststart",
            str(out),
        ]
    )


def build_cover(out: Path) -> None:
    run(
        [
            "ffmpeg", "-y", "-i", str(FRAMES / "s13-push.png"),
            "-vf",
            f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},"
            f"drawbox=x=0:y=ih-280:w=iw:h=280:color=black@0.55:t=fill,"
            f"drawtext=fontfile={FONT}:text='重生后，她把毒酒推了回去':"
            f"fontsize=52:fontcolor=white:x=(w-text_w)/2:y=h-180",
            "-frames:v", "1", "-update", "1", str(out),
        ]
    )


def main() -> None:
    WORK.mkdir(parents=True, exist_ok=True)
    FINAL.mkdir(parents=True, exist_ok=True)
    asyncio.run(gen_tts())

    clips: list[Path] = []
    durations: list[float] = []
    for idx, (name, a, b, motion, move_dur, dur, zoom, px, py, shake, flicker) in enumerate(SHOTS):
        # every clip after the first absorbs the dissolve overlap
        clip_dur = dur + (XFADE if idx else 0.0)
        raw = WORK / f"raw_{idx:02d}_{name}.mp4"
        build_beat(name, idx, FRAMES / a, FRAMES / b if b else None,
                   motion, move_dur, clip_dur, raw)

        out = WORK / f"clip_{idx:02d}_{name}.mp4"
        finish_shot(raw, clip_dur, zoom, px, py, shake, flicker, out)
        clips.append(out)
        durations.append(clip_dur)

    end = WORK / "clip_99_end.mp4"
    end_card(6.0 + XFADE, end)
    clips.append(end)
    durations.append(6.0 + XFADE)

    total = sum(shot[5] for shot in SHOTS) + 6.0
    silent = WORK / "video_silent.mp4"
    xfade_chain(clips, durations, silent)

    make_bgm(total, WORK / "bgm.wav")
    mix_audio(total, WORK / "mix.wav")

    with_audio = WORK / "video_audio.mp4"
    run(
        [
            "ffmpeg", "-y", "-i", str(silent), "-i", str(WORK / "mix.wav"),
            "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac",
            "-b:a", "192k", "-t", f"{total:.3f}", str(with_audio),
        ]
    )

    out_mp4 = FINAL / "ep01-v3.mp4"
    burn_subs(with_audio, out_mp4)
    cover = FINAL / "cover-v3.png"
    build_cover(cover)
    shutil.copy(out_mp4, FINAL / "ep01.mp4")
    shutil.copy(cover, FINAL / "cover.png")
    print(f"DONE total={total}s -> {out_mp4}")


if __name__ == "__main__":
    main()
