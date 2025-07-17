# Sing-Box 订阅转换工具

一个用于将各种代理订阅链接转换为 Sing-Box 配置文件的 Python 工具。

## 功能特性

- 🔄 **多协议支持**：支持 VMess、VLESS、Trojan、Shadowsocks、Hysteria、Hysteria2 等主流协议
- 📋 **多格式兼容**：支持原始订阅链接和 Clash 格式订阅
- ⚡ **自动配置**：自动生成完整的 Sing-Box 配置文件，包含路由规则、DNS 设置等
- 🎯 **智能选择**：内置节点选择器和自动测速功能
- 🛡️ **安全可靠**：包含广告拦截、分流规则等安全特性
- 🌐 **管理界面**：集成 Clash API 和 Web 管理界面

## 安装依赖

```bash
pip install -r requirements.txt
```

### 依赖包说明

- `requests>=2.28.0` - HTTP 请求库，用于获取订阅内容
- `PyYAML>=6.0` - YAML 解析库，用于处理 Clash 格式订阅
- `urllib3>=1.26.0` - URL 处理库，用于解析代理链接

## 使用方法

### 1. 配置订阅链接

在 `url.yaml` 文件中添加你的订阅链接：

```yaml
# 订阅链接列表
- https://your-subscription-url-1
- https://your-subscription-url-2
# 以 # 开头的行为注释
```

### 2. 运行转换脚本

```bash
python convert_subscription.py
```

### 3. 使用生成的配置

```bash
sing-box run -c sing-box_config.json
```

## 输出文件

- `sing-box.json` - 解析得到的代理节点列表
- `sing-box_config.json` - 完整的 Sing-Box 配置文件

## 配置特性

### 🌐 DNS 配置
- 国内外分流 DNS 解析
- 广告拦截 DNS 规则
- 支持 DoH (DNS over HTTPS)

### 📡 入站配置
- TUN 模式：透明代理，支持全局流量接管
- Mixed 模式：HTTP/SOCKS5 混合代理 (端口 2080)

### 🚀 出站配置
- 自动节点选择器
- 延迟测试和故障转移
- 直连和拦截规则

### 🛣️ 路由规则
- 国内外网站自动分流
- 广告和恶意网站拦截
- 自定义规则支持

### 🎛️ 管理界面
- Clash API 兼容接口 (端口 9090)
- Web 管理界面 (MetaCubeX)
- 节点切换和状态监控

## 支持的协议

| 协议 | 支持状态 | 说明 |
|------|----------|------|
| VMess | ✅ | 支持 TCP、WebSocket、gRPC 传输 |
| VLESS | ✅ | 支持 Reality、TLS 等安全传输 |
| Trojan | ✅ | 支持标准 Trojan 协议 |
| Shadowsocks | ✅ | 支持各种加密方式 |
| Hysteria | ✅ | 支持 Hysteria v1 协议 |
| Hysteria2 | ✅ | 支持 Hysteria v2 协议 |
| TUIC | ❌ | 暂不支持 |
| WireGuard | ❌ | 暂不支持 |

## 故障排除

### 常见问题

1. **订阅获取失败**
   - 检查网络连接
   - 确认订阅链接有效性
   - 检查防火墙设置

2. **节点解析失败**
   - 确认订阅格式正确
   - 检查是否为支持的协议类型
   - 查看错误日志信息

3. **配置文件无法使用**
   - 确认 Sing-Box 版本兼容性
   - 检查配置文件语法
   - 验证节点连通性

### 调试模式

如需查看详细的调试信息，可以修改代码中的日志级别或添加调试输出。

## 自定义配置

### 修改默认设置

在 `convert_subscription.py` 中的 `Config` 类可以修改：

- 文件路径
- 网络超时设置
- 默认端口
- 用户代理字符串

### 自定义模板

可以修改 `config.json` 作为配置模板，脚本会优先使用现有模板。

## 注意事项

- 🔒 请确保订阅链接来源可信
- 🌍 部分功能需要相应的网络环境
- 📱 移动设备使用需要 root 权限或相应权限
- ⚖️ 请遵守当地法律法规

## 许可证

本项目仅供学习和研究使用，请遵守相关法律法规。

## 贡献

欢迎提交 Issue 和 Pull Request 来改进这个项目。

---

**免责声明**：本工具仅用于技术学习和研究目的，使用者需自行承担使用风险并遵守当地法律法规。