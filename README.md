# github-wechat-publisher

[![License](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.8+-green.svg)](https://www.python.org/)

**Markdown 内容 → GitHub 仓库备份 + 微信公众号发布** 一体化 Skill

一个用于 Claude Code 的自动化发布工具，接收 Markdown 内容，自动完成 GitHub 推送备份和微信公众号排版发布。

生成效果可以查看公众号日报文章：

<img width="430" height="430" alt="alwhatyouneed code" src="https://github.com/user-attachments/assets/06ed1b3e-0122-40ba-b1cf-ac3ae7d16b70" />


---

## 功能特性

| 功能 | 说明 |
|------|------|
| 📤 GitHub 备份 | 自动推送 Markdown 报告到指定 GitHub 仓库，保留历史归档 |
| 🎨 微信排版 | 集成 [xiaohu-wechat-format](https://github.com/xiaohuailabs/xiaohu-wechat-format)，支持 30+ 主题 |
| 📱 公众号发布 | 自动发布到微信公众号草稿箱 |
| ⚙️ 交互配置 | 首次使用自动引导配置 GitHub Token、仓库、微信 API |
| 🔀 灵活调用 | 支持仅 GitHub、仅微信、或两者都执行 |

---

## 工作流程

```
┌─────────────────────────────────────────────────────────────┐
│                     用户请求示例                              │
│   "爬取 HuggingFace Papers，生成日报，                        │
│    备份到 GitHub 并发布到微信公众号"                          │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   Claude 执行数据爬取                         │
│   • 使用 WebFetch / WebSearch 爬取数据                       │
│   • 生成结构化 Markdown 报告                                  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│              github-wechat-publisher 接管                    │
│   • 接收 Markdown 内容                                        │
│   • 推送到 GitHub 仓库备份                                    │
│   • 使用 xiaohu-wechat-format 排版                            │
│   • 发布到微信公众号草稿箱                                     │
└─────────────────────────────────────────────────────────────┘
```

---

## 安装

### 方式一：对话安装（最简单）

对 Claude 说（需提供仓库地址）：

```
安装 github-wechat-publisher skill: https://github.com/AIWhatYouNeed/github-wechat-publisher
```

Claude 会自动执行：
1. Clone 到 `~/.agents/skills/` 目录
2. 安装依赖 `markdown`、`requests`
3. 运行配置向导

### 方式二：命令行安装

```bash
cd ~/.agents/skills/
git clone https://github.com/AIWhatYouNeed/github-wechat-publisher.git
cd github-wechat-publisher
pip3 install markdown requests
```

### 方式三：手动安装

```bash
git clone https://github.com/AIWhatYouNeed/github-wechat-publisher.git
cd github-wechat-publisher
pip3 install markdown requests
```

---

## 配置

### 运行配置向导

```bash
python3 scripts/setup.py
```

配置向导会交互式引导你完成以下配置：

### 配置项说明

| 配置项 | 环境变量 | 说明 | 获取方式 |
|--------|----------|------|----------|
| GitHub Token | `GITHUB_TOKEN` | 推送文件到仓库 | [GitHub Settings](https://github.com/settings/tokens)，需 `repo` 权限 |
| GitHub 仓库 | `GITHUB_REPO` | 备份目标仓库 | 格式：`owner/repo-name` |
| 微信 API Key | `WECHAT_API_KEY` | wx.limyai.com API Key | 在 [wx.limyai.com](https://wx.limyai.com) 授权获取 |
| 微信 AppID | `WECHAT_APPID` | 公众号 AppID | 配置时自动列出已授权公众号，若没列出，请前往[微信公众平台](https://mp.weixin.qq.com/?spm=5176.28103460.0.0.788b2988y6yh0I) 获取AppID|
| 排版主题 | `WECHAT_THEME` | 微信排版主题 | 默认 `sspai`（少数派风格） |

### 配置文件示例

`config.json`:

```json
{
  "github": {
    "token": "ghp_xxxxxxxxxxxx",
    "repo": "your-username/your-backup-repo",
    "branch": "main"
  },
  "wechat": {
    "api_key": "xhs_xxxxxxxxxxxx",
    "appid": "wxef8076005687e866",
    "author": "AI自动生成",
    "theme": "sspai"
  },
  "xiaohu_format": {
    "skill_path": "/path/to/xiaohu-wechat-format"
  }
}
```

---

## 使用方式

### 方式一：Claude Skill 调用

在 Claude Code 对话中，当用户请求包含以下关键词时触发：

| 关键词 | 动作 |
|--------|------|
| `GitHub 备份`、`推送到 GitHub`、`保存到仓库` | 执行 GitHub 推送 |
| `微信公众号`、`发布到公众号`、`推送微信` | 执行微信排版+发布 |
| `github-wechat-publisher` | 执行完整流程 |

**示例对话：**

```
用户: 爬取今天的 HuggingFace Papers Trending，生成日报，备份到 GitHub 并发布到微信公众号

Claude 执行:
1. [自己完成] 使用 WebFetch 爬取数据，生成 Markdown 报告
2. [调用 skill] 将 Markdown 传给 github-wechat-publisher
3. [skill 完成] GitHub 推送 + 微信排版发布
```

### 方式二：Python 模块调用

```python
from scripts.main import GithubWechatPublisher

# 创建实例
publisher = GithubWechatPublisher()

# 执行完整发布
result = publisher.publish(
    title="HuggingFace Papers 日报 - 2026年05月02日",
    content="# 报告内容\n...",
    push_github=True,
    push_wechat=True
)

# 仅推送到 GitHub
result = publisher.publish_github_only(
    title="报告标题",
    content="# 内容..."
)

# 仅发布到微信公众号
result = publisher.publish_wechat_only(
    title="报告标题",
    content="# 内容..."
)
```

### 方式三：命令行调用

```bash
# 从文件读取并发布（完整流程）
python3 scripts/main.py --file report.md --title "日报标题"

# 只推送到 GitHub
python3 scripts/main.py --file report.md --title "日报标题" --no-wechat

# 只发布到微信
python3 scripts/main.py --file report.md --title "日报标题" --no-github

# 直接传入内容
python3 scripts/main.py --content "# 报告\n内容..." --title "日报标题"

# 测试配置连接
python3 scripts/main.py --test

# 运行配置向导
python3 scripts/main.py --setup
```

---

## API 参考

### `GithubWechatPublisher.publish()`

```python
publisher.publish(
    title: str,                    # 文章标题
    content: str,                  # Markdown 内容
    push_github: bool = True,      # 是否 GitHub 备份
    push_wechat: bool = True,      # 是否微信发布
    github_path: str = None,       # GitHub 文件路径（默认 daily/YYYY-MM-DD.md）
    github_message: str = None,    # GitHub 提交信息
    summary: str = None            # 微信文章摘要
) -> dict
```

**返回值：**

```python
{
    "success": True,
    "steps": {
        "github": {"success": True, "path": "daily/2026-05-02.md"},
        "wechat": {"success": True}
    }
}
```

### `GithubWechatPublisher.publish_github_only()`

仅推送到 GitHub：

```python
publisher.publish_github_only(title, content, github_path=None)
```

### `GithubWechatPublisher.publish_wechat_only()`

仅发布到微信公众号：

```python
publisher.publish_wechat_only(title, content, summary=None)
```

---

## 微信排版主题

集成 [xiaohu-wechat-format](https://github.com/xiaohuailabs/xiaohu-wechat-format)，支持 30+ 主题：

| 主题 ID | 风格描述 |
|---------|----------|
| `sspai` | 少数派科技风格（默认） |
| `bytedance` | 字节跳动风格 |
| `github` | GitHub 风格 |
| `newspaper` | 报纸风格 |
| `magazine` | 杂志风格 |
| `midnight` | 深色风格 |
| `ink` | 纯黑极简 |
| `terracotta` | 温暖橙色 |

查看完整主题列表：[xiaohu-wechat-format themes](https://github.com/xiaohuailabs/xiaohu-wechat-format#themes-30)

---

## 目录结构

```
github-wechat-publisher/
├── README.md                 # 本文档
├── SKILL.md                  # Claude Code Skill 说明
├── config.json               # 配置文件
├── scripts/
│   ├── main.py               # 主入口（publish 方法）
│   ├── setup.py              # 配置向导
│   ├── github_push.py        # GitHub 备份模块
│   └── wechat_publish.py     # 微信排版+发布模块
└── templates/
    └── report.md.j2          # 报告模板
```

---

## 依赖

```
Python >= 3.8
markdown >= 3.4
requests >= 2.28
```

安装依赖：

```bash
pip3 install markdown requests
```

---

## 注意事项

1. **GitHub Token 权限**：需要 `repo` 权限才能推送文件到仓库
2. **微信 API 来源**：使用 [wx.limyai.com](https://wx.limyai.com) 提供的 OpenAPI
3. **公众号授权**：需提前在 wx.limyai.com 授权你的公众号
4. **排版依赖**：微信排版功能需要安装 [xiaohu-wechat-format](https://github.com/xiaohuailabs/xiaohu-wechat-format) skill

---

## 定时任务配置

配置系统级 crontab 实现自动化：

```bash
# 编辑 crontab
sudo nano /etc/cron.d/github-wechat-publisher

# 内容示例（每天 7:00 执行）
0 7 * * * root cd ~/.agents/skills/github-wechat-publisher && \
    export GITHUB_TOKEN=ghp_xxx && \
    export WECHAT_API_KEY=xhs_xxx && \
    python3 scripts/main.py --file /path/to/daily_report.md --title "日报" \
    >> /var/log/github-wechat-publisher.log 2>&1
```

---

## 相关链接

- [xiaohu-wechat-format](https://github.com/xiaohuailabs/xiaohu-wechat-format) - 微信公众号排版工具
- [wx.limyai.com](https://wx.limyai.com) - 微信公众号 OpenAPI 平台

---

## License

[MIT](LICENSE)

---

## 贡献

欢迎提交 Issue 和 Pull Request！
