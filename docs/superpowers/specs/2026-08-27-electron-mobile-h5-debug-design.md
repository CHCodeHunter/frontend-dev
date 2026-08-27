# Electron 桌面端调试移动端 H5：方案设计

日期：2026-08-27  
状态：草案（咨询/方案，尚未进入实现）

## 1. 目标

在 **Electron 桌面应用**里，调试 **移动端 App 内 WebView 打开的 H5**，体验尽量接近：

- Android：Chrome `chrome://inspect` 插 USB 线远程调试
- iOS：Safari「开发」菜单远程调试 WKWebView

两端代码都可以改。调试能力只放 debug 包，不进生产。

本文默认这是 **原生壳 + WebView 装 H5** 的混合应用（可带 JSBridge），而不是纯浏览器里打开的网页。

## 2. 先对齐：Safari / Chrome「插线调试」实际在干什么

桌面浏览器并没有「看」手机屏幕，而是连上了 WebView 暴露的 **调试协议**：

```text
手机 WebView ──(USB / ADB / usbmuxd)──▶ 调试协议服务端
                                              │
桌面 DevTools UI ──(WebSocket)───────────────▶ 调试协议客户端
```

| 平台 | WebView | 协议 | 桌面入口 | 开启条件 |
|------|---------|------|----------|----------|
| Android | System WebView / Chrome（Chromium） | Chrome DevTools Protocol（CDP） | `chrome://inspect` | `WebView.setWebContentsDebuggingEnabled(true)` |
| iOS 16.4+ | WKWebView（WebKit） | WebKit Remote Inspector（不是 CDP） | Safari Develop | `webView.isInspectable = true` |

Electron 本身就是 Chromium，**原生就能当 CDP 客户端**，也能把官方 DevTools 前端嵌进窗口。这是「在桌面端复刻插线调试」最硬的技术基础。

iOS 是另一套协议。想在 Electron 里用同一套 Chrome DevTools UI 调 iOS，必须做协议转换，或走下文的 JS Agent 通道。

## 3. 三种方案

### 方案 A：原生远程检查器（保真度最高，最像插线）

Electron 只做 **设备发现 + 端口转发 + 嵌 DevTools 前端**。页面仍跑在手机真实 WebView 里，DOM / 样式 / 性能 / 与系统 WebView 版本相关的问题都能看到。

**Android（成熟）**

1. Debug 包：`WebView.setWebContentsDebuggingEnabled(true)`
2. Electron 调 `adb devices`，对目标进程做：
   `adb forward tcp:<port> localabstract:webview_devtools_remote_<pid>`
3. 拉 `http://127.0.0.1:<port>/json`，拿到每个 H5 页的 `webSocketDebuggerUrl`
4. Electron `BrowserWindow` 加载 DevTools 前端，连这个 WebSocket

无线：先 USB 执行 `adb tcpip 5555`，再 `adb connect <手机IP>`。之后和插线同一条 CDP 路径。

**iOS（明显更难）**

- 协议是 WebKit Inspector，官方 UI 是 Safari，不是 Chrome DevTools。
- 常见桥：`ios-webkit-debug-proxy`，把 USB 上的 Inspector 转成近似 CDP 的 `localhost:9222/json`。映射不完整（Timeline、部分 CSS、部分 Console 会缺）。
- Windows 还依赖 Apple 移动设备驱动 / usbmuxd；macOS 上体验最好。
- 若团队可以接受「iOS 仍用 Safari，Electron 只调 Android」，实现量和稳定性都会好很多。

**优点**：看到的就是真机 WebView；Android 几乎可以做到和 Chrome inspect 同级。  
**缺点**：iOS 协议转换脆弱；Windows 驱动麻烦；纯 USB 日常摩擦大。

### 方案 B：H5 内注入 CDP Agent（无线、双端同一条路，推荐作日常主路径）

不依赖系统 WebView 的 inspect 开关。Debug 包在每个 WebView 里注入一段 JS，在页面里实现一套 **CDP 子集**，经局域网 WebSocket 连到 Electron 里的调试服务。DevTools UI 仍用 Chrome 那套。

可直接复用的开源栈：

- [chii](https://github.com/liriliri/chii) / [chobitsu](https://github.com/liriliri/chobitsu)：浏览器里跑 CDP + 官方 DevTools 前端
- 微信开发者工具、各类小程序 IDE 也是这条路：Electron 宿主 + 真机/模拟器 + 注入调试 agent

注入方式（优先原生注入，H5 不用改每个页面）：

- Android：`WebView.addJavascriptInterface` 不负责注入；用 `evaluateJavascript` 或 `WebViewClient` 在 `onPageFinished` 注入；更好是 `WebViewCompat.addDocumentStartJavaScript`（页面一开始就有）
- iOS：`WKUserScript`（`.atDocumentStart`）

发现 Electron 的方式（按稳妥程度）：

1. Electron 展示二维码 / 局域网 URL，App 调试页扫码或粘贴
2. UDP / mDNS 在局域网广播 `electron-h5-debug`
3. 同一 Wi‑Fi 下原生层把 `http://<ip>:<port>/target.js` 写进 UserScript

**优点**：Android / iOS / 无线同一套；Windows 上也能调 iOS H5；可加自定义面板（JSBridge、容器版本）。  
**缺点**：不是 WebView 内核自带的 inspector。布局/合成/jank 和「这个系统 WebView 的 bug」保真度低于方案 A。Sources 映射、部分 Performance 会弱一些。

### 方案 C：Electron 里直接打开同一份 H5（模拟，不是真机）

Electron 加载同一 URL，改 UA / 视口 / DPR。适合写样式、接接口、跑热更新，**测不出** WKWebView 与 Chromium 差异、安全区、输入法、原生桥。

只作为预览窗口，不替代 A/B。

## 4. 推荐架构：双通道

日常用 B，需要对齐真机内核时用 A。Electron 做一个「调试工作台」把两条通道收在一起。

```text
┌──────────────────────────────────────────────────────────┐
│ Electron 调试宿主                                         │
│                                                          │
│  设备列表 / 扫码连接                                      │
│  DevTools 窗口（chrome-devtools-frontend）                │
│  可选：H5 本地预览（方案 C）                               │
│  可选：Vite/webpack 开发服务，给真机 WebView 热更新        │
│                                                          │
│  ┌─ 通道 A：原生 CDP ─────────────────────────────────┐  │
│  │ adb forward  →  /json  →  ws://127.0.0.1:9222/...  │  │
│  │ iOS: ios-webkit-debug-proxy（可选，macOS 优先）     │  │
│  └────────────────────────────────────────────────────┘  │
│  ┌─ 通道 B：注入 Agent ────────────────────────────────┐  │
│  │ WS Server  ←── 局域网 ──  WebView 内 chobitsu/chii │  │
│  └────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────┘
        │ USB / 无线 ADB                    │ Wi‑Fi WS
        ▼                                   ▼
┌──────────────────────────────────────────────────────────┐
│ 移动端 Debug 包                                           │
│  WebView inspectable = true（给通道 A）                    │
│  WKUserScript / document-start JS（给通道 B）              │
│  调试面板：连接状态、当前 H5 URL、JSBridge 日志            │
└──────────────────────────────────────────────────────────┘
```

### 4.1 Electron 侧模块

| 模块 | 职责 |
|------|------|
| DeviceHub | 列 ADB 设备、转发端口、轮询 `/json`；维护通道 B 的已连接 target |
| DevtoolsHost | 为每个 H5 target 开窗口，加载匹配版本的 DevTools 前端 |
| AgentServer | 通道 B 的 HTTP + WebSocket；下发 `target.js`；可 mDNS 广播 |
| BridgeProbe（可选） | 自定义 DevTools panel，看 JSBridge 调用 |
| H5DevServer（可选） | 把本地 H5 打到局域网，WebView 加载 `http://pc-ip:5173` |

嵌 DevTools 前端时注意 **协议版本要对上**：

- 通道 A / Android：跟手机 System WebView 的 Chrome 大版本对齐，或用 `https://chrome-devtools-frontend.appspot.com/serve_rev/@<revision>/inspector.html?ws=...`
- 通道 B：跟 chii/chobitsu 绑定的 frontend 版本锁死，不要跟系统 Chrome 混用

`devtools://devtools/bundled/inspector.html` 主要服务于 **本进程 webContents**，远程 target 更稳妥的是独立 frontend 资源，而不是假定 `devtools://` 能连任意 `ws://`。

通道 A 的连接信息来自 `/json`，典型字段：`title`、`url`、`webSocketDebuggerUrl`、`devtoolsFrontendUrl`。

### 4.2 移动端改动（debug 包）

**Android**

```kotlin
if (BuildConfig.DEBUG) {
    WebView.setWebContentsDebuggingEnabled(true)
}
// document-start 注入通道 B 的 loader
// loader 从本地存储或扫码结果读取 Electron 的 agent URL
```

**iOS**

```swift
if isDebug {
    webView.isInspectable = true
}
let script = WKUserScript(
    source: loaderJS, // 读取调试服务器地址并插入 <script src=".../target.js">
    injectionTime: .atDocumentStart,
    forMainFrameOnly: false
)
webView.configuration.userContentController.addUserScript(script)
```

子 frame / iframe 里的 H5 也要调试时，`forMainFrameOnly` 必须为 `false`，并确认跨域 iframe 是否允许注入（很多支付页不行，这是预期限制）。

**不要**把 agent URL 写死进生产包。用：

- 仅 debug flavor 编译进 loader
- 或原生调试页手动填 IP / 扫码后写入 `UserDefaults` / `SharedPreferences`

### 4.3 连接体验（接近「插上线就能看」）

目标交互：

1. 打开 Electron → 显示本机 IP、端口、二维码、ADB 设备列表
2. 手机与电脑同一 Wi‑Fi，或 USB 已授权
3. 打开 App 里任意 H5
4. Electron 设备列表出现该页（title + url），点一下打开 DevTools

通道 A：有 USB/无线 ADB 时自动出现，无需扫码。  
通道 B：第一次扫码或点「连接调试器」，之后 loader 记住服务器地址。

### 4.4 JSBridge

Chrome/Safari inspect **看不到** 自定义 `window.webkit.messageHandlers` / `JavascriptInterface`。混合应用建议在通道 B 加一层探针：

- 包装 `postMessage` / `prompt` 桥，把 method、args、耗时、回调打到自定义 CDP domain，例如 `Bridge.export`
- Electron DevTools 加一个「Bridge」面板

这是官方插线做不到、而你们能改两端时最值得做的增量。

### 4.5 和「H5 热更新」一起用

很多团队真正的日常是：手机 WebView 打开 `http://<电脑IP>:5173`。这和远程 DevTools 是正交的：

- 热更新：改的是 **页面从哪加载**
- DevTools：改的是 **怎么检查已经在跑的页面**

两者叠在一起最舒服：真机 WebView 加载本地 Vite，同时走通道 A 或 B 检查。Electron 可以把「启动 H5 dev server + 显示局域网 URL + 打开 DevTools」做成一个按钮。

## 5. 安全与范围

- AgentServer 默认只绑局域网，不绑 `0.0.0.0` 到公网；可加一次性 token（写进二维码）
- 生产包：关闭 inspectable、不注入 loader、不打 adb 相关逻辑
- HTTPS H5 注入 HTTP 的 `target.js` 会被 mixed content 拦住：agent 用 HTTP 明文即可（仅 LAN），或让 Electron 发自签证书并把 CA 装进 debug 包（成本高，一般不值得）
- 更稳：原生在 document-start **直接注入脚本源码**，不从 HTTP 拉 `target.js`，只连 `ws://`。WS 从页面连局域网 IP 通常比插 `<script src="http://...">` 少踩 mixed content

## 6. 建议落地顺序

不需要一次做完。按收益排序：

1. **通道 B 最小闭环**：Electron 起 chii（或自建 WS + 官方 frontend）+ 手机 debug 包 document-start 注入。先调通 Console / Network / Elements。验证：Android 真机无线打开 H5，Electron 能看到 DOM 和接口。
2. **发现体验**：二维码 + 记住地址；可选 mDNS。
3. **通道 A（仅 Android）**：Electron 调 adb、列 `/json`、一键开 DevTools。需要查真实排版/性能时用。
4. **JSBridge 面板**（如果你们有桥）。
5. **iOS 通道 A**：仅当 B 不够、且团队以 macOS 为主时再上 ios-webkit-debug-proxy；否则 iOS 继续用 Safari Develop 作保真兜底。
6. **方案 C 预览窗** 可随时加，不要挡 1–3。

## 7. 怎么选（简表）

| 需求 | 走哪条 |
|------|--------|
| 日常改 H5、看 console / network / DOM | 通道 B |
| 和系统 WebView 排版、滚动、性能有关 | 通道 A（Android）或 Safari（iOS） |
| Windows 上调 iOS H5 | 只能通道 B（或真机 Safari，但那不是 Electron） |
| 查 JSBridge | 通道 B + 自定义面板 |
| 只是先写页面 | 方案 C 或浏览器，不必上真机 |

## 8. 明确不做什么（本方案范围）

- 不替代 Charles / Proxyman 做全流量抓包（可另接系统代理）
- 不调试 React Native / Flutter 原生层（只覆盖 WebView 里的 H5）
- 不在生产用户设备上开远程调试
- 第一期不做完整 iOS 原生协议栈（成本高、保真仍不如 Safari）

## 9. 实现时建议复用的组件

- Electron：`child_process` 调 `adb`；`bonjour` / `multicast-dns` 做发现；独立 `BrowserWindow` 加载 frontend
- 通道 B：优先 chii 作参考实现，不要从零实现 CDP
- 通道 A Android：官方 `/json` + `webSocketDebuggerUrl`，不要解析 DevTools 内部私有协议
- iOS 保真兜底：继续用 Safari；Electron 里给「在 Safari 中打开检查器」的说明，而不是假装已经 100% 对齐

## 10. 成功标准

做到下面这件事，方案就算成立：

> 手机打开 App 内 H5 后，在 Electron 里点该页面，出现可用的 Elements / Console / Network，能改 DOM、能看到接口，行为接近 Chrome inspect。

进阶标准：同一列表里区分「原生 CDP」和「注入 Agent」两个来源；Android USB 插入后无需扫码自动出现页面。
