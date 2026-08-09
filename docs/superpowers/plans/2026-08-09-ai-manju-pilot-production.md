# 《侯府嫡女：今生换你们跪》3 集试水制作计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 按已批准设计规格，产出可发布的第 1–3 集古风重生复仇 AI 漫剧成片，并用数据决定是否扩到第 4–10 集。

**Architecture:** 先锁定角色定妆与提示词资产，再按集「关键帧出图 → 配音对白 → 剪辑成片 → 封面文案发布」流水线推进；第 1 集先发测完播，通过后再做第 2、3 集，避免一口气砸完成本。

**Tech Stack:** AI 文生图（可图生图/参考图）、TTS 或真人配音、剪映/CapCut（或同类短视频剪辑）、目标短视频平台（抖音/快手/视频号任选其一先测）

**Spec:** `docs/superpowers/specs/2026-08-09-ai-manju-rebirth-pilot-design.md`

## Global Constraints

- 系列名固定：`《侯府嫡女：今生换你们跪》`（禁止改回撞名旧标题）
- 单集时长：第 1 集约 75s，第 2 集约 80s，第 3 集约 85s
- 开场 0–3s 必须冲突钩子，禁止世界观铺垫
- 角色外貌以定妆参考图锁定，禁止每集重写外貌描述
- 统一负面提示词：`现代元素，眼镜，夸张网红脸，文字水印，肢体畸形，额外手指，脸崩，卡通过度，塑料皮肤，西方奇幻盔甲`
- 感情线节奏：第 1 集男主仅远影；第 2 集帘外侧脸；第 3 集正式交手；不解释男主是否重生
- 试水成功标准见规格 §1.2；三项中两项通过再扩集

---

## File Structure

```
production/
  characters/
    prompts.md                 # 角色提示词 + 负面词 + 选用说明
    shen-qingning/             # 女主候选与锁定定妆
    xie-linyuan/               # 男主
    shen-waner/                # 继妹
    lu-chengyan/               # 渣男
  episodes/
    ep01/
      shot-list.md             # 第 1 集逐镜执行表
      frames/                  # 关键帧图片
      voice-script.md          # 配音台本
      edit-checklist.md        # 剪辑验收
      final/                   # 成片与封面
    ep02/ ...
    ep03/ ...
  audio/
    voice-style.md             # 声线规范
  publish/
    ep01-publish.md            # 第 1 集发布文案与数据记录
    ep02-publish.md
    ep03-publish.md
    metrics-decision.md        # 3 集后扩集决策
```

---

### Task 1: 建立制作资产目录与角色提示词文件

**Files:**
- Create: `production/characters/prompts.md`
- Create: `production/audio/voice-style.md`
- Create: `production/characters/shen-qingning/.gitkeep`
- Create: `production/characters/xie-linyuan/.gitkeep`
- Create: `production/characters/shen-waner/.gitkeep`
- Create: `production/characters/lu-chengyan/.gitkeep`

**Interfaces:**
- Consumes: 规格 §3 角色设定、§7.1 定妆提示词、§4.2 声音
- Produces: 后续出图一律从 `production/characters/prompts.md` 复制提示词前缀

- [ ] **Step 1: 写入角色提示词文件**

创建 `production/characters/prompts.md` with:

```markdown
# 角色提示词锁定

系列：《侯府嫡女：今生换你们跪》

## 负面提示词（所有出图追加）
现代元素，眼镜，夸张网红脸，文字水印，肢体畸形，额外手指，脸崩，卡通过度，塑料皮肤，西方奇幻盔甲

## 沈清宁（女主）
古风美女，18-20岁，侯府嫡女，鹅蛋脸，凤眼微挑，薄唇，神态冷静克制，黑发高挽珠钗，水色薄纱长裙，素净不艳，冷青金色调，半身肖像，正面微侧，电影光，高细节，古装剧质感，一致人物设计

重生后加词：眼神锋利，嘴角冷笑，压迫感

锁定文件：`production/characters/shen-qingning/lock.png`（选定后填入）

## 谢临渊（男主）
古风俊美男子，25岁，权臣气质，剑眉，深目，薄唇寡言，玄色金纹长袍，墨发束冠，身形修长，气场强，半身肖像，俯视感，冷光，高细节，古装剧质感，一致人物设计

锁定文件：`production/characters/xie-linyuan/lock.png`

## 沈婉儿（继妹）
古风娇美女子，17岁，伪善甜美，圆润杏眼，笑里藏刀，粉白绣花裙，珠翠繁复，刻意妖娇，半身肖像，娇笑表情，暖粉光，古装剧质感

锁定文件：`production/characters/shen-waner/lock.png`

## 陆承晏（渣男）
古风英俊男子，22岁，表面谦谦世子，眼神势利闪躲，月白锦袍，金玉腰带，精致却轻浮，半身肖像，假笑，宴会光，古装剧质感

锁定文件：`production/characters/lu-chengyan/lock.png`

## 出图规则
1. 每角色先出 4 张候选：`candidate-01.png` … `candidate-04.png`
2. 选定 1 张复制/重命名为 `lock.png`
3. 后续分镜必须使用 lock 参考图 + 上方提示词前缀
```

- [ ] **Step 2: 写入声线规范**

Create `production/audio/voice-style.md` with:

```markdown
# 声线规范

| 角色 | 声线 | 语气 |
|------|------|------|
| 旁白 | 女声，沉稳偏低 | 讲故事感，前世恨、今生冷 |
| 沈清宁 | 女声，清亮带冷 | 短句，少哭腔，越危越稳 |
| 谢临渊 | 男声，低沉干净 | 慢、少、每个字有重量 |
| 沈婉儿 | 女声，甜而尖 | 假哭、娇嗔、破防时撕裂 |
| 陆承晏 | 男声，客气轻浮 | 人前体面，露馅发虚 |

气口：对白句尾留 0.2–0.4s。打脸落点：静场 0.5s → 刺音效。男主出场：压低 BGM。
```

- [ ] **Step 3: 验收目录存在**

Run:

```bash
test -f production/characters/prompts.md && test -f production/audio/voice-style.md && ls production/characters/*/
```

Expected: 提示词与声线文件存在，四个角色目录列出。

- [ ] **Step 4: Commit**

```bash
git add production/characters production/audio/voice-style.md
git commit -m "chore: scaffold manju character prompt and voice assets"
```

---

### Task 2: 锁定四角色定妆图

**Files:**
- Create: `production/characters/shen-qingning/candidate-01.png` … `candidate-04.png`, `lock.png`
- Create: `production/characters/xie-linyuan/candidate-01.png` … `candidate-04.png`, `lock.png`
- Create: `production/characters/shen-waner/candidate-01.png` … `candidate-04.png`, `lock.png`
- Create: `production/characters/lu-chengyan/candidate-01.png` … `candidate-04.png`, `lock.png`
- Modify: `production/characters/prompts.md`（填写锁定说明）

**Interfaces:**
- Consumes: `production/characters/prompts.md` 提示词
- Produces: 四个 `lock.png`，供 Task 3–7 分镜参考

- [ ] **Step 1: 女主出 4 张候选并选定**

用女主提示词生成 4 张，保存到 `production/characters/shen-qingning/`。  
选定标准：脸型清晰、水色裙、冷青金、可复用半身。  
将选定图复制为 `lock.png`。

- [ ] **Step 2: 男主 / 继妹 / 渣男同样各出 4 选 1**

同样流程，分别写入对应目录的 `lock.png`。

- [ ] **Step 3: 一致性验收（人工清单）**

对每个 `lock.png` 勾选：

```text
[ ] 无现代元素/眼镜/水印
[ ] 无畸形手/崩脸
[ ] 服装色系符合 prompts.md
[ ] 四人并排对比时，女主与继妹可一眼区分（素净 vs 繁复）
[ ] 男主玄色金纹压迫感成立
```

Expected: 四条全部勾选通过；否则重出该角色。

- [ ] **Step 4: Commit**

```bash
git add production/characters
git commit -m "assets: lock four character design sheets for pilot"
```

---

### Task 3: 第 1 集逐镜表 + 关键帧出图

**Files:**
- Create: `production/episodes/ep01/shot-list.md`
- Create: `production/episodes/ep01/frames/shot-01.png` … `shot-08.png`（可按镜合并多帧，但至少覆盖下表 8 镜）

**Interfaces:**
- Consumes: 四角色 `lock.png` + 规格 §6 第 1 集逐镜
- Produces: `ep01/frames/*` 供配音剪辑

- [ ] **Step 1: 写入第 1 集执行逐镜表**

Create `production/episodes/ep01/shot-list.md` with:

```markdown
# EP01 跪着死，睁眼活（目标 75s）

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
```

- [ ] **Step 2: 按逐镜表出 8 个关键帧**

每帧使用对应角色 `lock.png` 作参考。必保三帧质量最高：`shot-02`（跪地）、`shot-05`（睁眼）、`shot-08`（推酒）。

- [ ] **Step 3: 关键帧验收**

```text
[ ] 8 个 shot 文件都存在
[ ] 女主脸与 lock.png 一致（不像换人）
[ ] shot-04 男主仅远影，不抢戏
[ ] shot-08 可直接当封面候选
[ ] 无现代元素/崩手/水印
```

- [ ] **Step 4: Commit**

```bash
git add production/episodes/ep01
git commit -m "assets: add episode 1 shot list and key frames"
```

---

### Task 4: 第 1 集配音台本与音频

**Files:**
- Create: `production/episodes/ep01/voice-script.md`
- Create: `production/episodes/ep01/audio/narration.wav`（或 `.mp3`）
- Create: `production/episodes/ep01/audio/qingning.wav`
- Create: `production/episodes/ep01/audio/waner.wav`
- Create: `production/episodes/ep01/audio/chengyan.wav`

**Interfaces:**
- Consumes: `production/audio/voice-style.md` + ep01 shot-list
- Produces: 分轨音频，供 Task 5 剪辑

- [ ] **Step 1: 写配音台本**

Create `production/episodes/ep01/voice-script.md` with:

```markdown
# EP01 配音台本

## 旁白
1. 「前世，我跪着死在侯府寿宴上。」（停半拍）
2. 「而我错过的那个人，终于来晚了。」

## 沈婉儿
1. 「姐姐喝多了……」（假哭）
2. 「姐姐，这杯贺寿酒，你先饮。」（甜笑）

## 陆承晏
1. 「真是丢尽陆家的脸。」（嫌恶）

## 沈清宁
1. 「好啊。」（冷，短）
2. 「这酒烈，该你喝。」（更冷，句尾压住）

## 结尾字幕（可人声可仅字幕）
「今生，换你们跪。」
```

- [ ] **Step 2: 按声线规范录制/TTS 导出分轨**

保存到 `production/episodes/ep01/audio/`。旁白与女主必须分轨，便于打脸静场。

- [ ] **Step 3: 听感验收**

```text
[ ] 女主无哭腔
[ ] 继妹假哭足够刺耳可恨
[ ] 旁白沉、不抢打脸句
[ ] 单句尾有 0.2–0.4s 气口
[ ] 总对白时长可塞进 75s（含画面呼吸）
```

- [ ] **Step 4: Commit**

```bash
git add production/episodes/ep01/voice-script.md production/episodes/ep01/audio
git commit -m "audio: add episode 1 voice script and stems"
```

---

### Task 5: 第 1 集剪辑成片 + 封面

**Files:**
- Create: `production/episodes/ep01/edit-checklist.md`
- Create: `production/episodes/ep01/final/ep01.mp4`
- Create: `production/episodes/ep01/final/cover.png`

**Interfaces:**
- Consumes: ep01 frames + audio
- Produces: 可上传成片与封面

- [ ] **Step 1: 写剪辑验收清单**

Create `production/episodes/ep01/edit-checklist.md` with:

```markdown
# EP01 剪辑验收

- [ ] 成片时长 70–80s（目标 75s）
- [ ] 0–3s 已出现毒酒/跪地冲突，无自我介绍
- [ ] 打脸句「该你喝」前有约 0.5s 静场
- [ ] 字幕清晰，每屏不超过 2 行
- [ ] 结尾黑屏字幕：今生，换你们跪。
- [ ] 系列名仅在片头/片尾轻标一次，不压过钩子
- [ ] 导出竖屏 1080x1920（或平台要求等比）
```

- [ ] **Step 2: 在剪映/CapCut 按 shot-list 组装**

时间线顺序严格按镜号 1→8；BGM：前压抑、推酒后冷钢琴/斩击感。

- [ ] **Step 3: 导出成片与封面**

- 成片：`production/episodes/ep01/final/ep01.mp4`
- 封面：优先用 `shot-08` 女主冷笑/推酒，标题字：`重生后，她把毒酒推了回去`

- [ ] **Step 4: 对照 edit-checklist 全勾后 Commit**

```bash
git add production/episodes/ep01/edit-checklist.md production/episodes/ep01/final
git commit -m "video: export episode 1 pilot cut and cover"
```

---

### Task 6: 发布第 1 集并记录基线数据

**Files:**
- Create: `production/publish/ep01-publish.md`

**Interfaces:**
- Consumes: `ep01/final/ep01.mp4` + `cover.png`
- Produces: 完播率基线，决定是否立即启动第 2 集

- [ ] **Step 1: 写发布单**

Create `production/publish/ep01-publish.md` with:

```markdown
# EP01 发布单

系列：《侯府嫡女：今生换你们跪》
单集标题：重生后，她把毒酒推了回去

## 文案
前世她跪着死在寿宴上。
重生当天，继妹又端来同一杯酒——
她笑了：这酒，该你喝。
#古风漫剧 #重生复仇 #嫡女

## 发布记录
- 平台：
- 账号：
- 发布时间：
- 作品链接：

## 24h / 72h 数据
| 指标 | 24h | 72h |
|------|-----|-----|
| 播放 |  |  |
| 完播率 |  |  |
| 点赞 |  |  |
| 评论 |  |  |
| 关键评论摘要 |  |  |

## 判定
- [ ] 完播率高于账号同时长均值 → 启动 EP02
- [ ] 明显偏低 → 先改封面/前 3 秒重发，不直接拍 EP02
```

- [ ] **Step 2: 上传发布**

封面 + 文案原样使用；话题标签保留三个核心签。

- [ ] **Step 3: 满 24h 填数据并判定**

Expected 决策二选一：`启动 EP02` 或 `先改钩子重发`。写入发布单「判定」区。

- [ ] **Step 4: Commit**

```bash
git add production/publish/ep01-publish.md
git commit -m "publish: record episode 1 release and baseline metrics"
```

---

### Task 7: 第 2 集制作（逐镜 → 音频 → 成片 → 发布）

**Files:**
- Create: `production/episodes/ep02/shot-list.md`
- Create: `production/episodes/ep02/frames/shot-01.png` … `shot-07.png`
- Create: `production/episodes/ep02/voice-script.md`
- Create: `production/episodes/ep02/audio/*`
- Create: `production/episodes/ep02/edit-checklist.md`
- Create: `production/episodes/ep02/final/ep02.mp4`
- Create: `production/episodes/ep02/final/cover.png`
- Create: `production/publish/ep02-publish.md`

**Interfaces:**
- Consumes: 角色 lock + 规格 §6 第 2 集；仅在 Task 6 判定通过后开始
- Produces: EP02 成片与评论爽点数据

- [ ] **Step 1: 写 EP02 逐镜表**

Create `production/episodes/ep02/shot-list.md` with:

```markdown
# EP02 当众揭谎（目标 80s）

封面标题：她当众揭穿毒酒，继妹假哭也救不了

| 镜号 | 时长 | 画面文件 | 画面要点 | 对白 |
|------|------|----------|----------|------|
| 1 | 0–5s | frames/shot-01.png | 酒盏停在继妹唇边 | 宾客：嫡女这是怎么了？ |
| 2 | 5–15s | frames/shot-02.png | 继妹洒酒娇哭 | 沈婉儿：姐姐吓我……我手脚软了。 |
| 3 | 15–28s | frames/shot-03.png | 举帕示毒砂 | 沈清宁：手脚软？还是心里有鬼？ |
| 4 | 28–40s | frames/shot-04.png | 女主请府医验酒 | 沈清宁：验不出来，我沈清宁给妹妹跪。 |
| 5 | 40–55s | frames/shot-05.png | 府医色变全场哗然 | 宾客：竟敢毒嫡女！ / 府医：酒中有毒，还拌了软筋散！ |
| 6 | 55–65s | frames/shot-06.png | 钉住陆承晏 | 沈清宁：陆公子方才退得最快，倒像早知有事。 |
| 7 | 65–80s | frames/shot-07.png | 帘外男主侧脸对视 | （无对白） |

结尾字幕：这个男人……看我的眼神，为何像认识很久？
```

- [ ] **Step 2: 出关键帧（必保 shot-03 / shot-05 / shot-07）并配音剪辑**

声线仍遵 `voice-style.md`。男主本集无对白，只有侧脸压迫感。

- [ ] **Step 3: 验收并导出**

```text
[ ] 时长 75–85s
[ ] 验毒打脸信息一次说清：有毒 + 软筋散
[ ] 男主仅帘外侧脸，不提前剧透身份全貌
[ ] 导出 ep02.mp4 + cover.png
```

- [ ] **Step 4: 发布并记录评论爽点**

Create `production/publish/ep02-publish.md`，字段同 EP01，额外增加：

```markdown
## 评论观察
- [ ] 出现「继妹讨厌 / 女主爽 / 打脸解气」类评论
- 代表性评论粘贴：
```

- [ ] **Step 5: Commit**

```bash
git add production/episodes/ep02 production/publish/ep02-publish.md
git commit -m "video: finish and publish episode 2 slap-face cut"
```

---

### Task 8: 第 3 集制作（逐镜 → 音频 → 成片 → 发布）

**Files:**
- Create: `production/episodes/ep03/shot-list.md`
- Create: `production/episodes/ep03/frames/shot-01.png` … `shot-07.png`
- Create: `production/episodes/ep03/voice-script.md`
- Create: `production/episodes/ep03/audio/*`
- Create: `production/episodes/ep03/edit-checklist.md`
- Create: `production/episodes/ep03/final/ep03.mp4`
- Create: `production/episodes/ep03/final/cover.png`
- Create: `production/publish/ep03-publish.md`

**Interfaces:**
- Consumes: 角色 lock + 规格 §6 第 3 集
- Produces: 男主悬念数据，供扩集决策

- [ ] **Step 1: 写 EP03 逐镜表**

Create `production/episodes/ep03/shot-list.md` with:

```markdown
# EP03 错过的人（目标 85s）

封面标题：前世我选了渣男；今生，错过的人提前来了

| 镜号 | 时长 | 画面文件 | 画面要点 | 对白 |
|------|------|----------|----------|------|
| 1 | 0–8s | frames/shot-01.png | 廊下独处捏毒砂 | 旁白：前世我信错人，也看错局。 |
| 2 | 8–18s | frames/shot-02.png | 男主走近递玉佩 | 谢临渊：沈小姐，别来无恙。 |
| 3 | 18–30s | frames/shot-03.png | 女主看玉佩一震 | 沈清宁：……你怎么会有这个？ |
| 4 | 30–45s | frames/shot-04.png | 闪回错过求见 | 谢临渊：有人要你死，也有人要你活。 |
| 5 | 45–58s | frames/shot-05.png | 出示买毒账册 | 谢临渊：今晚，只是开始。 |
| 6 | 58–70s | frames/shot-06.png | 对视烛火 | 沈清宁：你想要什么？ |
| 7 | 70–85s | frames/shot-07.png | 俯身低语特写 | 谢临渊：前世你不信我。今生，别再选错人。 |

结尾字幕：下集：她要用这份账，把继母钉死在府里。
```

- [ ] **Step 2: 出关键帧（必保 shot-02 / shot-06 / shot-07）并配音剪辑**

谢临渊对白必须「慢、少、有重量」。禁止加旁白解释他是否重生。

- [ ] **Step 3: 验收并导出**

```text
[ ] 时长 80–90s
[ ] 玉佩 + 账册两个道具信息都交代清楚
[ ] 结尾钩子落在「前世你不信我」
[ ] 不出现「我也重生了」类直给台词
[ ] 导出 ep03.mp4 + cover.png
```

- [ ] **Step 4: 发布并记录男主相关评论占比**

Create `production/publish/ep03-publish.md`，额外：

```markdown
## 男主悬念观察
- [ ] 出现「男主是谁 / 他也重生了吗 / 好撩」类评论
- 男主相关评论占比估算：____%
```

- [ ] **Step 5: Commit**

```bash
git add production/episodes/ep03 production/publish/ep03-publish.md
git commit -m "video: finish and publish episode 3 male-lead hook cut"
```

---

### Task 9: 三集复盘与是否扩到 4–10 集

**Files:**
- Create: `production/publish/metrics-decision.md`

**Interfaces:**
- Consumes: ep01/ep02/ep03 发布单数据
- Produces: Go / No-Go 决策；若 Go，下一计划从规格 §5 第 4 集「夺回账房」起做

- [ ] **Step 1: 填写决策表**

Create `production/publish/metrics-decision.md` with:

```markdown
# 3 集试水决策

系列：《侯府嫡女：今生换你们跪》

| 标准（规格 §1.2） | 结果 | 通过？ |
|------------------|------|--------|
| EP01 完播率高于账号同时长均值 |  | 是/否 |
| EP02 出现骂点/爽点评论 |  | 是/否 |
| EP03 出现男主追更评论 |  | 是/否 |

## 决策规则
- 三项中 ≥2 项「是」→ **Go**：启动第 4–10 集（先做 EP04 夺回账房）
- 仅 1 项「是」→ **Iterate**：只重做最弱那一集的前 3 秒/封面后再测
- 0 项「是」→ **Stop/Pivot**：换钩子或换男主出场节奏，不直接连拍 10 集

## 最终结论
- 结论：Go / Iterate / Stop
- 理由：
- 下一步负责人动作：
```

- [ ] **Step 2: 按规则写下最终结论**

Expected: 结论字段为 `Go`、`Iterate` 或 `Stop` 之一，且有对应下一步。

- [ ] **Step 3: Commit**

```bash
git add production/publish/metrics-decision.md
git commit -m "docs: record three-episode pilot go or no-go decision"
```

---

## Spec Coverage Checklist（写计划时自检）

| 规格章节 | 对应任务 |
|----------|----------|
| §1 成功标准 | Task 6、7、8、9 |
| §2 剧名/定位 | Task 1、6 文案；全局约束 |
| §3 角色 | Task 1–2 |
| §4 视觉声音剪辑节奏 | Task 2、4、5 |
| §5 10 集大纲 | Task 9 扩集入口指向 EP04+ |
| §6 EP01–03 逐镜 | Task 3、7、8 |
| §7 出图提示词 | Task 1–3、7、8 |
| §8 发布模板 | Task 6–8 |
| §9 最小执行清单 | Task 2→3→5→6→7→8→9 |
| §10 非目标 | 不做账号矩阵/付费分销/男主重生解释 |

## Placeholder Scan
本计划无 TBD/TODO；每步含具体文件路径、台本原文与验收勾选。

---

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-08-09-ai-manju-pilot-production.md`.

**Two execution options:**

1. **Subagent-Driven（推荐）** — 每个 Task 派一个新子代理，任务间审查，迭代快  
2. **Inline Execution** — 本会话按 executing-plans 顺序执行，设检查点

你要哪一种？
