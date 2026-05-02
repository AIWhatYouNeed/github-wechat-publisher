#!/usr/bin/env python3
"""
GitHub 推送模块
支持文件推送、仓库操作等功能
"""
import base64
import json
import os
import requests
from pathlib import Path
from typing import Optional, Tuple, List


class GitHubPush:
    """GitHub 文件推送类"""
    
    def __init__(self, token: str = None, repo: str = None, branch: str = "main"):
        """
        初始化 GitHub 推送实例
        
        参数:
            token: GitHub Personal Access Token
            repo: 仓库名称，格式 "owner/repo-name"
            branch: 分支名称，默认 main
        """
        self.token = token or os.environ.get("GITHUB_TOKEN", "")
        self.repo = repo or os.environ.get("GITHUB_REPO", "")
        self.branch = branch
        
        if "/" in self.repo:
            self.owner, self.repo_name = self.repo.split("/", 1)
        else:
            self.owner = ""
            self.repo_name = self.repo
    
    def _api_request(self, method: str, path: str, data: dict = None) -> dict:
        """发送 GitHub API 请求"""
        url = f"https://api.github.com/repos/{self.owner}/{self.repo_name}/{path}"
        headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        try:
            resp = requests.request(method, url, headers=headers, json=data, timeout=30)
            if resp.status_code in (200, 201):
                return {"success": True, "data": resp.json()}
            else:
                try:
                    error = resp.json().get("message", resp.text)
                except:
                    error = resp.text
                return {"success": False, "error": f"HTTP {resp.status_code}: {error}"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_file_sha(self, path: str) -> Optional[str]:
        """获取文件的 SHA 值（用于更新文件）"""
        result = self._api_request("GET", f"contents/{path}?ref={self.branch}")
        if result["success"]:
            return result["data"].get("sha")
        return None
    
    def push_file(
        self, 
        path: str, 
        content: str, 
        message: str = "Update file",
        encoding: str = "utf-8"
    ) -> Tuple[bool, str]:
        """
        推送文件到 GitHub 仓库
        
        参数:
            path: 文件路径（相对于仓库根目录）
            content: 文件内容
            message: 提交信息
            encoding: 内容编码
        
        返回:
            (success, message)
        """
        if not self.token:
            return False, "GitHub Token 未配置"
        if not self.repo:
            return False, "GitHub 仓库未配置"
        
        # 获取已有文件的 SHA（用于更新）
        sha = self.get_file_sha(path)
        
        # Base64 编码内容
        encoded_content = base64.b64encode(content.encode(encoding)).decode("utf-8")
        
        # 构建请求数据
        data = {
            "message": message,
            "content": encoded_content,
            "branch": self.branch
        }
        
        # 如果文件已存在，添加 SHA
        if sha:
            data["sha"] = sha
        
        # 推送文件
        result = self._api_request("PUT", f"contents/{path}", data)
        
        if result["success"]:
            url = f"https://github.com/{self.repo}/blob/{self.branch}/{path}"
            return True, f"推送成功: {url}"
        else:
            return False, result["error"]
    
    def push_multiple_files(
        self, 
        files: List[Tuple[str, str, str]],  # [(path, content, message), ...]
    ) -> Tuple[int, List[str]]:
        """
        批量推送多个文件
        
        参数:
            files: 文件列表，每个元素为 (path, content, message)
        
        返回:
            (success_count, error_messages)
        """
        success_count = 0
        errors = []
        
        for path, content, message in files:
            success, msg = self.push_file(path, content, message)
            if success:
                success_count += 1
            else:
                errors.append(f"{path}: {msg}")
        
        return success_count, errors
    
    def file_exists(self, path: str) -> bool:
        """检查文件是否存在"""
        return self.get_file_sha(path) is not None
    
    def get_file_content(self, path: str) -> Optional[str]:
        """获取文件内容"""
        result = self._api_request("GET", f"contents/{path}?ref={self.branch}")
        if result["success"]:
            content_b64 = result["data"].get("content", "")
            try:
                return base64.b64decode(content_b64).decode("utf-8")
            except:
                return None
        return None
    
    def create_readme(self, title: str, description: str, latest_file: str = None) -> Tuple[bool, str]:
        """
        创建或更新 README.md
        
        参数:
            title: 仓库标题
            description: 仓库描述
            latest_file: 最新文件链接
        """
        lines = [
            f"# {title}",
            "",
            f"> {description}",
            ""
        ]
        
        if latest_file:
            lines.append("## 📅 最新更新")
            lines.append("")
            lines.append(f"- [{latest_file}]({latest_file})")
            lines.append("")
        
        lines.extend([
            "---",
            "",
            "*本仓库由自动化任务维护。*"
        ])
        
        readme_content = "\n".join(lines)
        return self.push_file("README.md", readme_content, "📖 更新 README")


# 便捷函数
def push_to_github(
    content: str,
    path: str,
    message: str = "Update file",
    token: str = None,
    repo: str = None
) -> Tuple[bool, str]:
    """
    便捷函数：推送文件到 GitHub
    
    参数:
        content: 文件内容
        path: 文件路径
        message: 提交信息
        token: GitHub Token（可选，默认从环境变量读取）
        repo: 仓库名称（可选，默认从环境变量读取）
    
    返回:
        (success, message)
    """
    pusher = GitHubPush(token=token, repo=repo)
    return pusher.push_file(path, content, message)


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "--test":
            # 测试连接
            pusher = GitHubPush()
            if pusher.token and pusher.repo:
                result = pusher._api_request("GET", "")
                if result["success"]:
                    print(f"✅ 连接成功: {pusher.repo}")
                else:
                    print(f"❌ 连接失败: {result['error']}")
            else:
                print("❌ GitHub Token 或仓库未配置")
        else:
            print(f"用法: {sys.argv[0]} --test")
    else:
        # 显示帮助
        print("""
GitHub 推送模块

用法:
    python3 github_push.py --test  # 测试连接

环境变量:
    GITHUB_TOKEN: GitHub Personal Access Token
    GITHUB_REPO: 仓库名称 (格式: owner/repo)
""")