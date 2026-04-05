# AI Insight Daily — 项目报告

## 一、项目目标与功能概述

### 项目目标

构建一个基于 Agent 自动化发布的 AI 最新资讯聚合展示网站。用户只需在 Claude Code 中输入 `/chuangxinshijian` 命令并粘贴文章内容，Agent 即可自主完成信息提取、数据文件修改及 Git 版本推送，实现网站的自动化更新。

### 核心功能

| 功能 | 说明 |
|------|------|
| 资讯展示 | 以卡片形式展示 AI 领域最新资讯，支持点击查看详情 |
| 搜索 | 实时搜索文章标题、摘要、作者、标签 |
| 标签筛选 | 按标签（AI、大模型、开源、研究、产品、行业等）过滤文章 |
| 统计面板 | 展示文章总数、本周新增、标签数、最近更新时间 |
| 深色/浅色模式 | 支持主题切换，默认米白色浅色模式 |
| 自动化发布 | 通过 `/chuangxinshijian` Skill 一键解析文章并发布到网站 |
| 暗道入口 | 在 LuoLuo Wiki 搜索框输入 "ljy牛逼" 回车可跳转到本站 |

---

## 二、整体代码架构

```
ai-news-site/
├── index.html              # 主页（单页应用入口）
├── css/
│   └── style.css           # 全部样式（Fluid Glass 风格）
├── js/
│   └── app.js              # 渲染逻辑、搜索、筛选、主题切换
├── data/
│   └── articles.json       # 文章数据（Agent 唯一修改的文件）
├── assets/                 # 静态资源目录（预留）
└── README.md               # 使用说明
```

### 设计原则：内容与展示分离

整个项目最核心的设计决策是 **数据驱动**：

- 所有文章存储在 `data/articles.json` 这一个 JSON 文件中
- `index.html` 是纯静态 HTML 骨架，不包含任何文章内容
- `app.js` 在页面加载时 fetch JSON 数据，动态渲染所有内容
- Agent（`/chuangxinshijian` Skill）**只允许修改 `articles.json`**，绝不碰 HTML/CSS/JS

**为什么这样设计？** 因为任务要求 Agent "只能修改与新闻插入相关的关键部分，绝不能擅自修改页面的其他结构"。把数据独立成 JSON 文件后，Agent 的操作范围被严格限制在一个文件内，从根本上杜绝了页面崩溃的风险。

---

## 三、每个核心模块的职责

### 3.1 `index.html` — 页面骨架

- 定义 HTML 结构：导航栏、Hero 区、统计面板、标签筛选、卡片网格、文章详情模态框、页脚
- 引入 Google Fonts（Inter 字体）
- 不包含任何硬编码的文章内容，所有内容由 JS 动态注入

### 3.2 `css/style.css` — Fluid Glass 风格样式

**设计灵感来源：** [fluid.glass](https://fluid.glass/)

| 设计元素 | 实现方式 |
|----------|----------|
| 米白底色 | `--cream: #f3f0ec`，参考 fluid.glass 的 `--color-cream` |
| 深灰文字 | `--grey: #212325`，通过不同透明度区分层级（100%/60%/35%）|
| 毛玻璃效果 | `backdrop-filter: blur(2rem) saturate(180%)` + 半透明白色渐变背景 |
| 噪点纹理 | SVG 内联的 `feTurbulence` 滤镜，opacity 0.35 |
| 网格纹理 | CSS `linear-gradient` 生成 64px 间距网格线，opacity 0.04 |
| 极简边框 | `rgba(33, 35, 37, 0.12)`，hover 时加深到 0.3 |
| 排版 | uppercase 标签、0.08-0.12em 字间距、大量留白 |
| 无动画 | 只有 hover 时的 border-color transition（0.3s），无花哨动效 |

**深色模式：** 底色切换为 `#0b1012`，文字切换为 `#f3f0ec`，边框改为白色半透明，整体色板一致。

### 3.3 `js/app.js` — 应用逻辑

采用 IIFE（立即执行函数）封装，零依赖，纯 Vanilla JS。

| 函数 | 职责 |
|------|------|
| `loadArticles()` | fetch JSON 数据，按日期降序排列，兼容多种路径（本地/GitHub Pages）|
| `renderStats()` | 计算并渲染统计数据（总数、本周新增、标签数、最近更新）|
| `renderTags()` | 从文章中提取所有标签，生成筛选按钮 |
| `renderCards()` | 根据当前筛选条件渲染文章卡片 |
| `getFiltered()` | 组合标签筛选 + 关键词搜索的过滤逻辑 |
| `openModal()` / `closeModal()` | 文章详情模态框的打开/关闭 |
| `initTheme()` / `toggleTheme()` | 主题初始化（读取 localStorage）和切换 |
| `esc()` | HTML 转义，防止 XSS 注入 |

### 3.4 `data/articles.json` — 数据文件

每篇文章的数据结构：

```json
{
  "id": "news-001",
  "title": "文章标题",
  "summary": "2-3 句话的摘要（150 字以内）",
  "content": "完整正文（300-500 字）",
  "author": "作者/来源",
  "date": "2026-04-02",
  "tags": ["AI", "大模型", "开源"],
  "source": "原文链接"
}
```

**ID 规则：** `news-XXX`，三位数字递增。新文章由 Skill 自动生成下一个 ID。

### 3.5 `/chuangxinshijian` Skill — 自动化发布

Skill 文件位于 `~/.claude/skills/chuangxinshijian/SKILL.md`，定义了完整的工作流：

```
用户发文章 → Skill 触发 → 解析提取结构化字段
→ 读取 articles.json → 插入新条目到数组开头
→ 验证 JSON 合法性 → git add + commit + push
→ GitHub Pages 自动部署
```

**安全约束：**
- 只修改 `data/articles.json`，绝不碰其他文件
- 对用户输入做文本清洗，移除可疑指令片段（防 Prompt 注入）
- 每次修改后验证 JSON 格式合法
- Git commit message 标注新增文章标题

### 3.6 `easter-egg.tsx` — 暗道组件（LuoLuo Wiki 侧）

在 LuoLuo Wiki 项目（`HisMax/luoluo-wiki`）中新增的 React 组件：

- 渲染 `null`，DOM 中完全不可见
- 通过 `document.addEventListener('keydown', ..., true)` 捕获阶段监听按键
- 检测到搜索框输入值为 "ljy牛逼" + 回车时，`window.location.href` 跳转到新闻站
- 不影响正常搜索功能

---

## 四、页面/UI 设计思路

### 设计语言

以 [fluid.glass](https://fluid.glass/) 为视觉参考，融合 iOS 设计规范：

1. **色彩：** 米白色（`#f3f0ec`）为主色调，温暖不刺眼。用暖灰（`#d4cec6`）和深灰（`#212325`）构建层级。避免纯黑纯白。
2. **质感：** 所有卡片、导航栏、模态框使用 `backdrop-filter: blur(2rem)` 毛玻璃效果 + 半透明白色渐变，营造玻璃质感和空间纵深。
3. **纹理：** 米白底上叠加极淡的 SVG 噪点纹理和 64px 网格线，给平面增加微妙的纵深感。
4. **排版：** Inter 字体，标签用 uppercase + 宽字间距，标题用 -0.04em 紧凑字间距，形成节奏对比。
5. **交互：** 去掉所有花哨动画。只有 hover 时 border-color 变化（0.3s ease），极其克制。

### 首屏设计

- **Hero 区：** 4.2rem/800 weight 大标题，深灰→暖灰垂直渐变，一眼抓住注意力
- **Badge：** "POWERED BY AGENT" 胶囊徽章，暗示自动化能力
- **统计条：** 四格横排毛玻璃长条，数字 2rem/800 weight 突出

### 信息层级

```
导航栏（固定顶部，毛玻璃）
  ↓
Hero（大标题 + 副标题）
  ↓
统计条（一行四格数据）
  ↓
标签筛选（胶囊按钮组）
  ↓
文章卡片网格（主内容区）
  ↓
页脚
```

---

## 五、数据来源与处理流程

### 数据来源

1. **初始数据：** 通过 Web 搜索获取 2026 年 4 月真实 AI 新闻，人工核实后结构化为 JSON
2. **后续数据：** 用户通过 `/chuangxinshijian` Skill 提供文章原文，Agent 自动解析

### 处理流程

```
原始文章文本
  ↓ Agent 解析
提取：标题、摘要、正文、作者、日期、标签、来源
  ↓ 文本清洗
移除可疑指令、多余空行、格式噪声
  ↓ 生成 ID
读取现有 JSON，找最大 ID + 1
  ↓ 写入 JSON
插入到数组开头（最新优先）
  ↓ 验证
JSON.parse 校验格式合法
  ↓ 推送
git add → commit → push
  ↓ 部署
GitHub Pages 自动构建（1-2 分钟）
```

---

## 六、参考项目的启发

### Hextra-AI-Insight-Daily

| 启发点 | 我的借鉴 |
|--------|----------|
| Markdown 内容 + 静态站生成 | 简化为 JSON + 纯前端渲染，去掉 Hugo 依赖 |
| GitHub Actions 自动化流水线 | 简化为 Claude Code Skill + git push |
| 按月归档的侧边栏 | 简化为标签筛选 |
| 首页最新内容卡片 | 采用卡片网格布局，按日期降序 |
| 双语支持 | 未采用（当前只需中文） |

**核心学习：** 内容与展示分离的架构思想。Hextra 用 Markdown 文件作为数据源，我用 JSON 文件——更简单，更适合 Agent 操作。

### hot_find_twitter_reddit

| 启发点 | 我的借鉴 |
|--------|----------|
| 统计卡片（总数、互动量） | 采用四格统计面板 |
| 搜索 + 阈值过滤 | 采用关键词搜索 + 标签筛选 |
| 虚拟滚动处理大数据 | 未采用（文章数量级不需要） |
| 组件化拆分 | 采用清晰的功能分区（Stats/Filter/Cards/Modal） |
| Chrome 扩展架构 | 未采用（我们是 Web 站点） |

**核心学习：** 信息密度的平衡。统计面板 + 筛选 + 列表的三段式布局，让用户快速定位感兴趣的内容。

---

## 七、开发过程中的优化

### 第一轮优化：对齐 Fluid Glass 视觉风格

- **问题：** 初版用了紫色渐变 + 发光效果，用户反馈"太丑"
- **方案：** 完全重写 CSS，对齐 fluid.glass 的米白底 + 深灰文字 + 毛玻璃质感
- **结果：** 视觉质感大幅提升，风格统一

### 第二轮优化：首屏视觉冲击力

- **问题：** 首屏太平，缺少"一眼抓住人"的感觉
- **方案：**
  1. 背景叠加 SVG 噪点纹理 + CSS 网格纹理
  2. Hero 标题放大到 4.2rem/800 weight + 深灰→暖灰渐变
  3. 统计卡片合并为一个毛玻璃长条，数字放大突出
- **结果：** 首屏有了视觉锚点，信息层级更清晰

### Bug 修复：文章不显示

- **问题：** GitHub Pages 部署后文章不渲染
- **原因：** Pages 部署在子目录 `/ai-news-site/`，fetch 相对路径 + `color-mix()` CSS 函数兼容性
- **修复：** fetch 加多路径 fallback，CSS 全部改为 rgba fallback

---

## 八、后续修改指南

### 如果要改样式

修改 `css/style.css`：
- 颜色：修改 `:root` 中的 CSS 变量（`--cream`、`--grey`、`--taupe` 等）
- 卡片圆角：修改 `--radius`（默认 1.25rem）
- 毛玻璃强度：修改 `--blur`（默认 2rem）

### 如果要改页面结构

修改 `index.html`：
- 增减区块、调整布局
- 注意：不要删除带 `id` 属性的元素（JS 依赖这些 ID 渲染内容）

### 如果要改交互逻辑

修改 `js/app.js`：
- 搜索逻辑在 `getFiltered()` 函数
- 标签颜色映射在 `TAG_COLORS` 对象
- 日期格式在 `fmtDate()` 函数

### 如果要手动添加文章

直接编辑 `data/articles.json`，在数组开头加一个对象，注意 ID 递增。

### 如果要改 Skill

编辑 `~/.claude/skills/chuangxinshijian/SKILL.md`。

---

## 九、项目启动、运行、部署

### 本地运行

```bash
# 无需安装任何依赖！直接用浏览器打开即可
# 方法一：直接双击 index.html（搜索功能可能受限于 CORS）
# 方法二：用任意 HTTP 服务器（推荐）
cd D:/ai-news-site
python -m http.server 8080
# 然后打开 http://localhost:8080
```

### 在线访问

https://2083054677-ctrl.github.io/ai-news-site/

### 发布新文章

在 Claude Code 中：
```
/chuangxinshijian
```
然后粘贴文章内容，Agent 会自动解析、写入 JSON、推送到 GitHub，网站 1-2 分钟后自动更新。

### 如果报错排查

1. **页面空白 / 文章不显示：** 打开浏览器开发者工具（F12）→ Console，看是否有 fetch 错误。检查 `data/articles.json` 是否是合法 JSON。
2. **样式异常：** 检查 CSS 文件是否正确引用。如果用了很旧的浏览器，毛玻璃效果可能不生效（需要支持 `backdrop-filter`）。
3. **git push 失败：** 先 `git pull --rebase` 再 push。
4. **GitHub Pages 没更新：** 去仓库 Settings → Pages 确认 Source 是 `main` 分支。构建状态在 Actions 页面查看。

---

## 十、项目仓库与链接

| 项目 | 地址 |
|------|------|
| GitHub 仓库 | https://github.com/2083054677-ctrl/ai-news-site |
| 在线网站 | https://2083054677-ctrl.github.io/ai-news-site/ |
| 暗道入口（LuoLuo Wiki） | 搜索框输入 "ljy牛逼" 回车 |
