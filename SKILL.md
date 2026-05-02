# github-wechat-publisher

**Markdown 内容 → GitHub 仓库备份 + 微信公众号发布** 后处理 Skill

当 Claude 完成数据爬取生成 Markdown 后，调用此 skill 执行备份和发布。

## 功能定位

| 步骤 | 执行者 | 说明 |
|------|--------|------|
| 🔍 数据爬取 | **Claude** | 使用 WebFetch/WebSearch 等工具完成 |
| 📤 GitHub 备份 | **本 Skill** | 推送 Markdown 到指定仓库 |
| 🎨 微信排版 | **本 Skill** | 使用 xiaohu-wechat-format 排版 |
| 📱 公众号发布 | **本 Skill** | 发布到草稿箱 |

## 触发场景

当用户请求中包含以下关键词时，应调用此 skill：

| 关键词 | 动作 |
|--------|------|
| `GitHub 备份`、`推送到 GitHub`、`保存到仓库` | 执行 GitHub 推送 |
| `微信公众号`、`发布到公众号`、`推送微信` | 执行微信排版+发布 |
| `github-wechat-publisher` | 执行完整流程 |

## 使用方式

### Claude 调用示例

```
用户: 爬取今天的 HuggingFace Papers Trending，生成日报，备份到 GitHub 并发布到微信公众号

Claude 执行流程:
1. [自己完成] 使用 WebFetch 爬取数据，生成 Markdown 报告
2. [调用 skill] 将 Markdown 传给 github-wechat-publisher
3. [skill 完成] GitHub 推送 + 微信排版发布
```

### 调用方法

**Python 模块调用**（推荐）：

```python
from scripts.main import GithubWechatPublisher

# 创建实例
publisher = GithubWechatPublisher()

# 执行发布（Claude 传入已生成的 Markdown）
result = publisher.publish(
    title="日报标题",
    content="# 报告内容\n...",
    push_github=True,      # 是否 GitHub 备份
    push_wechat=True       # 是否微信发布
)
```

**命令行调用**（传入 Markdown 文件）：

```bash
# 从文件读取并发布
python3 scripts/main.py --file report.md --title "日报标题"

# 只推送 GitHub
python3 scripts/main.py --file report.md --title "日报标题" --no-wechat

# 只发布微信
python3 scripts/main.py --file report.md --title "日报标题" --no-github
```

## 配置项

首次使用需运行配置向导：

```bash
python3 scripts/setup.py
```

| 配置项 | 环境变量 | 说明 |
|--------|----------|------|
| GitHub Token | `GITHUB_TOKEN` | 推送文件到仓库（需 `repo` 权限） |
| GitHub 仓库 | `GITHUB_REPO` | 格式：`owner/repo-name` |
| 微信 API Key | `WECHAT_API_KEY` | wx.limyai.com 的 API Key |
| 微信 AppID | `WECHAT_APPID` | 公众号 AppID |
| 排版主题 | `WECHAT_THEME` | 默认 `sspai`（少数派风格） |

## API 说明

### `publish()` 方法

```python
publisher.publish(
    title: str,              # 文章标题
    content: str,            # Markdown 内容
    push_github: bool = True,    # 是否 GitHub 备份
    push_wechat: bool = True,    # 是否微信发布
    github_path: str = None,     # GitHub 文件路径（默认 daily/YYYY-MM-DD.md）
    github_message: str = None   # 提交信息
) -> dict                    # 返回结果 {"success": bool, "steps": {...}}
```

### 返回值结构

```python
{
    "success": True,          # 整体是否成功
    "steps": {
        "github": {"success": True, "path": "daily/2026-05-02.md"},
        "wechat": {"success": True, "media_id": "xxx"}
    }
}
```

## 目录结构

```
github-wechat-publisher/
├── SKILL.md                 # 本文档
├── config.json              # 配置文件
├── scripts/
│   ├── main.py              # 主入口（publish 方法）
│   ├── setup.py             # 配置向导
│   ├── github_push.py       # GitHub 备份模块
│   └── wechat_publish.py    # 微信排版+发布模块
├── templates/
└── themes/
```

## 微信排版主题

集成 xiaohu-wechat-format，支持 30+ 主题：

| 主题 ID | 风格 |
|---------|------|
| `sspai` | 少数派科技风格（默认） |
| `bytedance` | 字节跳动风格 |
| `github` | GitHub 风格 |
| `newspaper` | 报纸风格 |
| `midnight` | 深色风格 |

## 注意事项

1. **数据爬取由 Claude 完成**，skill 只接收 Markdown 结果
2. **GitHub Token** 需要 `repo` 权限
3. **微信 API** 来自 [wx.limyai.com](https://wx.limyai.com)
4. **可选择性执行**：只备份、只发布、或两者都执行

## License

MIT