# AI Insight Daily

AI 最新资讯聚合展示网站，基于 Agent 自动化发布。

## 在线访问

https://2083054677-ctrl.github.io/ai-news-site/

## 快速开始

### 本地运行

```bash
# 无需安装任何依赖
cd D:/ai-news-site
python -m http.server 8080
# 打开 http://localhost:8080
```

### 发布新文章

在 Claude Code 中输入：

```
/chuangxinshijian
```

然后粘贴文章内容，Agent 自动完成：解析 → 写入 JSON → git push → 网站更新。

## 项目结构

```
ai-news-site/
├── index.html              # 主页
├── css/style.css           # Fluid Glass 风格样式
├── js/app.js               # 渲染、搜索、筛选逻辑
├── data/articles.json      # 文章数据（Agent 唯一修改的文件）
├── REPORT.md               # 详细项目报告
└── README.md               # 本文件
```

## 技术栈

- 纯 HTML + CSS + Vanilla JS（零依赖）
- GitHub Pages 部署
- Claude Code Skill 自动化发布

## 文章数据格式

```json
{
  "id": "news-001",
  "title": "文章标题",
  "summary": "摘要",
  "content": "正文",
  "author": "作者",
  "date": "2026-04-05",
  "tags": ["AI", "大模型"],
  "source": "来源链接"
}
```

## 排查指南

| 问题 | 排查方法 |
|------|----------|
| 文章不显示 | F12 → Console 看 fetch 错误，检查 JSON 格式 |
| 样式异常 | 确认浏览器支持 `backdrop-filter` |
| push 失败 | `git pull --rebase` 后重试 |
| Pages 没更新 | Settings → Pages 确认 Source 是 main 分支 |
