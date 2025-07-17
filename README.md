# Sing-Box 1.12 配置文件说明

这是一个适用于 sing-box 1.12 版本的完整配置文件示例。

## 配置文件结构

### 主要组件
- **log**: 日志配置
- **dns**: DNS 服务器配置
- **inbounds**: 入站连接配置
- **outbounds**: 出站连接配置
- **route**: 路由规则配置
- **experimental**: 实验性功能配置

### 入站配置
1. **TUN 接口** (tun-in): 用于透明代理
   - 监听地址: 172.19.0.1/30
   - 自动路由: 启用
   - 流量嗅探: 启用

2. **混合代理** (mixed-in): HTTP/SOCKS5 代理
   - 监听地址: 127.0.0.1:2080

### 出站配置
包含多种代理协议支持:
- **Shadowsocks**: 高性能代理协议
- **VMess**: V2Ray 协议
- **Trojan**: 基于 TLS 的代理协议
- **选择器**: 手动选择代理节点
- **自动测速**: 自动选择最快节点

### DNS 配置
- 国内域名使用阿里 DNS (223.5.5.5)
- 国外域名使用 Cloudflare DNS (1.1.1.1)
- 广告域名直接阻断

### 路由规则
- 广告域名 → 阻断
- 中国大陆域名/IP → 直连
- 国外域名/IP → 代理

## 使用前配置

### 1. 修改代理服务器信息
请根据你的实际代理服务器信息修改以下字段:

**Shadowsocks 配置:**
```json
"server": "your-server.com",        // 替换为你的服务器地址
"server_port": 8388,               // 替换为你的服务器端口
"password": "your-password"         // 替换为你的密码
```

**VMess 配置:**
```json
"server": "your-server.com",        // 替换为你的服务器地址
"server_port": 443,                // 替换为你的服务器端口
"uuid": "your-uuid",               // 替换为你的 UUID
"tls": {
  "server_name": "your-server.com"  // 替换为你的域名
},
"transport": {
  "path": "/path",                 // 替换为你的路径
  "headers": {
    "Host": "your-server.com"       // 替换为你的域名
  }
}
```

**Trojan 配置:**
```json
"server": "your-server.com",        // 替换为你的服务器地址
"server_port": 443,                // 替换为你的服务器端口
"password": "your-password",        // 替换为你的密码
"tls": {
  "server_name": "your-server.com"  // 替换为你的域名
}
```

### 2. 启动 Sing-Box
```bash
# 检查配置文件
sing-box check -c config.json

# 启动服务
sing-box run -c config.json
```

### 3. 使用代理
- **系统代理**: 设置 HTTP/SOCKS5 代理为 127.0.0.1:2080
- **TUN 模式**: 需要管理员权限，启动后自动接管系统流量
- **Clash API**: 访问 http://127.0.0.1:9090 使用 Web 管理界面

## 注意事项

1. **权限要求**: TUN 模式需要管理员/root 权限
2. **防火墙**: 确保防火墙允许相关端口通信
3. **证书验证**: 生产环境建议启用 TLS 证书验证
4. **定期更新**: 建议定期更新 geoip.db 和 geosite.db 文件

## 常用命令

```bash
# 检查配置文件语法
sing-box check -c config.json

# 格式化配置文件
sing-box format -w -c config.json

# 生成密钥对
sing-box generate reality-keypair
sing-box generate ech-keypair

# 编译规则集
sing-box rule-set compile --output rules.srs rules.json
```

## 故障排除

1. **连接失败**: 检查服务器地址、端口、密码是否正确
2. **DNS 解析问题**: 检查 DNS 服务器配置
3. **路由问题**: 检查路由规则和 geoip/geosite 数据库
4. **权限问题**: 确保以管理员权限运行

更多详细配置请参考官方文档: https://sing-box.sagernet.org/