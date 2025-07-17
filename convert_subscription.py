#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import base64
import urllib.parse
import requests
import yaml
import re
from typing import List, Dict, Any

class Config:
    """配置类，管理所有硬编码的参数"""
    # 文件路径
    URL_FILE = "url.yaml"
    CONFIG_TEMPLATE = "config.json"
    OUTPUT_PROXIES = "sing-box.json"
    OUTPUT_CONFIG = "sing-box_config.json"
    
    # 网络配置
    REQUEST_TIMEOUT = 10
    USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    
    # 默认端口
    DEFAULT_PORTS = {
        'vmess': 443,
        'vless': 443,
        'trojan': 443,
        'shadowsocks': 443,
        'hysteria': 443,
        'hysteria2': 443
    }

class SubscriptionConverter:
    """订阅转换器类，用于将各种代理协议转换为 sing-box 格式"""
    
    def __init__(self) -> None:
        """初始化转换器"""
        self.proxies = []
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': Config.USER_AGENT
        })
    
    def read_subscription_urls(self, file_path: str = None) -> List[str]:
        """读取订阅链接文件"""
        if file_path is None:
            file_path = Config.URL_FILE
        urls = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            lines = content.strip().split('\n')
            for line in lines:
                line = line.strip()
                if line and not line.startswith('#'):
                    urls.append(line)
            
            return urls
        except Exception as e:
            print(f"读取订阅链接文件失败: {e}")
            return []
    
    def fetch_subscription(self, url: str) -> str:
        """拉取订阅内容"""
        try:
            proxies = {'http': None, 'https': None}
            response = self.session.get(url, timeout=Config.REQUEST_TIMEOUT, proxies=proxies)
            response.raise_for_status()
            return response.text
        except Exception as e:
            print(f"拉取订阅失败: {e}")
            return ""
    
    def parse_vmess(self, vmess_str: str) -> Dict[str, Any]:
        """解析 VMess 链接"""
        try:
            # 移除 vmess:// 前缀
            vmess_data = vmess_str.replace('vmess://', '')
            # Base64 解码
            decoded = base64.b64decode(vmess_data + '==').decode('utf-8')
            config = json.loads(decoded)
            
            # 验证必需字段
            required_fields = ['add', 'port', 'id']
            for field in required_fields:
                if not config.get(field):
                    raise ValueError(f"缺少必需字段: {field}")
            
            # 获取节点名称，保持原有名称
            node_name = config.get('ps', 'unknown')
            
            outbound = {
                "type": "vmess",
                "tag": node_name,
                "server": config.get('add', ''),
                "server_port": int(config.get('port', Config.DEFAULT_PORTS['vmess'])),
                "uuid": config.get('id', ''),
                "security": config.get('scy', 'auto'),
                "alter_id": int(config.get('aid', 0))
            }
            
            # TLS 配置
            if config.get('tls') == 'tls':
                outbound["tls"] = {
                    "enabled": True,
                    "server_name": config.get('sni', config.get('add', '')),
                    "insecure": False
                }
            
            # 传输协议配置
            net = config.get('net', 'tcp')
            if net == 'ws':
                outbound["transport"] = {
                    "type": "ws",
                    "path": config.get('path', '/'),
                    "headers": {
                        "Host": config.get('host', config.get('add', ''))
                    }
                }
            elif net == 'grpc':
                outbound["transport"] = {
                    "type": "grpc",
                    "service_name": config.get('path', '')
                }
            
            return outbound
        except Exception as e:
            print(f"解析 VMess 失败: {e}")
            return None
    
    def parse_vless(self, vless_str: str) -> Dict[str, Any]:
        """解析 VLESS 链接"""
        try:
            # 移除 vless:// 前缀
            url_part = vless_str.replace('vless://', '')
            
            # 分离 UUID 和其他部分
            if '@' not in url_part:
                return None
            
            uuid_part, rest = url_part.split('@', 1)
            
            # 分离服务器地址和参数
            if '?' in rest:
                server_part, params_part = rest.split('?', 1)
            else:
                server_part = rest
                params_part = ''
            
            # 解析服务器地址和端口
            if ':' in server_part:
                server, port = server_part.rsplit(':', 1)
                server = server.strip('[]')  # 移除 IPv6 地址的方括号
            else:
                return None
            
            # 解析参数
            params = urllib.parse.parse_qs(params_part)
            
            # 获取节点名称，优先从 fragment 获取，然后从 remarks 参数获取
            node_name = "unknown"
            if '#' in vless_str:
                fragment = vless_str.split('#')[1]
                node_name = urllib.parse.unquote(fragment)
            elif 'remarks' in params:
                node_name = params.get('remarks', ['unknown'])[0]
            
            outbound = {
                "type": "vless",
                "tag": node_name,
                "server": server,
                "server_port": int(port),
                "uuid": uuid_part,
                "flow": params.get('flow', [''])[0]
            }
            
            # TLS 配置
            security = params.get('security', [''])[0]
            if security == 'tls':
                outbound["tls"] = {
                    "enabled": True,
                    "server_name": params.get('sni', [server])[0],
                    "insecure": False
                }
            elif security == 'reality':
                outbound["tls"] = {
                    "enabled": True,
                    "server_name": params.get('sni', [server])[0],
                    "reality": {
                        "enabled": True,
                        "public_key": params.get('pbk', [''])[0],
                        "short_id": params.get('sid', [''])[0]
                    }
                }
            
            # 传输协议配置
            transport_type = params.get('type', ['tcp'])[0]
            if transport_type == 'ws':
                outbound["transport"] = {
                    "type": "ws",
                    "path": params.get('path', ['/'])[0],
                    "headers": {
                        "Host": params.get('host', [server])[0]
                    }
                }
            elif transport_type == 'grpc':
                outbound["transport"] = {
                    "type": "grpc",
                    "service_name": params.get('serviceName', [''])[0]
                }
            
            return outbound
        except Exception as e:
            print(f"解析 VLESS 失败: {e}")
            return None
    
    def parse_trojan(self, trojan_str: str) -> Dict[str, Any]:
        """解析 Trojan 链接"""
        try:
            # 移除 trojan:// 前缀
            url_part = trojan_str.replace('trojan://', '')
            
            # 分离密码和其他部分
            if '@' not in url_part:
                return None
            
            password, rest = url_part.split('@', 1)
            
            # 分离服务器地址和参数
            if '?' in rest:
                server_part, params_part = rest.split('?', 1)
            else:
                server_part = rest
                params_part = ''
            
            # 解析服务器地址和端口
            if ':' in server_part:
                server, port = server_part.rsplit(':', 1)
                server = server.strip('[]')
            else:
                return None
            
            # 解析参数
            params = urllib.parse.parse_qs(params_part)
            
            # 获取节点名称，优先从 fragment 获取，然后从 remarks 参数获取
            node_name = "unknown"
            if '#' in trojan_str:
                fragment = trojan_str.split('#')[1]
                node_name = urllib.parse.unquote(fragment)
            elif 'remarks' in params:
                node_name = params.get('remarks', ['unknown'])[0]
            
            outbound = {
                "type": "trojan",
                "tag": node_name,
                "server": server,
                "server_port": int(port),
                "password": urllib.parse.unquote(password)
            }
            
            # TLS 配置
            security = params.get('security', ['tls'])[0]
            if security == 'tls':
                outbound["tls"] = {
                    "enabled": True,
                    "server_name": params.get('sni', [server])[0],
                    "insecure": False
                }
            
            # 传输协议配置
            transport_type = params.get('type', ['tcp'])[0]
            if transport_type == 'ws':
                outbound["transport"] = {
                    "type": "ws",
                    "path": params.get('path', ['/'])[0],
                    "headers": {
                        "Host": params.get('host', [server])[0]
                    }
                }
            
            return outbound
        except Exception as e:
            print(f"解析 Trojan 失败: {e}")
            return None
    
    def parse_shadowsocks(self, ss_str: str) -> Dict[str, Any]:
        """解析 Shadowsocks 链接"""
        try:
            # 移除 ss:// 前缀
            url_part = ss_str.replace('ss://', '')
            
            # 处理两种格式
            if '@' in url_part:
                # 格式: method:password@server:port#name
                auth_part, rest = url_part.split('@', 1)
                if ':' in auth_part:
                    method, password = auth_part.split(':', 1)
                else:
                    # Base64 编码的认证信息
                    decoded_auth = base64.b64decode(auth_part + '==').decode('utf-8')
                    method, password = decoded_auth.split(':', 1)
            else:
                # 全部 Base64 编码
                decoded = base64.b64decode(url_part + '==').decode('utf-8')
                if '@' in decoded:
                    auth_part, rest = decoded.split('@', 1)
                    method, password = auth_part.split(':', 1)
                else:
                    return None
            
            # 解析服务器地址和端口
            if '#' in rest:
                server_part, name = rest.split('#', 1)
                name = urllib.parse.unquote(name)
            else:
                server_part = rest
                name = 'unknown'
            
            if ':' in server_part:
                server, port = server_part.rsplit(':', 1)
                server = server.strip('[]')
            else:
                return None
            
            outbound = {
                "type": "shadowsocks",
                "tag": name,
                "server": server,
                "server_port": int(port),
                "method": method,
                "password": password
            }
            
            return outbound
        except Exception as e:
            print(f"解析 Shadowsocks 失败: {e}")
            return None
    
    def parse_hysteria(self, hysteria_str: str) -> Dict[str, Any]:
        """解析 Hysteria 链接"""
        try:
            # 移除 hysteria:// 前缀
            url_part = hysteria_str.replace('hysteria://', '')
            
            # 分离服务器地址和参数
            if '?' in url_part:
                server_part, params_part = url_part.split('?', 1)
            else:
                server_part = url_part
                params_part = ''
            
            # 解析服务器地址和端口
            if ':' in server_part:
                server, port = server_part.rsplit(':', 1)
                server = server.strip('[]')
            else:
                return None
            
            # 解析参数
            params = urllib.parse.parse_qs(params_part)
            
            # 获取认证信息
            auth_str = params.get('auth', [''])[0]
            if not auth_str:
                return None
            
            # 解析节点名称（从 fragment 中获取）
            node_name = "unknown"
            if '#' in hysteria_str:
                fragment = hysteria_str.split('#')[1]
                node_name = urllib.parse.unquote(fragment)
            
            outbound = {
                "type": "hysteria",
                "tag": node_name,
                "server": server,
                "server_port": int(port),
                "up_mbps": int(params.get('upmbps', ['100'])[0]),
                "down_mbps": int(params.get('downmbps', ['100'])[0]),
                "auth_str": auth_str
            }
            
            # 混淆配置
            if 'obfs' in params and params.get('obfs', [''])[0]:
                outbound["obfs"] = params.get('obfs', [''])[0]
            
            # TLS 配置
            outbound["tls"] = {
                "enabled": True,
                "server_name": params.get('peer', [server])[0],
                "insecure": params.get('insecure', ['0'])[0] == '1'
            }
            
            return outbound
        except Exception as e:
            print(f"解析 Hysteria 失败: {e}")
            return None
    
    def parse_hysteria2(self, hysteria2_str: str) -> Dict[str, Any]:
        """解析 Hysteria2 链接"""
        try:
            # 移除 hysteria2:// 或 hy2:// 前缀
            url_part = hysteria2_str.replace('hysteria2://', '').replace('hy2://', '')
            
            # 分离认证信息和其他部分
            if '@' not in url_part:
                return None
            
            auth_part, rest = url_part.split('@', 1)
            
            # 分离服务器地址和参数
            if '?' in rest:
                server_part, params_part = rest.split('?', 1)
            else:
                server_part = rest
                params_part = ''
            
            # 解析服务器地址和端口
            if ':' in server_part:
                server, port = server_part.rsplit(':', 1)
                server = server.strip('[]')
            else:
                return None
            
            # 解析参数
            params = urllib.parse.parse_qs(params_part)
            
            # 获取节点名称，优先从 fragment 获取
            node_name = "unknown"
            if '#' in hysteria2_str:
                fragment = hysteria2_str.split('#')[1]
                node_name = urllib.parse.unquote(fragment)
            
            outbound = {
                "type": "hysteria2",
                "tag": node_name,
                "server": server,
                "server_port": int(port),
                "up_mbps": int(params.get('up', ['100'])[0]),
                "down_mbps": int(params.get('down', ['100'])[0]),
                "password": auth_part
            }
            
            # 混淆配置
            if 'obfs' in params:
                obfs_password = params.get('obfs-password', [''])[0]
                if obfs_password:
                    outbound["obfs"] = {
                        "type": "salamander",
                        "password": obfs_password
                    }
            
            # TLS 配置
            outbound["tls"] = {
                "enabled": True,
                "server_name": params.get('sni', [server])[0],
                "insecure": params.get('insecure', ['0'])[0] == '1'
            }
            
            return outbound
        except Exception as e:
            print(f"解析 Hysteria2 失败: {e}")
            return None
    
    def parse_subscription_content(self, content: str) -> List[Dict[str, Any]]:
        """解析订阅内容"""
        proxies = []
        unsupported_protocols = set()
        
        # 尝试解析为 YAML 格式 (Clash)
        try:
            yaml_data = yaml.safe_load(content)
            if isinstance(yaml_data, dict) and 'proxies' in yaml_data:
                for proxy in yaml_data['proxies']:
                    converted = self.convert_clash_proxy(proxy)
                    if converted:
                        proxies.append(converted)
                    else:
                        proxy_type = proxy.get('type', 'unknown')
                        unsupported_protocols.add(proxy_type)
                return proxies
        except Exception:
            pass
        
        # 尝试 Base64 解码
        try:
            decoded_content = base64.b64decode(content + '==').decode('utf-8')
            content = decoded_content
        except Exception:
            pass
        
        # 按行解析代理链接
        lines = content.strip().split('\n')
        
        for i, line in enumerate(lines, 1):
            line = line.strip()
            if not line:
                continue
            
            proxy = None
            protocol = 'unknown'
            
            if line.startswith('vmess://'):
                protocol = 'vmess'
                proxy = self.parse_vmess(line)
            elif line.startswith('vless://'):
                protocol = 'vless'
                proxy = self.parse_vless(line)
            elif line.startswith('trojan://'):
                protocol = 'trojan'
                proxy = self.parse_trojan(line)
            elif line.startswith('ss://'):
                protocol = 'shadowsocks'
                proxy = self.parse_shadowsocks(line)
            elif line.startswith('hysteria://'):
                protocol = 'hysteria'
                proxy = self.parse_hysteria(line)
            elif line.startswith('hysteria2://') or line.startswith('hy2://'):
                protocol = 'hysteria2'
                proxy = self.parse_hysteria2(line)
            elif line.startswith('tuic://'):
                protocol = 'tuic'
                unsupported_protocols.add(protocol)
                continue
            elif line.startswith('wireguard://'):
                protocol = 'wireguard'
                unsupported_protocols.add(protocol)
                continue
            elif '://' in line:
                protocol = line.split('://')[0]
                unsupported_protocols.add(protocol)
                continue
            else:
                continue
            
            if proxy:
                proxies.append(proxy)
        
        return proxies
    
    def convert_clash_proxy(self, proxy: Dict[str, Any]) -> Dict[str, Any]:
        """转换 Clash 代理配置为 sing-box 格式"""
        try:
            proxy_type = proxy.get('type', '').lower()
            proxy_name = proxy.get('name', 'unknown')
            
            if proxy_type == 'vmess':
                outbound = {
                    "type": "vmess",
                    "tag": proxy_name,
                    "server": proxy.get('server', ''),
                    "server_port": int(proxy.get('port', 443)),
                    "uuid": proxy.get('uuid', ''),
                    "security": proxy.get('cipher', 'auto'),
                    "alter_id": int(proxy.get('alterId', 0))
                }
                
                # TLS 配置
                if proxy.get('tls'):
                    outbound["tls"] = {
                        "enabled": True,
                        "server_name": proxy.get('servername', proxy.get('server', '')),
                        "insecure": proxy.get('skip-cert-verify', False)
                    }
                
                # 传输协议配置
                network = proxy.get('network', 'tcp')
                if network == 'ws':
                    ws_opts = proxy.get('ws-opts', {})
                    outbound["transport"] = {
                        "type": "ws",
                        "path": ws_opts.get('path', '/'),
                        "headers": ws_opts.get('headers', {})
                    }
                elif network == 'grpc':
                    grpc_opts = proxy.get('grpc-opts', {})
                    outbound["transport"] = {
                        "type": "grpc",
                        "service_name": grpc_opts.get('grpc-service-name', '')
                    }
                
                return outbound
            
            elif proxy_type == 'vless':
                outbound = {
                    "type": "vless",
                    "tag": proxy_name,
                    "server": proxy.get('server', ''),
                    "server_port": int(proxy.get('port', 443)),
                    "uuid": proxy.get('uuid', ''),
                    "flow": proxy.get('flow', '')
                }
                
                # TLS 配置
                if proxy.get('tls'):
                    outbound["tls"] = {
                        "enabled": True,
                        "server_name": proxy.get('servername', proxy.get('server', '')),
                        "insecure": proxy.get('skip-cert-verify', False)
                    }
                    
                    # Reality 配置
                    if proxy.get('reality-opts'):
                        reality_opts = proxy.get('reality-opts', {})
                        outbound["tls"]["reality"] = {
                            "enabled": True,
                            "public_key": reality_opts.get('public-key', ''),
                            "short_id": reality_opts.get('short-id', '')
                        }
                
                # 传输协议配置
                network = proxy.get('network', 'tcp')
                if network == 'ws':
                    ws_opts = proxy.get('ws-opts', {})
                    outbound["transport"] = {
                        "type": "ws",
                        "path": ws_opts.get('path', '/'),
                        "headers": ws_opts.get('headers', {})
                    }
                elif network == 'grpc':
                    grpc_opts = proxy.get('grpc-opts', {})
                    outbound["transport"] = {
                        "type": "grpc",
                        "service_name": grpc_opts.get('grpc-service-name', '')
                    }
                
                return outbound
            
            elif proxy_type == 'trojan':
                outbound = {
                    "type": "trojan",
                    "tag": proxy_name,
                    "server": proxy.get('server', ''),
                    "server_port": int(proxy.get('port', 443)),
                    "password": proxy.get('password', '')
                }
                
                # TLS 配置
                outbound["tls"] = {
                    "enabled": True,
                    "server_name": proxy.get('sni', proxy.get('server', '')),
                    "insecure": proxy.get('skip-cert-verify', False)
                }
                
                # 传输协议配置
                network = proxy.get('network', 'tcp')
                if network == 'ws':
                    ws_opts = proxy.get('ws-opts', {})
                    outbound["transport"] = {
                        "type": "ws",
                        "path": ws_opts.get('path', '/'),
                        "headers": ws_opts.get('headers', {})
                    }
                
                return outbound
            
            elif proxy_type == 'ss':
                outbound = {
                    "type": "shadowsocks",
                    "tag": proxy_name,
                    "server": proxy.get('server', ''),
                    "server_port": int(proxy.get('port', 8388)),
                    "method": proxy.get('cipher', 'aes-256-gcm'),
                    "password": proxy.get('password', '')
                }
                
                # 插件支持
                if proxy.get('plugin'):
                    plugin = proxy.get('plugin')
                    plugin_opts = proxy.get('plugin-opts', {})
                    if plugin == 'obfs':
                        outbound["plugin"] = "obfs-local"
                        outbound["plugin_opts"] = {
                            "mode": plugin_opts.get('mode', 'http'),
                            "host": plugin_opts.get('host', '')
                        }
                
                return outbound
            
            elif proxy_type == 'hysteria':
                outbound = {
                    "type": "hysteria",
                    "tag": proxy_name,
                    "server": proxy.get('server', ''),
                    "server_port": int(proxy.get('port', 443)),
                    "up_mbps": proxy.get('up', 100),
                    "down_mbps": proxy.get('down', 100),
                    "auth_str": proxy.get('auth_str', proxy.get('password', ''))
                }
                
                # 混淆配置
                if proxy.get('obfs'):
                    outbound["obfs"] = proxy.get('obfs')
                
                # TLS 配置
                outbound["tls"] = {
                    "enabled": True,
                    "server_name": proxy.get('sni', proxy.get('server', '')),
                    "insecure": proxy.get('skip-cert-verify', False)
                }
                
                # 网络类型
                if proxy.get('protocol'):
                    outbound["network"] = proxy.get('protocol')
                
                return outbound
            
            elif proxy_type == 'hysteria2':
                outbound = {
                    "type": "hysteria2",
                    "tag": proxy_name,
                    "server": proxy.get('server', ''),
                    "server_port": int(proxy.get('port', 443)),
                    "up_mbps": proxy.get('up', 100),
                    "down_mbps": proxy.get('down', 100),
                    "password": proxy.get('password', '')
                }
                
                # 混淆配置
                if proxy.get('obfs'):
                    obfs_config = proxy.get('obfs')
                    if isinstance(obfs_config, str):
                        outbound["obfs"] = {
                            "type": "salamander",
                            "password": obfs_config
                        }
                    elif isinstance(obfs_config, dict):
                        outbound["obfs"] = obfs_config
                
                # TLS 配置
                outbound["tls"] = {
                    "enabled": True,
                    "server_name": proxy.get('sni', proxy.get('server', '')),
                    "insecure": proxy.get('skip-cert-verify', False)
                }
                
                return outbound
            
            else:
                return None
            
        except Exception:
            pass
        
        return None
    
    def process_subscriptions(self, urls: List[str]) -> List[Dict[str, Any]]:
        """处理所有订阅链接
        
        Args:
            urls: 订阅链接列表
            
        Returns:
            解析得到的所有代理节点列表
        """
        all_proxies = []
        
        for url in urls:
            try:
                content = self.fetch_subscription(url)
                if content:
                    proxies = self.parse_subscription_content(content)
                    all_proxies.extend(proxies)
            except Exception as e:
                print(f"处理订阅时发生错误: {e}")
                continue
        
        return all_proxies
    
    def save_proxies_json(self, proxies: List[Dict[str, Any]], filename: str = None):
        """保存代理列表为 JSON 文件"""
        if filename is None:
            filename = Config.OUTPUT_PROXIES
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(proxies, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"保存代理列表失败: {e}")
    
    def generate_config(self, proxies: List[Dict[str, Any]]) -> Dict[str, Any]:
        """生成完整的 sing-box 配置文件，基于现有模板"""
        # 读取现有的配置文件作为模板
        try:
            with open(Config.CONFIG_TEMPLATE, 'r', encoding='utf-8') as f:
                config = json.load(f)
        except Exception:
            # 如果读取失败，使用默认配置
            # 如果读取失败，使用默认配置
            config = {
                "log": {
                    "level": "info",
                    "timestamp": True
                },
                "dns": {
                    "servers": [
                        {
                            "tag": "dns_proxy",
                            "address": "https://1.1.1.1/dns-query",
                            "address_resolver": "dns_resolver",
                            "strategy": "ipv4_only",
                            "detour": "默认"
                        },
                        {
                            "tag": "dns_direct",
                            "address": "https://223.5.5.5/dns-query",
                            "address_resolver": "dns_resolver",
                            "strategy": "ipv4_only",
                            "detour": "direct"
                        },
                        {
                            "tag": "dns_resolver",
                            "address": "223.5.5.5",
                            "strategy": "ipv4_only",
                            "detour": "direct"
                        },
                        {
                            "tag": "dns_block",
                            "address": "rcode://success"
                        }
                    ],
                    "rules": [
                        {
                            "geosite": ["category-ads-all"],
                            "server": "dns_block",
                            "disable_cache": True
                        },
                        {
                            "geosite": ["cn"],
                            "server": "dns_direct"
                        },
                        {
                            "geosite": ["geolocation-!cn"],
                            "server": "dns_proxy"
                        }
                    ],
                    "final": "dns_proxy",
                    "strategy": "ipv4_only",
                    "disable_cache": False,
                    "disable_expire": False
                },
                "inbounds": [
                    {
                        "type": "tun",
                        "tag": "tun-in",
                        "interface_name": "tun0",
                        "address": [
                            "172.19.0.1/30",
                            "fdfe:dcba:9876::1/126"
                        ],
                        "mtu": 9000,
                        "auto_route": True,
                        "strict_route": True,
                        "stack": "system",
                        "sniff": True,
                        "sniff_override_destination": True
                    },
                    {
                        "type": "mixed",
                        "tag": "mixed-in",
                        "listen": "127.0.0.1",
                        "listen_port": 2080,
                        "sniff": True,
                        "sniff_override_destination": True
                    }
                ],
                "outbounds": [],
                "route": {
                    "geoip": {
                        "path": "geoip.db",
                        "download_url": "https://raw.githubusercontent.com/SagerNet/sing-geoip/rule-set/geoip.db",
                        "download_detour": "默认"
                    },
                    "geosite": {
                        "path": "geosite.db",
                        "download_url": "https://raw.githubusercontent.com/SagerNet/sing-geosite/rule-set/geosite.db",
                        "download_detour": "默认"
                    },
                    "rules": [
                        {
                            "protocol": "dns",
                            "outbound": "dns-out"
                        },
                        {
                            "geosite": ["category-ads-all"],
                            "outbound": "block"
                        },
                        {
                            "geosite": ["cn"],
                            "geoip": ["cn"],
                            "outbound": "direct"
                        },
                        {
                            "geosite": ["geolocation-!cn"],
                            "outbound": "默认"
                        },
                        {
                            "geoip": ["cn"],
                            "outbound": "direct"
                        }
                    ],
                    "final": "默认",
                    "auto_detect_interface": True
                },
                "experimental": {
                    "clash_api": {
                        "external_controller": "127.0.0.1:9090",
                        "external_ui": "metacubexd",
                        "external_ui_download_url": "https://github.com/MetaCubeX/metacubexd/archive/refs/heads/gh-pages.zip",
                        "external_ui_download_detour": "默认",
                        "secret": "",
                        "default_mode": "rule",
                        "store_selected": True,
                        "cache_file": "cache.db"
                    }
                }
            }
        
        # 提取代理标签并按地区分组
        proxy_tags = [proxy['tag'] for proxy in proxies]
        us_proxies = [tag for tag in proxy_tags if any(keyword in tag.lower() for keyword in ['🇺🇸', 'us ', 'usa', 'america', 'united states', '美国'])]
        ru_proxies = [tag for tag in proxy_tags if any(keyword in tag.lower() for keyword in ['🇷🇺', 'ru ', 'russia', 'moscow', '俄罗斯'])]
        
        # 清理现有的outbounds，保留系统outbounds
        system_outbounds = []
        for outbound in config.get('outbounds', []):
            outbound_type = outbound.get('type', '')
            if outbound_type in ['direct', 'block', 'dns']:
                system_outbounds.append(outbound)
        
        # 重新构建outbounds列表
        new_outbounds = []
        
        # 查找并更新现有的分组配置
        for outbound in config.get('outbounds', []):
            if outbound.get('tag') == '手动':
                outbound['outbounds'] = proxy_tags
                new_outbounds.append(outbound)
            elif outbound.get('tag') == '自动':
                outbound['outbounds'] = proxy_tags
                new_outbounds.append(outbound)
            elif outbound.get('tag') == 'US':
                outbound['outbounds'] = us_proxies if us_proxies else proxy_tags
                new_outbounds.append(outbound)
            elif outbound.get('tag') == 'RU':
                outbound['outbounds'] = ru_proxies if ru_proxies else proxy_tags
                new_outbounds.append(outbound)
            elif outbound.get('type') in ['selector'] and outbound.get('tag') in ['默认', 'AI', 'YouTube']:
                new_outbounds.append(outbound)
        
        # 添加所有代理节点
        new_outbounds.extend(proxies)
        
        # 添加系统outbounds
        new_outbounds.extend(system_outbounds)
        
        # 更新配置
        config['outbounds'] = new_outbounds
        
        return config
    
    def save_config(self, config: Dict[str, Any], filename: str = None):
        """保存配置文件"""
        if filename is None:
            filename = Config.OUTPUT_CONFIG
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"保存配置文件失败: {e}")

def main():
    """主函数"""
    converter = SubscriptionConverter()
    
    try:
        # 读取订阅链接
        urls = converter.read_subscription_urls()
        if not urls:
            print("❌ 没有找到有效的订阅链接")
            return
        
        # 处理订阅并解析节点
        proxies = converter.process_subscriptions(urls)
        if not proxies:
            print("❌ 没有解析到任何节点")
            return
        
        # 保存节点列表和配置文件
        converter.save_proxies_json(proxies)
        config = converter.generate_config(proxies)
        converter.save_config(config)
        
        # 输出结果
        print(f"✅ 转换完成！")
        print(f"📥 从 {len(urls)} 个订阅链接获取节点")
        print(f"🔄 总共解析到 {len(proxies)} 个代理节点")
        print(f"📋 代理列表已保存到: {Config.OUTPUT_PROXIES}")
        print(f"⚙️  配置文件已生成: {Config.OUTPUT_CONFIG}")
        print(f"\n🎉 配置文件已准备就绪，可以直接使用！")
        print(f"\n🚀 使用方法:")
        print(f"   sing-box run -c {Config.OUTPUT_CONFIG}")
        
    except KeyboardInterrupt:
        print("\n❌ 用户中断操作")
    except Exception as e:
        print(f"\n❌ 程序执行出错: {e}")

if __name__ == '__main__':
    main()