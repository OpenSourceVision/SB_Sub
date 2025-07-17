# Sing-box 订阅转换器

一个用于将各种代理订阅链接转换为 sing-box 配置格式的 Python 工具。

## 功能特性

- 🔄 支持多种代理协议：VMess、VLESS、Trojan、Shadowsocks、Hysteria、Hysteria2
- 📋 支持 Clash 和原始订阅链接格式
- ⚙️ 自动生成符合 sing-box 1.12+ 版本的配置文件
- 🌍 智能地区分组（美国、俄罗斯等）
- 🚀 自动化工作流支持

## 项目结构

```
sing-box/
├── convert_subscription.py  # 主要转换脚本
├── config.json             # 配置模板文件
├── url.yaml                # 订阅链接配置
├── requirements.txt        # Python 依赖
├── sing-box.json          # 生成的代理列表
├── sing-box_config.json   # 生成的完整配置
└── README.md              # 项目说明
```

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置订阅链接

编辑 `url.yaml` 文件，添加你的订阅链接：

```yaml
https://your-subscription-url-1
https://your-subscription-url-2
```

### 3. 运行转换

```bash
python convert_subscription.py
```

### 4. 使用生成的配置

```bash
sing-box run -c sing-box_config.json
```

## 配置说明

### 支持的协议

- **VMess**: 支持 TCP、WebSocket、gRPC 传输
- **VLESS**: 支持 Reality、TLS 加密
- **Trojan**: 支持 TLS 加密和多种传输方式
- **Shadowsocks**: 支持各种加密方法
- **Hysteria/Hysteria2**: 支持混淆和自定义参数

### 自动分组

脚本会自动根据节点名称进行地区分组：
- 🇺🇸 美国节点
- 🇷🇺 俄罗斯节点
- 其他地区节点

### 配置文件特性

- 符合 sing-box 1.12+ 版本规范
- 使用现代化的 `rule_set` 配置
- 包含 DNS 分流和广告屏蔽
- 支持 TUN 和混合入站

## GitHub Actions 工作流

项目包含自动化工作流，支持：
- 手动触发执行
- 定时自动更新
- 自动提交生成的配置文件

## 环境要求

- Python 3.7+
- requests >= 2.28.0
- PyYAML >= 6.0

## 许可证

MIT License

## 贡献

欢迎提交 Issue 和 Pull Request！

## 注意事项

1. 请确保订阅链接的有效性
2. 生成的配置文件仅供学习和研究使用
3. 请遵守当地法律法规

## 更新日志

### v1.0.0
- 初始版本发布
- 支持多种代理协议转换
- 符合 sing-box 1.12+ 版本规范
- 移除废弃的实验性功能