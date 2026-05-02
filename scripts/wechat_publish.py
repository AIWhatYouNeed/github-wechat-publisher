#!/usr/bin/env python3
"""
微信公众号发布模块
集成 xiaohu-wechat-format 排版引擎，发布到草稿箱
"""
import json
import os
import re
import sys
import tempfile
from pathlib import Path
from typing import Optional, Tuple
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

# 默认配置
API_BASE_URL = "https://wx.limyai.com/api/openapi"
XIAOHU_SKILL_PATH = Path("/root/.agents/skills/xiaohu-wechat-format")


class WeChatPublisher:
    """微信公众号发布类"""
    
    def __init__(
        self,
        api_key: str = None,
        appid: str = None,
        author: str = "AI自动生成",
        theme: str = "sspai",
        xiaohu_skill_path: str = None
    ):
        """
        初始化微信公众号发布实例
        
        参数:
            api_key: wx.limyai.com API Key
            appid: 微信公众号 AppID
            author: 文章作者
            theme: 排版主题（默认 sspai 少数派风格）
            xiaohu_skill_path: xiaohu-wechat-format skill 路径
        """
        self.api_key = api_key or os.environ.get("WECHAT_API_KEY", "")
        self.appid = appid or os.environ.get("WECHAT_APPID", "")
        self.author = author
        self.theme = theme or os.environ.get("WECHAT_THEME", "sspai")
        self.xiaohu_path = Path(xiaohu_skill_path) if xiaohu_skill_path else XIAOHU_SKILL_PATH
    
    def _make_api_request(self, endpoint: str, data: dict = None) -> dict:
        """发送微信 API 请求"""
        if not self.api_key:
            return {"success": False, "error": "WECHAT_API_KEY 未配置"}
        
        url = f"{API_BASE_URL}{endpoint}"
        headers = {
            "X-API-Key": self.api_key,
            "Content-Type": "application/json"
        }
        
        body = json.dumps(data or {}).encode("utf-8")
        
        try:
            request = Request(url, data=body, headers=headers, method="POST")
            with urlopen(request, timeout=60) as response:
                return json.loads(response.read().decode("utf-8"))
        except HTTPError as e:
            error_body = e.read().decode("utf-8") if e.fp else ""
            try:
                return json.loads(error_body)
            except:
                return {"success": False, "error": f"HTTP {e.code}: {error_body[:200]}"}
        except URLError as e:
            return {"success": False, "error": f"网络错误: {e.reason}"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def list_accounts(self) -> list:
        """列出已授权的微信公众号"""
        result = self._make_api_request("/wechat-accounts")
        if result.get("success"):
            return result.get("data", [])
        return []
    
    def publish_article(
        self,
        title: str,
        content: str,
        summary: str = None,
        content_format: str = "html"
    ) -> Tuple[bool, str]:
        """
        发布文章到微信公众号草稿箱
        
        参数:
            title: 文章标题（最长64字符）
            content: 文章内容（HTML格式）
            summary: 文章摘要（最长120字符）
            content_format: 内容格式，默认 html
        
        返回:
            (success, message)
        """
        data = {
            "wechatAppid": self.appid,
            "title": title[:64],
            "content": content,
            "contentFormat": content_format,
            "articleType": "news"
        }
        
        if summary:
            data["summary"] = summary[:120]
        if self.author:
            data["author"] = self.author
        
        result = self._make_api_request("/wechat-publish", data)
        
        if result.get("success"):
            media_id = result.get("data", {}).get("mediaId", "")
            return True, f"发布成功，media_id: {media_id}"
        else:
            error = result.get("error") or result.get("message") or "未知错误"
            return False, f"发布失败: {error}"
    
    def format_with_xiaohu(self, markdown_content: str, theme: str = None) -> Optional[str]:
        """
        使用 xiaohu-wechat-format 进行排版
        
        参数:
            markdown_content: Markdown 格式的文章内容
            theme: 主题名称（覆盖默认主题）
        
        返回:
            HTML 内容，失败返回 None
        """
        theme = theme or self.theme
        
        # 检查 skill 路径
        scripts_dir = self.xiaohu_path / "scripts"
        if not scripts_dir.exists():
            print(f"[!] xiaohu-wechat-format 未找到: {self.xiaohu_path}")
            return None
        
        # 临时保存 Markdown 文件
        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.md', delete=False, encoding='utf-8'
        ) as f:
            f.write(markdown_content)
            temp_input = f.name
        
        try:
            # 导入排版模块
            sys.path.insert(0, str(scripts_dir))
            
            from format import (
                load_theme,
                inject_inline_styles,
                extract_links_as_footnotes,
                md_to_html,
                strip_frontmatter,
                process_callouts,
                process_manual_footnotes,
                process_fenced_containers,
                convert_wikilinks,
                copy_markdown_images,
                convert_image_captions,
            )
            
            input_path = Path(temp_input)
            output_dir = Path("/tmp/wechat-format/github-wechat-post")
            vault_root = Path("/tmp")
            
            # 加载主题
            theme_data = load_theme(theme)
            
            # 处理流程
            content = markdown_content
            content = strip_frontmatter(content)
            content = process_callouts(content)
            content = process_manual_footnotes(content)
            content = process_fenced_containers(content)
            content = re.sub(r'~~(.+?)~~', r'<del>\1</del>', content)
            
            output_dir.mkdir(parents=True, exist_ok=True)
            content = convert_wikilinks(content, vault_root, output_dir)
            content = copy_markdown_images(content, input_path.parent, output_dir)
            
            # Markdown → HTML
            html = md_to_html(content)
            html, footnote_html = extract_links_as_footnotes(html)
            
            # 注入内联样式
            html = inject_inline_styles(html, theme_data)
            if footnote_html:
                footnote_html = inject_inline_styles(footnote_html, theme_data, skip_wrapper=True)
            
            # 处理图片图说
            html = convert_image_captions(html)
            if footnote_html:
                footnote_html = convert_image_captions(footnote_html)
            
            # 合并正文和脚注
            full_html = html
            if footnote_html:
                full_html += "\n" + footnote_html
            
            return full_html
            
        except ImportError as e:
            print(f"[!] 导入 xiaohu-wechat-format 模块失败: {e}")
            print(f"    请确保已安装: cd ~/.agents/skills && git clone https://github.com/xiaohuailabs/xiaohu-wechat-format.git")
            return None
        except Exception as e:
            print(f"[!] xiaohu-wechat-format 排版失败: {e}")
            return None
        finally:
            # 清理
            try:
                os.unlink(temp_input)
            except:
                pass
            # 清理 sys.path
            if str(scripts_dir) in sys.path:
                sys.path.remove(str(scripts_dir))
    
    def publish_markdown(
        self,
        markdown_content: str,
        title: str = None,
        summary: str = None,
        theme: str = None
    ) -> Tuple[bool, str]:
        """
        完整流程：Markdown → 排版 → 发布到微信公众号
        
        参数:
            markdown_content: Markdown 格式的文章内容
            title: 文章标题（自动从 Markdown 提取）
            summary: 文章摘要
            theme: 主题名称（覆盖默认主题）
        
        返回:
            (success, message)
        """
        # 排版
        print(f"[*] 使用 xiaohu-wechat-format 排版（主题: {theme or self.theme}）...")
        html_content = self.format_with_xiaohu(markdown_content, theme)
        
        if not html_content:
            return False, "排版失败"
        
        print("  [+] 排版完成")
        
        # 提取标题
        if not title:
            title_match = re.search(r'^#\s+(.+)$', markdown_content, re.MULTILINE)
            title = title_match.group(1).strip() if title_match else "未命名文章"
        
        # 发布
        return self.publish_article(
            title=title,
            content=html_content,
            summary=summary,
            content_format="html"
        )


# 便捷函数
def publish_to_wechat(
    markdown_content: str,
    title: str = None,
    summary: str = None,
    api_key: str = None,
    appid: str = None,
    theme: str = "sspai"
) -> Tuple[bool, str]:
    """
    便捷函数：Markdown → 排版 → 发布到微信公众号
    
    参数:
        markdown_content: Markdown 格式的文章内容
        title: 文章标题
        summary: 文章摘要
        api_key: 微信 API Key
        appid: 微信公众号 AppID
        theme: 排版主题
    
    返回:
        (success, message)
    """
    publisher = WeChatPublisher(api_key=api_key, appid=appid, theme=theme)
    return publisher.publish_markdown(markdown_content, title, summary)


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "--list-accounts":
            publisher = WeChatPublisher()
            accounts = publisher.list_accounts()
            if accounts:
                for acc in accounts:
                    print(f"  - {acc.get('name', '未知')} ({acc.get('appid', '')})")
            else:
                print("❌ 未找到已授权的公众号")
        else:
            # 从文件发布
            filepath = sys.argv[1]
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            success, msg = publish_to_wechat(content)
            print(f"结果: {success}, {msg}")
    else:
        print("""
微信公众号发布模块

用法:
    python3 wechat_publish.py --list-accounts   # 列出已授权公众号
    python3 wechat_publish.py article.md        # 发布文章

环境变量:
    WECHAT_API_KEY: wx.limyai.com API Key
    WECHAT_APPID:   微信公众号 AppID
    WECHAT_THEME:   排版主题 (默认 sspai)
""")