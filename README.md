# 🏫 平和一中校园墙

一个浪漫风格的校园墙网站（表白 / 心愿 / 吐槽 / 树洞都欢迎），前后端分离架构。

- **前端**：Vue 3 + Vite（QQ空间式单列时间线、启动页、无限滚动、移动端适配）
- **后端**：Python FastAPI + SQLite（账号系统、权限管理、速率限制、IP 拉黑）

## 功能

### 内容
| 功能 | 说明 |
| --- | --- |
| 单列时间线 | QQ 空间式布局，评论**内联展开**，不再跳转详情页 |
| 置顶 | 管理员/超管可将内容**置顶**，置顶内容永远排在墙最前，带 📌 标记 |
| 头衔展示 | 管理员/超管及被下发头衔的用户的**头衔徽章**显示在墙首页 |
| 懒加载 | 数据分批加载，划到底端自动加载下一页（无限滚动） |
| 点赞 | 每个 IP 仅可赞一次（防刷赞），动画反馈 |
| 评论 | 每条内容可评论互动 |
| **图片** | 发布可带最多 9 张图片（**匿名限 1 张**），**浏览器端自动压缩到 ≤2MB 后上传**，墙上九宫格展示、点击可看大图 |
| **短视频** | **登录后**可带 ≤15 秒短视频（≤15MB，客户端+服务端双重校验），墙上直接播放 |
| 启动页 | 先展示校徽，再加载资源，丝滑过渡进入首页 |
| 操作反馈 | 全局 toast 提示 + 确定/取消弹窗，所有操作有反馈 |

### 账号体系
| 功能 | 说明 |
| --- | --- |
| 注册 | 需填写昵称/班级/学校；**邮箱与电话至少填一项**；记录注册 IP、设备、浏览器 |
| 登录 | 普通用户可登录，发布不限次 |
| 修改密码 | 任意登录用户可修改自己的密码 |
| 匿名发布 | 未登录也可发布（可匿名可署名），但**单 IP / 设备 24 小时内限发 3 条**（首页有声明） |
| 头衔 | 管理员/超管有专属头衔，超管可给任意用户下发自定义头衔（个人页展示） |
| 注册审核 | 可开关「注册需管理员激活」，默认关闭 |

### 管理后台（`/admin`）
| 标签 | 说明 |
| --- | --- |
| 内容管理 | 默认「全部」；审核上墙、**置顶/取消置顶**、**编辑内容（赞数/对象/昵称）**、**编辑评论赞数**、拉黑发布 IP、删除内容与评论 |
| 账号管理 | **仅超管**：改角色、下发头衔、**单独配置每个用户的权限（细到每个设置项）**、重置密码、拉黑账号/IP |
| IP 黑名单 | 独立标签页：查看、解除拉黑 |
| 服务器设置 | 设置项按权限显示；**🔒敏感项（站点名、限速、请求体上限、JWT密钥）仅超管可改** |

### 权限体系
超管恒有全部权限；普通用户/管理员由超管在「账号管理 → 权限」里**单独配置**，可精细到每个功能与每个设置项：

| 权限键 | 说明 |
| --- | --- |
| `content.manage` | 内容审核 / 删除 |
| `content.pin` | 置顶 / 取消置顶 |
| `content.edit` | 编辑内容（赞数/对象/昵称） |
| `content.ban_ip` | 对内容拉黑 IP |
| `comment.edit` | 编辑评论点赞数 |
| `ban.manage` | IP 黑名单管理 |
| `settings.view` | 查看服务器设置 |
| `settings.<key>` | 修改对应设置项（公告/审核/注册/限发等） |

### 安全防护（面向公网）
- **速率限制**：默认全局宽松（1000 次/分钟兜底）；注册 20/分钟、登录 30/分钟、发布 20/分钟、评论 30/分钟、点赞 60/分钟，**均为设置项，仅超管可改**
- **请求体限制**：默认 512KB，超限 413，**上限仅超管可改**
- **IP 拉黑**：黑名单 IP 无法发布/评论/注册，内容管理与账号管理均可拉黑，IP黑名单页可解除
- **匿名限发**：未登录每 IP/设备限发（防刷墙），条数可配置
- 建议配合 Nginx `limit_req` / `limit_conn`（见下文部署配置）

## 目录结构

```
confession-wall/
├── backend/                 # FastAPI 后端
│   ├── app/
│   │   ├── main.py          # 入口（含生产静态托管 + 限流装配）
│   │   ├── config.py        # 环境变量 + 默认设置项定义
│   │   ├── models.py        # User / Setting / BannedIP / Post / Comment
│   │   ├── deps.py          # 当前用户 / 角色权限依赖、IP 识别
│   │   ├── settings_service.py  # 运行时设置（后台可改，带缓存）
│   │   ├── ratelimit.py     # slowapi 限流
│   │   ├── middleware.py    # 请求体大小限制
│   │   └── routers/         # auth / site / posts / comments / admin / users / settings
│   ├── data/confession.db   # SQLite 数据库（自动生成）
│   ├── run.py               # 本地启动
│   ├── seed_demo.py         # 示例数据
│   ├── e2e_test.py          # 端到端测试（31 项）
│   └── ps_cleanup.ps1       # Windows 端口清理脚本
└── frontend/                # Vue 3 前端
    ├── public/logo.jpg      # 校徽（启动页）
    ├── src/
    │   ├── store/auth.js    # 登录态
    │   ├── views/           # 墙 / 发布 / 账号 / 管理
    │   ├── components/      # 卡片(评论内联) / 管理后台子组件
    │   └── api/             # 请求封装（含设备标识头）
    └── vite.config.js       # 开发代理到 8000
```

## 本地运行（开发模式）

需要 Python 3.10+ 和 Node.js 18+。

```bash
# 1. 启动后端（终端 1）
cd backend
python -m venv .venv                       # 首次
.venv/Scripts/pip install -r requirements.txt   # Windows
.venv/Scripts/python run.py                # http://localhost:8000

# 2. 启动前端（终端 2）
cd frontend
npm install                                # 首次
npm run dev                                # http://localhost:5173
```

浏览器打开 **http://localhost:5173**，先看校徽启动页，再进入校园墙。

> 默认超级管理员：`admin / admin123`（首次启动自动创建，**上线前务必修改**）

## 生产运行（单进程，最简）

```bash
cd frontend && npm run build     # 生成 dist/
cd ../backend && .venv/Scripts/python run.py   # 访问 http://localhost:8000
```

后端检测到 `frontend/dist/` 后会自动托管页面，无需 Nginx 即可运行。

## 部署到服务器（Nginx + 防 DoS）

### 方案一：后端托管 + Nginx 反代（推荐）

```nginx
limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
limit_conn_zone $binary_remote_addr zone=conn:10m;

server {
    listen 80;
    server_name 你的域名或IP;

    # 基础防护
    client_max_body_size 1m;                 # 与后端 512KB 限制配合
    limit_conn conn 20;                      # 单 IP 并发连接数
    limit_req zone=api burst=20 nodelay;     # 全局限速兜底
    proxy_read_timeout 30s;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;  # 关键：让后端识别真实 IP
    }
}
```

> **重要**：`X-Forwarded-For` 必须设置，否则点赞防刷、匿名限发、IP 拉黑都会把所有人当成 127.0.0.1。

### 方案二：Nginx 托管前端 + 后端分离

```nginx
server {
    listen 80;
    server_name 你的域名;
    root /path/to/confession-wall/frontend/dist;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;    # SPA 回退
    }
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        client_max_body_size 1m;
    }
}
```

### 服务器依赖说明
- **ffmpeg/ffprobe**：视频时长校验依赖。服务器需安装 ffmpeg（或 `pip install imageio-ffmpeg` 自带二进制）。未安装时视频仍可上传，但无法校验 15 秒时长限制。
- 上传的文件存放在 `backend/data/uploads/`，随数据库一起备份。

### 生产安全清单
- ✅ 修改超级管理员密码（后台「服务器设置 → 修改我的密码」）
- ✅ 修改 JWT 密钥（后台「服务器设置 → jwt_secret」，改后全员需重新登录）
- ✅ 设置 `CORS_ORIGINS`（方案二跨域时需要）
- ✅ 建议开启 HTTPS（Let's Encrypt / 云厂商证书）
- 💡 公网规模大时可再套一层 CDN / 云 WAF（本应用限流为应用层兜底）

## 服务器设置项（后台可改）

| key | 默认 | 说明 | 权限 |
| --- | --- | --- | --- |
| `site_name` | 平和一中校园墙 | 站点名称 | 🔒 仅超管 |
| `site_announcement` | 空 | 首页公告 | 按权限 |
| `moderation_mode` | 0 | 1=发布需审核后上墙 | 按权限 |
| `allow_register` | 1 | 1=开放注册 | 按权限 |
| `register_approval` | 0 | 1=注册需管理员激活 | 按权限 |
| `anonymous_post_limit` | 3 | 未登录每 IP/设备限发条数 | 按权限 |
| `rate_register` | 20/minute | 注册接口限速 | 🔒 仅超管 |
| `rate_login` | 30/minute | 登录接口限速 | 🔒 仅超管 |
| `rate_post` | 20/minute | 发布接口限速 | 🔒 仅超管 |
| `rate_comment` | 30/minute | 评论接口限速 | 🔒 仅超管 |
| `rate_like` | 60/minute | 点赞接口限速 | 🔒 仅超管 |
| `rate_upload` | 10/minute | 上传接口限速 | 🔒 仅超管 |
| `max_body_kb` | 51200 | 请求体大小上限(KB)，默认50MB | 🔒 仅超管 |
| `image_max_mb` | 2 | 单张图片上传上限(MB，压缩后) | 🔒 仅超管 |
| `video_max_mb` | 15 | 单个视频上传上限(MB) | 🔒 仅超管 |
| `jwt_secret` | env | JWT 签名密钥 | 🔒 仅超管 |

> 「按权限」= 需对应 `settings.<key>` 权限，由超管在账号管理里单独授予/收回。

环境变量（首次启动播种默认值，数据库已有则忽略）：`ADMIN_USERNAME` / `ADMIN_PASSWORD` / `JWT_SECRET` / `PORT` / `CORS_ORIGINS`。

## 常用命令

```bash
# 重置内容并写入示例数据（保留账号与设置）
.venv/Scripts/python seed_demo.py

# 端到端接口测试（31 项，需要后端运行；可指定 base）
.venv/Scripts/python e2e_test.py
.venv/Scripts/python e2e_test.py http://127.0.0.1:5173   # 走前端代理

# Windows 下端口被占用时清理（会杀掉所有 python 进程）
powershell -ExecutionPolicy Bypass -File ps_cleanup.ps1
```

## 技术要点

- **权限模型**：`user / admin / super_admin` 三级；敏感设置与账号管理仅超管
- **匿名溯源**：未登录发布记录 IP + 设备 ID（前端 localStorage 生成）+ 请求头，超管可在后台查看/拉黑
- **防刷赞**：`post_likes` 表 `post_id + IP` 唯一约束
- **运行时设置**：设置存 SQLite，后台修改即时生效（带内存缓存）
- **SQLite 并发**：WAL 模式 + busy timeout，适合中小流量
