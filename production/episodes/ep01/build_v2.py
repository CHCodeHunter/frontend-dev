#!/usr/bin/env python3
"""Build EP01 v2: Ken Burns stills + dialogue + BGM -> vertical mp4."""

from __future__ import annotations

import asyncio
import subprocess
import wave
from pathlib import Path

import edge_tts

ROOT = Path("/workspace/production/episodes/ep01")
FRAMES = ROOT / "frames-v2"
AUDIO = ROOT / "audio-v2"
WORK = ROOT / "build-v2-tmp"
FINAL = ROOT / "final"
W, H, FPS = 1080, 1920, 30

# (file, duration_sec, zoom_end, panx, pany)  zoom starts at 1.0
SHOTS = [
    ("s01-candle.png", 4.0, 1.12, "iw/2-(iw/zoom/2)", "ih/2-(ih/zoom/2)"),
    ("s02-drink.png", 5.0, 1.10, "iw/2-(iw/zoom/2)+20", "ih/2-(ih/zoom/2)"),
    ("s03-collapse.png", 7.0, 1.08, "iw/2-(iw/zoom/2)", "ih/2-(ih/zoom/2)+30"),
    ("s04-fakecry.png", 6.0, 1.14, "iw/2-(iw/zoom/2)", "ih/2-(ih/zoom/2)"),
    ("s05-disdain.png", 8.0, 1.10, "iw/2-(iw/zoom/2)-30", "ih/2-(ih/zoom/2)"),
    ("s06-shadow.png", 10.0, 1.16, "iw/2-(iw/zoom/2)", "ih/2-(ih/zoom/2)-40"),
    ("s07-blackeye.png", 5.0, 1.06, "iw/2-(iw/zoom/2)", "ih/2-(ih/zoom/2)"),
    ("s08-awake.png", 8.0, 1.18, "iw/2-(iw/zoom/2)", "ih/2-(ih/zoom/2)"),  # sharp push
    ("s09-offer.png", 9.0, 1.10, "iw/2-(iw/zoom/2)+25", "ih/2-(ih/zoom/2)"),
    ("s10-poison.png", 6.0, 1.20, "iw/2-(iw/zoom/2)", "ih/2-(ih/zoom/2)"),
    ("s11-coldlook.png", 8.0, 1.12, "iw/2-(iw/zoom/2)", "ih/2-(ih/zoom/2)"),
    ("s12-smile.png", 6.0, 1.15, "iw/2-(iw/zoom/2)", "ih/2-(ih/zoom/2)"),
    ("s13-push.png", 10.0, 1.10, "iw/2-(iw/zoom/2)", "ih/2-(ih/zoom/2)"),
    ("s14-shock.png", 6.0, 1.08, "iw/2-(iw/zoom/2)", "ih/2-(ih/zoom/2)+20"),
    ("s15-stare.png", 6.0, 1.14, "iw/2-(iw/zoom/2)", "ih/2-(ih/zoom/2)"),
]

# dialogue events: (start_sec, wav_name, text for subtitles)
LINES = [
    (0.4, "n1.wav", "前世，我跪着死在侯府寿宴上。"),
    (10.0, "w1.wav", "姐姐喝多了……"),
    (23.0, "c1.wav", "真是丢尽陆家的脸。"),
    (31.0, "n2.wav", "而我错过的那个人，终于来晚了。"),
    (54.5, "w2.wav", "姐姐，这杯贺寿酒，你先饮。"),
    (70.0, "q1.wav", "好啊。"),
    (83.0, "q2a.wav", "这酒烈，"),
    # 0.6s silence then punch line
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
    print("+", " ".join(cmd[:8]), "...")
    subprocess.run(cmd, check=True)


async def gen_tts() -> None:
    AUDIO.mkdir(parents=True, exist_ok=True)
    for name, text, voice, rate, pitch in TTS:
        out = AUDIO / name
        if out.exists() and out.stat().st_size > 1000:
            continue
        communicate = edge_tts.Communicate(text, voice, rate=rate, pitch=pitch)
        tmp = out.with_suffix(".mp3")
        await communicate.save(str(tmp))
        run(
            [
                "ffmpeg",
                "-y",
                "-i",
                str(tmp),
                "-ac",
                "1",
                "-ar",
                "48000",
                str(out),
            ]
        )
        tmp.unlink(missing_ok=True)


def wav_duration(path: Path) -> float:
    with wave.open(str(path), "rb") as w:
        return w.getnframes() / float(w.getframerate())


def make_bgm(total: float, path: Path) -> None:
    # tense low drone + mid pulse, strike near push line (~86s)
    # using ffmpeg sine/noise lavfi
    run(
        [
            "ffmpeg",
            "-y",
            "-f",
            "lavfi",
            "-i",
            f"sine=frequency=55:duration={total}",
            "-f",
            "lavfi",
            "-i",
            f"sine=frequency=110:duration={total}",
            "-f",
            "lavfi",
            "-i",
            f"sine=frequency=220:duration={total}",
            "-f",
            "lavfi",
            "-i",
            f"anoisesrc=color=pink:amplitude=0.015:duration={total}",
            "-filter_complex",
            (
                "[0:a]volume=0.12[a0];"
                "[1:a]volume=0.05[a1];"
                "[2:a]volume=0.02[a2];"
                "[3:a]highpass=f=200,volume=0.35[a3];"
                "[a0][a1][a2][a3]amix=inputs=4:duration=longest:dropout_transition=0,"
                "afade=t=in:st=0:d=1.5,afade=t=out:st={out_start}:d=2,"
                "volume='if(lt(t,45),0.7,if(lt(t,82),0.9,if(lt(t,86),0.35,1.1)))'"
            ).format(out_start=max(total - 2.2, 0)),
            "-ac",
            "2",
            "-ar",
            "48000",
            str(path),
        ]
    )
    # strike hit
    strike = WORK / "strike.wav"
    run(
        [
            "ffmpeg",
            "-y",
            "-f",
            "lavfi",
            "-i",
            "sine=frequency=180:duration=0.35",
            "-f",
            "lavfi",
            "-i",
            "anoisesrc=color=brown:amplitude=0.4:duration=0.25",
            "-filter_complex",
            "[0]volume=0.5[a];[1]volume=0.7[b];[a][b]amix=inputs=2,afade=t=out:st=0.05:d=0.3",
            str(strike),
        ]
    )
    mixed = path.with_name("bgm_mixed.wav")
    run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(path),
            "-i",
            str(strike),
            "-filter_complex",
            "[1]adelay=86200|86200,volume=1.4[s];[0][s]amix=inputs=2:duration=first:dropout_transition=0",
            str(mixed),
        ]
    )
    mixed.replace(path)


def ken_burns(img: Path, dur: float, zoom_end: float, x: str, y: str, out: Path) -> None:
    frames = max(int(dur * FPS), 1)
    # scale to cover vertical canvas then zoompan
    vf = (
        f"scale={W}:{H}:force_original_aspect_ratio=increase,"
        f"crop={W}:{H},"
        f"zoompan=z='min(1+({zoom_end}-1)*on/{frames},{zoom_end})':"
        f"x='{x}':y='{y}':d={frames}:s={W}x{H}:fps={FPS},"
        f"fps={FPS},format=yuv420p"
    )
    run(
        [
            "ffmpeg",
            "-y",
            "-loop",
            "1",
            "-i",
            str(img),
            "-vf",
            vf,
            "-t",
            f"{dur:.3f}",
            "-an",
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-crf",
            "18",
            str(out),
        ]
    )


def end_card(dur: float, out: Path) -> None:
    # black with centered white Chinese text via drawtext
    font = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    # try Noto CJK
    for cand in [
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
        font,
    ]:
        if Path(cand).exists():
            font = cand
            break
    vf = (
        f"color=c=black:s={W}x{H}:d={dur},"
        f"drawtext=fontfile={font}:text='今生，换你们跪。':"
        f"fontsize=64:fontcolor=white:x=(w-text_w)/2:y=(h-text_h)/2"
    )
    run(
        [
            "ffmpeg",
            "-y",
            "-f",
            "lavfi",
            "-i",
            vf,
            "-t",
            f"{dur:.3f}",
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-preset",
            "veryfast",
            "-crf",
            "18",
            str(out),
        ]
    )


def burn_subs(video: Path, out: Path) -> None:
    font = "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc"
    for cand in [
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
    ]:
        if Path(cand).exists():
            font = cand
            break

    # build ass file
    ass = WORK / "subs.ass"
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
    events = []
    # series title first 1.8s
    events.append("Dialogue: 0,0:00:00.20,0:00:01.80,Default,,0,0,0,,{\\fs40}侯府嫡女：今生换你们跪")
    for start, wav, text in LINES:
        dur = wav_duration(AUDIO / wav)
        end = start + dur + 0.15
        events.append(
            f"Dialogue: 0,{fmt(start)},{fmt(end)},Default,,0,0,0,,{text}"
        )
    # end card dialogue spoken slightly after black starts (104.3)
    events.append("Dialogue: 0,0:01:44.40,0:01:48.50,Default,,0,0,0,,今生，换你们跪。")
    ass.write_text(header + "\n".join(events) + "\n", encoding="utf-8")

    run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(video),
            "-vf",
            f"ass={ass}:fontsdir=/usr/share/fonts",
            "-c:a",
            "copy",
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-crf",
            "18",
            str(out),
        ]
    )


def fmt(t: float) -> str:
    h = int(t // 3600)
    m = int((t % 3600) // 60)
    s = t % 60
    return f"{h:d}:{m:02d}:{s:05.2f}"


def mix_audio(total: float, out: Path) -> None:
    # delay each line onto timeline and mix with bgm
    inputs = ["-i", str(WORK / "bgm.wav")]
    filters = []
    labels = ["[0:a]"]
    for i, (start, wav, _) in enumerate(LINES, start=1):
        inputs += ["-i", str(AUDIO / wav)]
        ms = int(start * 1000)
        filters.append(f"[{i}]adelay={ms}|{ms},volume=1.35[v{i}]")
        labels.append(f"[v{i}]")
    # end line
    inputs += ["-i", str(AUDIO / "end.wav")]
    end_i = len(LINES) + 1
    filters.append(f"[{end_i}]adelay=104400|104400,volume=1.25[vend]")
    labels.append("[vend]")
    # bgm quieter under dialogue
    filters.insert(0, "[0:a]volume=0.45[bg]")
    labels[0] = "[bg]"
    n = len(labels)
    filters.append(
        f"{''.join(labels)}amix=inputs={n}:duration=first:dropout_transition=0:normalize=0[aout]"
    )
    cmd = [
        "ffmpeg",
        "-y",
        *inputs,
        "-filter_complex",
        ";".join(filters),
        "-map",
        "[aout]",
        "-t",
        f"{total:.3f}",
        "-ac",
        "2",
        "-ar",
        "48000",
        str(out),
    ]
    run(cmd)


def main() -> None:
    WORK.mkdir(parents=True, exist_ok=True)
    FINAL.mkdir(parents=True, exist_ok=True)
    asyncio.run(gen_tts())

    clip_paths = []
    for i, (name, dur, zend, x, y) in enumerate(SHOTS, start=1):
        out = WORK / f"clip_{i:02d}.mp4"
        ken_burns(FRAMES / name, dur, zend, x, y, out)
        clip_paths.append(out)

    end = WORK / "clip_end.mp4"
    end_card(6.0, end)
    clip_paths.append(end)

    total = sum(d for _, d, *_ in SHOTS) + 6.0
    concat_list = WORK / "concat.txt"
    concat_list.write_text(
        "".join(f"file '{p}'\n" for p in clip_paths), encoding="utf-8"
    )
    silent_video = WORK / "video_silent.mp4"
    run(
        [
            "ffmpeg",
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(concat_list),
            "-c",
            "copy",
            str(silent_video),
        ]
    )

    make_bgm(total, WORK / "bgm.wav")
    mix_audio(total, WORK / "mix.wav")

    with_audio = WORK / "video_audio.mp4"
    run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(silent_video),
            "-i",
            str(WORK / "mix.wav"),
            "-map",
            "0:v",
            "-map",
            "1:a",
            "-c:v",
            "copy",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-shortest",
            str(with_audio),
        ]
    )

    out_mp4 = FINAL / "ep01-v2.mp4"
    burn_subs(with_audio, out_mp4)

    # cover from s13-push with title
    font = "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc"
    for cand in [
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
    ]:
        if Path(cand).exists():
            font = cand
            break
    cover = FINAL / "cover-v2.png"
    run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(FRAMES / "s13-push.png"),
            "-vf",
            (
                f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},"
                f"drawbox=x=0:y=h-280:w=w:h=280:color=black@0.55:t=fill,"
                f"drawtext=fontfile={font}:text='重生后，她把毒酒推了回去':"
                f"fontsize=52:fontcolor=white:x=(w-text_w)/2:y=h-180"
            ),
            str(cover),
        ]
    )

    # also refresh primary publish aliases
    run(["cp", str(out_mp4), str(FINAL / "ep01.mp4")])
    run(["cp", str(cover), str(FINAL / "cover.png")])
    print(f"DONE total≈{total}s -> {out_mp4}")


if __name__ == "__main__":
    main()
