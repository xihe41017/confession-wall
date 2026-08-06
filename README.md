<div align="center">

# 💌 平和一中校园墙

**把想说的话，写在这里** · 校园表白墙 / 树洞 / 心愿墙

![Vue 3](https://img.shields.io/badge/Vue%203-4FC08D?style=for-the-badge&logo=vuedotjs&logoColor=white)
![Vite](https://img.shields.io/badge/Vite-646CFF?style=for-the-badge&logo=vite&logoColor=white)
![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-003B57?style=for-the-badge&logo=sqlite&logoColor=white)
![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)

一个浪漫风格的校园墙网站：表白、心愿、吐槽、树洞都欢迎。前后端分离，开箱即用。

</div>

---

## ✨ 功能亮点

### 📱 内容
| 功能 | 说明 |
| --- | --- |
| 🏠 QQ空间式时间线 | 单列信息流，评论**内联展开**，不再跳页 |
| 📌 置顶 | 管理员可将内容置顶，置顶永远排最前 |
| 🏅 头衔体系 | 管理员/超管专属头衔 + 超管下发的自定义头衔 |
| 🖼️ 图片 / 🎬 短视频 | 最多 9 张图（匿名限 1 张），≤15 秒视频，**浏览器端自动压缩上传** |
| ❤️ 点赞 / 💬 评论 | 每个 IP 限赞一次防刷，评论可点赞 |
| 🚀 启动页 + 无限滚动 | 校徽启动页丝滑过渡，数据划到底自动加载 |

### 👥 账号与权限
- 匿名发布（限 1 张图）/ 登录后 9 图 + 视频，记录 IP 与设备
- 三级角色：**普通用户 / 管理员 / 超级管理员**
- 权限精细到**每个功能、每个设置项**，超管可单独授予/收回
- 注册审核开关、一键拉黑账号 / IP

### 🛡️ 安全防护（面向公网）
- slowapi 速率限制（搜索/点歌/登录等，超管可调）
- 请求体大小限制（默认 50MB）、IP 黑名单
- 匿名单 IP/设备限发，防刷墙

## 🧱 技术栈

| 层 | 技术 |
| --- | --- |
| 前端 | Vue 3 · Vite · Vue Router |
| 后端 | Python · FastAPI · SQLAlchemy |
| 数据库 | SQLite（WAL 模式，零配置） |
| 安全 | JWT · slowapi · PBKDF2 密码哈希 |

## ⚡ 服务器一键部署（Linux）

> 只需一条命令，在 Linux 服务器上（需 root）完成部署。支持 Ubuntu / Debian / CentOS。

```bash
# 国内服务器（jsdelivr CDN 加速，推荐）
bash -c "$(curl -sSL https://cdn.jsdelivr.net/gh/xihe41017/confession-wall@main/deploy/install.sh)"

# 海外服务器
bash -c "$(curl -sSL https://raw.githubusercontent.com/xihe41017/confession-wall/main/deploy/install.sh)"
```

### 🎛️ 部署过程（交互式）

运行后会依次询问，也可用环境变量跳过：

```
请输入表白墙要使用的端口 [默认 8000]:   ← 选端口
请设置表白墙管理员密码（≥6位，直接回车自动生成）: *****   ← 静默输入
请再次输入确认: *****
是否配置 Nginx：80 端口反向代理到 8000？（y/N）:   ← 可选
```

| 设置项 | 说明 |
| --- | --- |
| 端口 | 任意 1~65535，自动检测占用（默认 8000） |
| 管理员密码 | 静默输入 + 二次确认，留空自动生成强随机密码 |
| JWT 密钥 | 自动生成（可用 `JWT_SECRET` 指定） |
| Nginx | 可选，80 端口反代到你选的端口 |

**非交互部署**（设置环境变量即可跳过所有询问）：

```bash
PORT=8080 ADMIN_PASSWORD='强密码' JWT_SECRET='随机串' DOMAIN='你的域名' bash -c "$(curl -sSL https://cdn.jsdelivr.net/gh/xihe41017/confession-wall@main/deploy/install.sh)"
```

### 📦 脚本自动完成

```
安装依赖(Python/Node/ffmpeg) → 拉取代码 → 后端venv → 前端构建
→ 写入管理员密码/JWT密钥 → 注册systemd服务(开机自启+崩溃重启)
→ 可选Nginx反代 → 输出访问地址和密码
```

### 🔄 自动更新管理（后台可配置）

部署后自带自动更新能力，**超管登录后台 → 系统设置 → 自动更新** 即可管理：

- **开关**：启用后按设定间隔自动检查更新
- **间隔**：每分钟 ~ 每天，自定义
- **手动更新**：一键立即更新
- **安全**：更新失败不影响当前运行；构建到临时目录、失败自动回滚

部署完成后访问 `http://服务器IP:端口/`，管理员密码在脚本输出末尾，请立即保存。

> 📻 **点歌系统**是独立项目，用它的独立脚本部署：[radio-song](https://github.com/xihe41017/radio-song) → `deploy/install.sh`（默认端口 8001，同样支持一键部署 + 自动更新）

## 🚀 本地快速开始

需要 Python 3.10+ 和 Node.js 18+。

```bash
# 1. 启动后端
cd backend
python -m venv .venv
.venv/Scripts/pip install -r requirements.txt
.venv/Scripts/python run.py          # http://localhost:8000

# 2. 启动前端（开发模式）
cd frontend
npm install
npm run dev                          # http://localhost:5173
```

> 默认超级管理员：`admin / admin123`，首次启动自动创建，**上线前务必修改**！

### 生产运行（单进程）

```bash
cd frontend && npm run build
cd ../backend && .venv/Scripts/python run.py   # http://localhost:8000
```

后端检测到 `frontend/dist/` 后自动托管前端，一个进程即可运行。

## 📖 详细文档

- [部署到服务器（Nginx + 防 DoS）](#部署到服务器)
- [服务器设置项说明](#服务器设置项后台可改)
- [权限体系](#权限体系)

### 部署到服务器

```bash
# 服务器上
cd confession-wall/backend
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
ADMIN_PASSWORD='强密码' JWT_SECRET='随机长字符串' nohup .venv/bin/python run.py > server.log 2>&1 &

# Nginx 反代（必须设置 X-Forwarded-For，否则 IP 防刷失效）
server {
    listen 80;
    server_name 你的域名;
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        client_max_body_size 60m;   # 允许大视频上传
    }
}
```

### 服务器设置项（后台可改）

| key | 默认 | 说明 | 权限 |
| --- | --- | --- | --- |
| `site_name` | 平和一中校园墙 | 站点名称 | 🔒 仅超管 |
| `site_announcement` | 空 | 首页公告 | 按权限 |
| `moderation_mode` | 0 | 发布需审核 | 按权限 |
| `allow_register` / `register_approval` | 1 / 0 | 开放注册 / 注册需激活 | 按权限 |
| `anonymous_post_limit` | 3 | 匿名单 IP/设备限发条数 | 按权限 |
| `rate_*` | 20~60 | 各接口限速（次/分钟） | 🔒 仅超管 |
| `max_body_kb` | 51200 | 请求体上限(KB)=50MB | 🔒 仅超管 |
| `image_max_mb` / `video_max_mb` | 2 / 15 | 图片压缩后 / 视频上传上限 | 🔒 仅超管 |
| `jwt_secret` | — | JWT 密钥（改后全员重登） | 🔒 仅超管 |

### 权限体系

超管恒有全部权限；普通用户的权限由超管在「账号管理 → 权限」里单独配置，精细到每个功能与设置项：`content.manage`、`content.pin`、`content.edit`、`settings.<key>` 等。

## 📜 开源许可

本项目基于 [MIT License](LICENSE) 开源，欢迎学习、使用与二次开发。
