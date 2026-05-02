#!/usr/bin/env python3
"""
github-wechat-publisher 主脚本
Markdown 内容 → GitHub 仓库备份 + 微信公众号发布

使用方式：
  1. Python 调用：publisher.publish(title, content)
  2. 命令行调用：python3 main.py --file report.md --title "标题"
"""
import argparse
import datetime
import json
import os
import sys
from pathlib import Path

# 添加脚本目录到路径
SCRIPTS_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPTS_DIR))

from github_push import GitHubPush
from wechat_publish import WeChatPublisher

# 配置文件
CONFIG_FILE = SCRIPTS_DIR.parent / "config.json"


def load_config() -> dict:
    """加载配置"""
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


class GithubWechatPublisher:
    """github-wechat-publisher 主类
    
    接收 Markdown 内容，执行 GitHub 备份和微信发布。
    数据爬取由 Claude 完成，不在此 skill 内处理。
    """
    
    def __init__(self, config: dict = None):
        """
        初始化
        
        参数:
            config: 配置字典（不传则自动加载）
        """
        self.config = config or load_config()
        
        # 初始化 GitHub 推送
        github_cfg = self.config.get("github", {})
        self.github = GitHubPush(
            token=github_cfg.get("token") or os.environ.get("GITHUB_TOKEN", ""),
            repo=github_cfg.get("repo") or os.environ.get("GITHUB_REPO", ""),
            branch=github_cfg.get("branch", "main")
        )
        
        # 初始化微信发布
        wechat_cfg = self.config.get("wechat", {})
        xiaohu_cfg = self.config.get("xiaohu_format", {})
        self.wechat = WeChatPublisher(
            api_key=wechat_cfg.get("api_key") or os.environ.get("WECHAT_API_KEY", ""),
            appid=wechat_cfg.get("appid") or os.environ.get("WECHAT_APPID", ""),
            author=wechat_cfg.get("author", "AI自动生成"),
            theme=wechat_cfg.get("theme", "sspai"),
            xiaohu_skill_path=xiaohu_cfg.get("skill_path", "")
        )
    
    def publish(
        self,
        title: str,
        content: str,
        push_github: bool = True,
        push_wechat: bool = True,
        github_path: str = None,
        github_message: str = None,
        summary: str = None
    ) -> dict:
        """
        发布 Markdown 内容到 GitHub 和微信公众号
        
        参数:
            title: 文章标题
            content: Markdown 内容
            push_github: 是否推送到 GitHub（默认 True）
            push_wechat: 是否发布到微信公众号（默认 True）
            github_path: GitHub 文件路径（默认 daily/YYYY-MM-DD.md）
            github_message: GitHub 提交信息
            summary: 微信文章摘要
        
        返回:
            {"success": bool, "steps": {"github": {...}, "wechat": {...}}}
        """
        results = {"success": False, "steps": {}}
        date_str = datetime.datetime.now().strftime("%Y-%m-%d")
        
        print("\n" + "=" * 50)
        print("  🚀 github-wechat-publisher 启动")
        print("=" * 50)
        print(f"\n📄 标题: {title}")
        
        # 1. GitHub 备份
        if push_github:
            print("\n[1/2] 📤 推送到 GitHub 仓库备份...")
            
            if not github_path:
                github_path = f"daily/{date_str}.md"
            if not github_message:
                github_message = f"📄 添加 {date_str} 报告"
            
            success, msg = self.github.push_file(github_path, content, github_message)
            
            if success:
                print(f"  [✓] {msg}")
                results["steps"]["github"] = {"success": True, "path": github_path}
                
                # 更新 README
                self.github.create_readme(
                    title=self.github.repo_name,
                    description="自动化报告仓库",
                    latest_file=github_path
                )
            else:
                print(f"  [✗] {msg}")
                results["steps"]["github"] = {"success": False, "error": msg}
        else:
            print("\n[1/2] 📤 跳过 GitHub 备份")
            results["steps"]["github"] = {"success": True, "skipped": True}
        
        # 2. 微信发布
        if push_wechat:
            print("\n[2/2] 📱 发布到微信公众号...")
            success, msg = self.wechat.publish_markdown(
                content,
                title=title,
                summary=summary
            )
            
            if success:
                print(f"  [✓] {msg}")
                results["steps"]["wechat"] = {"success": True}
            else:
                print(f"  [✗] {msg}")
                results["steps"]["wechat"] = {"success": False, "error": msg}
        else:
            print("\n[2/2] 📱 跳过微信发布")
            results["steps"]["wechat"] = {"success": True, "skipped": True}
        
        # 总结
        all_success = all(
            s.get("success", False) for s in results["steps"].values()
        )
        results["success"] = all_success
        
        print("\n" + "=" * 50)
        if all_success:
            print("  ✅ 全部完成！")
        else:
            print("  ⚠️ 部分步骤失败，请查看上方日志")
        print("=" * 50)
        
        return results
    
    def publish_github_only(self, title: str, content: str, github_path: str = None) -> dict:
        """仅推送到 GitHub"""
        return self.publish(title, content, push_github=True, push_wechat=False, github_path=github_path)
    
    def publish_wechat_only(self, title: str, content: str, summary: str = None) -> dict:
        """仅发布到微信公众号"""
        return self.publish(title, content, push_github=False, push_wechat=True, summary=summary)


def main():
    """命令行入口"""
    parser = argparse.ArgumentParser(
        description="github-wechat-publisher: Markdown → GitHub 备份 + 微信公众号发布"
    )
    parser.add_argument("--file", "-f", type=str, help="Markdown 文件路径")
    parser.add_argument("--title", "-t", type=str, help="文章标题")
    parser.add_argument("--content", "-c", type=str, help="Markdown 内容（直接传入）")
    parser.add_argument("--no-github", action="store_true", help="跳过 GitHub 备份")
    parser.add_argument("--no-wechat", action="store_true", help="跳过微信发布")
    parser.add_argument("--setup", action="store_true", help="运行配置向导")
    parser.add_argument("--test", action="store_true", help="测试配置连接")
    
    args = parser.parse_args()
    
    # 配置向导
    if args.setup:
        os.execv(sys.executable, [sys.executable, str(SCRIPTS_DIR / "setup.py")])
        return
    
    # 测试连接
    if args.test:
        config = load_config()
        publisher = GithubWechatPublisher(config)
        
        print("\n🔍 测试 GitHub 连接...")
        if publisher.github.token and publisher.github.repo:
            result = publisher.github._api_request("GET", "")
            if result["success"]:
                print(f"  ✅ GitHub 连接成功: {publisher.github.repo}")
            else:
                print(f"  ❌ GitHub 连接失败: {result.get('error')}")
        else:
            print("  ❌ GitHub 未配置")
        
        print("\n🔍 测试微信连接...")
        accounts = publisher.wechat.list_accounts()
        if accounts:
            print(f"  ✅ 已授权 {len(accounts)} 个公众号:")
            for acc in accounts:
                if isinstance(acc, dict):
                    print(f"     - {acc.get('name', '未知')} ({acc.get('appid', '')})")
                else:
                    print(f"     - {acc}")
        else:
            print("  ❌ 未找到已授权的公众号")
        return
    
    # 获取内容
    content = None
    title = args.title
    
    if args.file:
        file_path = Path(args.file)
        if not file_path.exists():
            print(f"[!] 文件不存在: {args.file}")
            sys.exit(1)
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 从文件内容提取标题（如果未指定）
        if not title:
            import re
            match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
            title = match.group(1) if match else file_path.stem
    
    elif args.content:
        content = args.content
    
    else:
        parser.print_help()
        print("\n示例:")
        print("  python3 main.py --file report.md --title '日报'")
        print("  python3 main.py --content '# 报告\\n内容...' --title '日报'")
        print("  python3 main.py --setup              # 配置向导")
        print("  python3 main.py --test               # 测试连接")
        sys.exit(0)
    
    if not title:
        print("[!] 请指定标题 (--title)")
        sys.exit(1)
    
    # 执行发布
    config = load_config()
    publisher = GithubWechatPublisher(config)
    
    result = publisher.publish(
        title=title,
        content=content,
        push_github=not args.no_github,
        push_wechat=not args.no_wechat
    )
    
    sys.exit(0 if result["success"] else 1)


if __name__ == "__main__":
    main()