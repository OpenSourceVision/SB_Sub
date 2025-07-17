#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
代码质量检查脚本
用于检查 convert_subscription.py 的代码质量和潜在问题
"""

import ast
import os
import re
from typing import List, Dict, Set

class CodeQualityChecker:
    """代码质量检查器"""
    
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.issues = []
        
    def check_all(self) -> List[Dict[str, str]]:
        """执行所有检查"""
        if not os.path.exists(self.file_path):
            return [{"type": "error", "message": f"文件不存在: {self.file_path}"}]
            
        with open(self.file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        try:
            tree = ast.parse(content)
        except SyntaxError as e:
            return [{"type": "error", "message": f"语法错误: {e}"}]
            
        self.check_imports(tree)
        self.check_duplicates(content)
        self.check_hardcoded_values(content)
        self.check_error_handling(tree)
        self.check_function_length(tree)
        
        return self.issues
        
    def check_imports(self, tree: ast.AST):
        """检查未使用的导入"""
        imports = set()
        used_names = set()
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.add(alias.name)
            elif isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    imports.add(alias.name)
            elif isinstance(node, ast.Name):
                used_names.add(node.id)
                
        unused = imports - used_names
        for name in unused:
            if name not in ['sys', 'os']:  # 常见的可能未直接使用的模块
                self.issues.append({
                    "type": "warning",
                    "message": f"可能未使用的导入: {name}"
                })
                
    def check_duplicates(self, content: str):
        """检查重复代码"""
        lines = content.split('\n')
        line_counts = {}
        
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if len(stripped) > 10 and not stripped.startswith('#'):
                if stripped in line_counts:
                    line_counts[stripped].append(i)
                else:
                    line_counts[stripped] = [i]
                    
        for line, occurrences in line_counts.items():
            if len(occurrences) > 1:
                self.issues.append({
                    "type": "info",
                    "message": f"重复代码行 {occurrences}: {line[:50]}..."
                })
                
    def check_hardcoded_values(self, content: str):
        """检查硬编码值"""
        # 检查硬编码的文件名
        file_patterns = [
            r'["\']\w+\.json["\']',
            r'["\']\w+\.yaml["\']',
            r'["\']\w+\.txt["\']'
        ]
        
        for pattern in file_patterns:
            matches = re.findall(pattern, content)
            for match in set(matches):
                if 'Config.' not in content.split(match)[0][-50:]:
                    self.issues.append({
                        "type": "suggestion",
                        "message": f"考虑将硬编码文件名移到Config类: {match}"
                    })
                    
    def check_error_handling(self, tree: ast.AST):
        """检查错误处理"""
        functions_without_try = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                has_try = any(isinstance(child, ast.Try) for child in ast.walk(node))
                if not has_try and node.name not in ['__init__', 'main']:
                    functions_without_try.append(node.name)
                    
        for func_name in functions_without_try:
            self.issues.append({
                "type": "suggestion",
                "message": f"函数 {func_name} 可能需要错误处理"
            })
            
    def check_function_length(self, tree: ast.AST):
        """检查函数长度"""
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                length = node.end_lineno - node.lineno if hasattr(node, 'end_lineno') else 0
                if length > 50:
                    self.issues.append({
                        "type": "suggestion",
                        "message": f"函数 {node.name} 过长 ({length} 行)，考虑拆分"
                    })

def main():
    """主函数"""
    checker = CodeQualityChecker('convert_subscription.py')
    issues = checker.check_all()
    
    if not issues:
        print("✅ 代码质量检查通过，未发现问题")
        return
        
    print(f"📋 发现 {len(issues)} 个问题:")
    print()
    
    for i, issue in enumerate(issues, 1):
        icon = {
            'error': '❌',
            'warning': '⚠️',
            'suggestion': '💡',
            'info': 'ℹ️'
        }.get(issue['type'], '•')
        
        print(f"{i:2d}. {icon} [{issue['type'].upper()}] {issue['message']}")
        
    print()
    print("💡 建议定期运行此检查以保持代码质量")

if __name__ == '__main__':
    main()