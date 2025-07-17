#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sing-box 订阅转换器部署脚本
用于快速设置和部署项目到 GitHub
"""

import os
import sys
import subprocess
import json
from pathlib import Path

class DeployHelper:
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.required_files = [
            'convert_subscription.py',
            'config.json',
            'url.yaml',
            'requirements.txt',
            'README.md',
            '.github/workflows/update-subscription.yml'
        ]
    
    def check_environment(self):
        """检查运行环境"""
        print("🔍 检查运行环境...")
        
        # 检查 Python 版本
        if sys.version_info < (3, 7):
            print("❌ Python 版本过低，需要 3.7+")
            return False
        
        print(f"✅ Python 版本: {sys.version.split()[0]}")
        
        # 检查 Git
        try:
            result = subprocess.run(['git', '--version'], capture_output=True, text=True)
            if result.returncode == 0:
                print(f"✅ Git 版本: {result.stdout.strip()}")
            else:
                print("❌ Git 未安装或不可用")
                return False
        except FileNotFoundError:
            print("❌ Git 未安装")
            return False
        
        return True
    
    def check_project_files(self):
        """检查项目文件完整性"""
        print("\n📁 检查项目文件...")
        
        missing_files = []
        for file_path in self.required_files:
            full_path = self.project_root / file_path
            if full_path.exists():
                print(f"✅ {file_path}")
            else:
                print(f"❌ {file_path} (缺失)")
                missing_files.append(file_path)
        
        if missing_files:
            print(f"\n⚠️ 缺失 {len(missing_files)} 个必要文件")
            return False
        
        print("\n✅ 所有必要文件都存在")
        return True
    
    def validate_config_files(self):
        """验证配置文件格式"""
        print("\n🔧 验证配置文件...")
        
        # 验证 config.json
        try:
            with open(self.project_root / 'config.json', 'r', encoding='utf-8') as f:
                json.load(f)
            print("✅ config.json 格式正确")
        except Exception as e:
            print(f"❌ config.json 格式错误: {e}")
            return False
        
        # 检查 url.yaml
        url_file = self.project_root / 'url.yaml'
        if url_file.exists():
            try:
                with open(url_file, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    if content:
                        print("✅ url.yaml 包含订阅链接")
                    else:
                        print("⚠️ url.yaml 为空，请添加订阅链接")
            except Exception as e:
                print(f"❌ url.yaml 读取错误: {e}")
                return False
        
        return True
    
    def install_dependencies(self):
        """安装 Python 依赖"""
        print("\n📦 安装 Python 依赖...")
        
        try:
            subprocess.run([
                sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'
            ], check=True, cwd=self.project_root)
            print("✅ 依赖安装完成")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ 依赖安装失败: {e}")
            return False
    
    def test_conversion(self):
        """测试订阅转换功能"""
        print("\n🧪 测试订阅转换...")
        
        try:
            result = subprocess.run([
                sys.executable, 'convert_subscription.py'
            ], capture_output=True, text=True, cwd=self.project_root, timeout=60)
            
            if result.returncode == 0:
                print("✅ 订阅转换测试通过")
                
                # 检查生成的文件
                if (self.project_root / 'sing-box_config.json').exists():
                    print("✅ 配置文件生成成功")
                if (self.project_root / 'sing-box.json').exists():
                    print("✅ 代理列表生成成功")
                
                return True
            else:
                print(f"❌ 转换失败: {result.stderr}")
                return False
        except subprocess.TimeoutExpired:
            print("❌ 转换超时")
            return False
        except Exception as e:
            print(f"❌ 转换错误: {e}")
            return False
    
    def init_git_repo(self):
        """初始化 Git 仓库"""
        print("\n🔧 初始化 Git 仓库...")
        
        try:
            # 检查是否已经是 Git 仓库
            result = subprocess.run(['git', 'status'], capture_output=True, cwd=self.project_root)
            if result.returncode == 0:
                print("✅ Git 仓库已存在")
                return True
            
            # 初始化仓库
            subprocess.run(['git', 'init'], check=True, cwd=self.project_root)
            subprocess.run(['git', 'add', '.'], check=True, cwd=self.project_root)
            subprocess.run([
                'git', 'commit', '-m', 'Initial commit: Sing-box subscription converter'
            ], check=True, cwd=self.project_root)
            
            print("✅ Git 仓库初始化完成")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Git 初始化失败: {e}")
            return False
    
    def show_deployment_guide(self):
        """显示部署指南"""
        print("\n" + "="*60)
        print("🚀 GitHub 部署指南")
        print("="*60)
        print()
        print("1. 在 GitHub 上创建新仓库")
        print("   - 访问 https://github.com/new")
        print("   - 仓库名建议: sing-box-subscription")
        print("   - 设置为 Public 或 Private")
        print()
        print("2. 推送代码到 GitHub")
        print("   git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git")
        print("   git branch -M main")
        print("   git push -u origin main")
        print()
        print("3. 配置 GitHub Actions")
        print("   - 工作流文件已自动创建在 .github/workflows/")
        print("   - 支持手动触发和定时执行")
        print("   - 可在 Actions 页面查看执行状态")
        print()
        print("4. 手动触发工作流")
        print("   - 进入仓库的 Actions 页面")
        print("   - 选择 'Update Sing-box Subscription' 工作流")
        print("   - 点击 'Run workflow' 按钮")
        print()
        print("5. 配置订阅链接")
        print("   - 编辑 url.yaml 文件添加你的订阅链接")
        print("   - 提交更改将自动触发工作流")
        print()
        print("📝 注意事项:")
        print("   - 确保订阅链接的有效性")
        print("   - 生成的配置文件仅供学习研究使用")
        print("   - 请遵守当地法律法规")
        print()
    
    def run_deployment_check(self):
        """运行完整的部署检查"""
        print("🚀 Sing-box 订阅转换器部署检查")
        print("="*50)
        
        checks = [
            ("环境检查", self.check_environment),
            ("文件检查", self.check_project_files),
            ("配置验证", self.validate_config_files),
            ("依赖安装", self.install_dependencies),
            ("功能测试", self.test_conversion),
            ("Git 初始化", self.init_git_repo)
        ]
        
        failed_checks = []
        
        for check_name, check_func in checks:
            print(f"\n{'='*20} {check_name} {'='*20}")
            try:
                if not check_func():
                    failed_checks.append(check_name)
            except Exception as e:
                print(f"❌ {check_name} 执行出错: {e}")
                failed_checks.append(check_name)
        
        print("\n" + "="*60)
        if failed_checks:
            print(f"❌ 部署检查完成，{len(failed_checks)} 项检查失败:")
            for check in failed_checks:
                print(f"   - {check}")
            print("\n请修复上述问题后重新运行部署检查")
            return False
        else:
            print("✅ 所有检查通过！项目已准备好部署到 GitHub")
            self.show_deployment_guide()
            return True

def main():
    """主函数"""
    deployer = DeployHelper()
    success = deployer.run_deployment_check()
    
    if success:
        print("\n🎉 部署检查完成！")
        sys.exit(0)
    else:
        print("\n💥 部署检查失败！")
        sys.exit(1)

if __name__ == "__main__":
    main()