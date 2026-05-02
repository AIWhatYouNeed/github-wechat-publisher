#!/usr/bin/env python3
"""
github-wechat-publisher 配置向导
交互式引导用户配置 GitHub Token、仓库、微信 API 等信息
"""
import json
import os
import sys
from pathlib import Path

# 配置文件路径
CONFIG_FILE = Path(__file__).parent.parent / "config.json"


def load_config():
    """加载配置文件"""
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {
        "github": {"token": "", "repo": "", "branch": "main"},
        "wechat": {"api_key": "", "appid": "", "author": "AI自动生成", "theme": "sspai"},
        "tasks": {},
        "xiaohu_format": {"skill_path": "/root/.agents/skills/xiaohu-wechat-format"}
    }


def save_config(config):
    """保存配置文件"""
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)
    print(f"\n✅ 配置已保存到: {CONFIG_FILE}")


def print_header(title):
    """打印标题"""
    print("\n" + "=" * 50)
    print(f"  {title}")
    print("=" * 50)


def input_with_default(prompt, default="", required=True):
    """带默认值的输入"""
    if default:
        hint = f" (默认: {default})" if default else ""
        user_input = input(f"{prompt}{hint}: ").strip()
        return user_input if user_input else default
    else:
        while True:
            user_input = input(f"{prompt}: ").strip()
            if user_input or not required:
                return user_input
            print("❌ 此项为必填项，请重新输入")


def select_from_list(prompt, options, default_index=0):
    """从列表中选择"""
    print(f"\n{prompt}")
    for i, opt in enumerate(options):
        marker = "👉" if i == default_index else "  "
        print(f"  {marker} {i+1}. {opt}")
    
    while True:
        try:
            choice = input(f"请选择 (1-{len(options)}, 默认 {default_index+1}): ").strip()
            if not choice:
                return options[default_index]
            idx = int(choice) - 1
            if 0 <= idx < len(options):
                return options[idx]
            print(f"❌ 请输入 1-{len(options)} 之间的数字")
        except ValueError:
            print("❌ 请输入有效数字")


def test_github_token(token, repo):
    """测试 GitHub Token 是否有效"""
    import requests
    
    if not token or not repo:
        return False, "Token 或仓库未配置"
    
    try:
        owner, name = repo.split('/')
        url = f"https://api.github.com/repos/{owner}/{name}"
        headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"}
        resp = requests.get(url, headers=headers, timeout=10)
        
        if resp.status_code == 200:
            return True, "连接成功"
        elif resp.status_code == 401:
            return False, "Token 无效或已过期"
        elif resp.status_code == 404:
            return False, "仓库不存在或无访问权限"
        else:
            return False, f"错误: HTTP {resp.status_code}"
    except Exception as e:
        return False, f"连接失败: {e}"


def test_wechat_api(api_key, appid):
    """测试微信 API 是否有效"""
    import requests
    
    if not api_key:
        return False, "API Key 未配置"
    
    try:
        url = "https://wx.limyai.com/api/openapi/wechat-accounts"
        headers = {"X-API-Key": api_key, "Content-Type": "application/json"}
        resp = requests.post(url, headers=headers, json={}, timeout=10)
        data = resp.json()
        
        if data.get("success"):
            accounts = data.get("data", [])
            if appid:
                # 检查配置的 appid 是否在授权列表中
                for acc in accounts:
                    if acc.get("appid") == appid:
                        return True, f"已授权: {acc.get('name', appid)}"
                return False, f"AppID {appid} 未授权，可用: {[a.get('appid') for a in accounts]}"
            return True, f"可用公众号: {len(accounts)} 个"
        else:
            return False, data.get("error", "未知错误")
    except Exception as e:
        return False, f"连接失败: {e}"


def configure_github(config):
    """配置 GitHub"""
    print_header("📦 GitHub 配置")
    
    print("""
GitHub Token 用于推送文件到你的仓库。

获取方式：
  1. 访问 https://github.com/settings/tokens
  2. 点击 "Generate new token (classic)"
  3. 勾选 "repo" 权限
  4. 生成并复制 Token
""")
    
    current = config.get("github", {})
    
    token = input_with_default(
        "GitHub Token (ghp_...)", 
        current.get("token", ""),
        required=True
    )
    
    repo = input_with_default(
        "GitHub 仓库 (格式: owner/repo-name)",
        current.get("repo", ""),
        required=True
    )
    
    branch = input_with_default(
        "分支名称",
        current.get("branch", "main"),
        required=False
    )
    
    # 测试连接
    print("\n🔍 测试 GitHub 连接...")
    success, message = test_github_token(token, repo)
    
    if success:
        print(f"✅ {message}")
        config["github"] = {
            "token": token,
            "repo": repo,
            "branch": branch
        }
        return True
    else:
        print(f"❌ {message}")
        retry = input("是否重新配置? (y/n): ").strip().lower()
        if retry == 'y':
            return configure_github(config)
        return False


def configure_wechat(config):
    """配置微信公众号"""
    print_header("📱 微信公众号配置")
    
    print("""
微信公众号 API 配置。

当前使用 wx.limyai.com 提供的 OpenAPI：
  - 需要提前在该平台授权你的公众号
  - 获取 API Key 后配置即可使用
""")
    
    current = config.get("wechat", {})
    
    api_key = input_with_default(
        "微信 API Key (xhs_...)",
        current.get("api_key", ""),
        required=True
    )
    
    # 先测试 API Key，获取可用公众号列表
    print("\n🔍 获取已授权公众号列表...")
    
    import requests
    try:
        url = "https://wx.limyai.com/api/openapi/wechat-accounts"
        headers = {"X-API-Key": api_key, "Content-Type": "application/json"}
        resp = requests.post(url, headers=headers, json={}, timeout=10)
        data = resp.json()
        
        if data.get("success"):
            accounts = data.get("data", [])
            if not accounts:
                print("❌ 没有已授权的公众号，请先在 wx.limyai.com 授权")
                return False
            
            print(f"\n已授权 {len(accounts)} 个公众号:")
            for i, acc in enumerate(accounts):
                print(f"  {i+1}. {acc.get('name', '未知')} ({acc.get('appid', '')})")
            
            # 选择公众号
            default_appid = current.get("appid", "")
            default_idx = 0
            for i, acc in enumerate(accounts):
                if acc.get("appid") == default_appid:
                    default_idx = i
                    break
            
            while True:
                try:
                    choice = input(f"\n请选择公众号 (1-{len(accounts)}, 默认 {default_idx+1}): ").strip()
                    if not choice:
                        idx = default_idx
                    else:
                        idx = int(choice) - 1
                    
                    if 0 <= idx < len(accounts):
                        selected = accounts[idx]
                        appid = selected.get("appid")
                        author = selected.get("name", "AI自动生成")
                        break
                    print(f"❌ 请输入 1-{len(accounts)} 之间的数字")
                except ValueError:
                    print("❌ 请输入有效数字")
        else:
            print(f"❌ 获取公众号列表失败: {data.get('error', '未知错误')}")
            return False
            
    except Exception as e:
        print(f"❌ 连接失败: {e}")
        return False
    
    # 选择排版主题
    print("\n🎨 微信排版主题:")
    themes = [
        ("sspai", "少数派科技风格（推荐）"),
        ("bytedance", "字节跳动风格"),
        ("github", "GitHub 风格"),
        ("newspaper", "报纸风格"),
        ("magazine", "杂志风格"),
        ("midnight", "午夜暗黑风格"),
    ]
    
    for i, (tid, tname) in enumerate(themes):
        print(f"  {i+1}. {tname}")
    
    current_theme = current.get("theme", "sspai")
    default_theme_idx = 0
    for i, (tid, _) in enumerate(themes):
        if tid == current_theme:
            default_theme_idx = i
            break
    
    while True:
        try:
            choice = input(f"请选择主题 (1-{len(themes)}, 默认 {default_theme_idx+1}): ").strip()
            if not choice:
                theme = themes[default_theme_idx][0]
            else:
                idx = int(choice) - 1
                if 0 <= idx < len(themes):
                    theme = themes[idx][0]
                else:
                    continue
            
            config["wechat"] = {
                "api_key": api_key,
                "appid": appid,
                "author": author,
                "theme": theme
            }
            print(f"\n✅ 已选择: {dict(themes).get(theme, theme)}")
            return True
        except ValueError:
            print("❌ 请输入有效数字")


def configure_tasks(config):
    """配置任务"""
    print_header("📋 任务配置")
    
    print("""
内置任务模板：
  1. hf-papers    - HuggingFace Papers Trending 日报
  2. github-trending - GitHub Trending 监控
""")
    
    tasks = config.get("tasks", {})
    
    # HuggingFace Papers
    enable_hf = input("启用 HuggingFace Papers 日报? (y/n, 默认 y): ").strip().lower()
    if enable_hf != 'n':
        top_n = input("爬取前几篇论文? (默认 5): ").strip()
        tasks["hf-papers"] = {
            "enabled": True,
            "top_n": int(top_n) if top_n.isdigit() else 5,
            "summary_detail": "detailed"
        }
    else:
        tasks["hf-papers"] = {"enabled": False}
    
    # GitHub Trending
    enable_gh = input("启用 GitHub Trending 监控? (y/n, 默认 n): ").strip().lower()
    if enable_gh == 'y':
        keywords = input("关注关键词 (逗号分隔, 默认: agent,skills): ").strip()
        tasks["github-trending"] = {
            "enabled": True,
            "keywords": [k.strip() for k in keywords.split(',')] if keywords else ["agent", "skills"],
            "top_n": 10
        }
    else:
        tasks["github-trending"] = {"enabled": False}
    
    config["tasks"] = tasks
    return True


def show_summary(config):
    """显示配置摘要"""
    print_header("📊 配置摘要")
    
    github = config.get("github", {})
    wechat = config.get("wechat", {})
    tasks = config.get("tasks", {})
    
    print(f"""
📦 GitHub:
   仓库: {github.get('repo', '未配置')}
   分支: {github.get('branch', 'main')}

📱 微信公众号:
   AppID: {wechat.get('appid', '未配置')}
   作者: {wechat.get('author', '未配置')}
   主题: {wechat.get('theme', 'sspai')}

📋 任务:
   HuggingFace Papers: {'✅ 启用' if tasks.get('hf-papers', {}).get('enabled') else '❌ 禁用'}
   GitHub Trending: {'✅ 启用' if tasks.get('github-trending', {}).get('enabled') else '❌ 禁用'}
""")


def main():
    """主函数"""
    print("""
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║       🚀 github-wechat-publisher 配置向导                      ║
║                                                           ║
║   数据爬取 → GitHub 推送 → 微信公众号发布                  ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
""")
    
    # 加载现有配置
    config = load_config()
    
    # 步骤选择
    print("请选择配置步骤:")
    print("  1. 完整配置（推荐首次使用）")
    print("  2. 仅配置 GitHub")
    print("  3. 仅配置微信公众号")
    print("  4. 配置任务")
    print("  5. 查看当前配置")
    print("  0. 退出")
    
    choice = input("\n请选择 (0-5): ").strip()
    
    if choice == '1':
        # 完整配置
        if configure_github(config):
            if configure_wechat(config):
                configure_tasks(config)
                show_summary(config)
                save_config(config)
                print("\n🎉 配置完成！现在可以使用 github-wechat-post 发布内容了。")
    elif choice == '2':
        if configure_github(config):
            save_config(config)
    elif choice == '3':
        if configure_wechat(config):
            save_config(config)
    elif choice == '4':
        configure_tasks(config)
        save_config(config)
    elif choice == '5':
        show_summary(config)
        print(f"配置文件位置: {CONFIG_FILE}")
    elif choice == '0':
        print("再见！")
        sys.exit(0)
    else:
        print("❌ 无效选择")
        main()


if __name__ == "__main__":
    main()