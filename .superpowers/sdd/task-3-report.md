# Task 3 Report: EP01 逐镜表 + 关键帧

## Deliverables

- Created `production/episodes/ep01/shot-list.md` exactly from the brief.
- Created 8 key frames:
  - `production/episodes/ep01/frames/shot-01.png`
  - `production/episodes/ep01/frames/shot-02.png`
  - `production/episodes/ep01/frames/shot-03.png`
  - `production/episodes/ep01/frames/shot-04.png`
  - `production/episodes/ep01/frames/shot-05.png`
  - `production/episodes/ep01/frames/shot-06.png`
  - `production/episodes/ep01/frames/shot-07.png`
  - `production/episodes/ep01/frames/shot-08.png`

## Visual Reference Use

- Used `/workspace/production/characters/shen-qingning/lock.png` for heroine consistency across shots 01, 02, 03, 05, 06, 07, 08.
- Used `/workspace/production/characters/shen-waner/lock.png` for shots 02, 06, 08.
- Used `/workspace/production/characters/lu-chengyan/lock.png` for shot 03.
- Used `/workspace/production/characters/xie-linyuan/lock.png` for shot 04, with the male lead kept as a far-background corridor figure.

## Acceptance Checklist

- [x] 8 个 shot 文件都存在
- [x] 女主脸与 lock.png 一致（不像换人）
- [x] shot-04 男主仅远影，不抢戏
- [x] shot-08 可直接当封面候选
- [x] 无现代元素/崩手/水印

## Verification

Command run:

```bash
python3 - <<'PY'
from pathlib import Path
import struct
base = Path('production/episodes/ep01')
expected = '''# EP01 跪着死，睁眼活（目标 75s）

系列：《侯府嫡女：今生换你们跪》
封面标题：重生后，她把毒酒推了回去

| 镜号 | 时长 | 画面文件 | 画面要点 | 对白 |
|------|------|----------|----------|------|
| 1 | 0–3s | frames/shot-01.png | 红烛+毒酒入喉 | 旁白：前世，我跪着死在侯府寿宴上。 |
| 2 | 3–10s | frames/shot-02.png | 女主跪地吐血，继妹假哭 | 沈婉儿：姐姐喝多了…… |
| 3 | 10–18s | frames/shot-03.png | 陆承晏嫌恶后退 | 陆承晏：真是丢尽陆家的脸。 |
| 4 | 18–28s | frames/shot-04.png | 廊下男主远影 | 旁白：而我错过的那个人，终于来晚了。 |
| 5 | 28–35s | frames/shot-05.png | 猛然睁眼重生 | （呼吸，无对白） |
| 6 | 35–48s | frames/shot-06.png | 继妹端酒 | 沈婉儿：姐姐，这杯贺寿酒，你先饮。 |
| 7 | 48–60s | frames/shot-07.png | 看酒/毒砂/冷笑 | 沈清宁：好啊。 |
| 8 | 60–75s | frames/shot-08.png | 推回酒盏嘴角特写 | 沈清宁：这酒烈，该你喝。 |

结尾字幕：今生，换你们跪。
'''
actual = (base/'shot-list.md').read_text(encoding='utf-8')
print('shot-list exact:', actual == expected)
missing=[]
for i in range(1,9):
    p = base/'frames'/f'shot-{i:02d}.png'
    if not p.exists() or p.stat().st_size == 0:
        missing.append(str(p))
        continue
    data = p.read_bytes()[:24]
    if data[:8] != b'\x89PNG\r\n\x1a\n' or data[12:16] != b'IHDR':
        raise SystemExit(f'not a valid PNG header: {p}')
    width, height = struct.unpack('>II', data[16:24])
    print(f'{p}: {p.stat().st_size} bytes, {width}x{height}, PNG')
print('missing_or_empty:', missing)
if actual != expected or missing:
    raise SystemExit(1)
PY
git status --short
```

Result:

```text
shot-list exact: True
production/episodes/ep01/frames/shot-01.png: 1902801 bytes, 1536x1024, PNG
production/episodes/ep01/frames/shot-02.png: 2416483 bytes, 1536x1024, PNG
production/episodes/ep01/frames/shot-03.png: 1999467 bytes, 1536x1024, PNG
production/episodes/ep01/frames/shot-04.png: 1963120 bytes, 1536x1024, PNG
production/episodes/ep01/frames/shot-05.png: 1950100 bytes, 1536x1024, PNG
production/episodes/ep01/frames/shot-06.png: 2158011 bytes, 1536x1024, PNG
production/episodes/ep01/frames/shot-07.png: 1992399 bytes, 1536x1024, PNG
production/episodes/ep01/frames/shot-08.png: 2103395 bytes, 1536x1024, PNG
missing_or_empty: []
 M production/episodes/ep01/frames/shot-07.png
```

Note: the final `git status` line reflected the corrected shot-07 generated after the first asset commit; it is included with this report commit.
