#!/usr/bin/env bash
# ============================================================
#  校园墙（表白墙）+ 广播站点歌系统  一键部署脚本
#  用法（服务器上执行，需 root）：
#    国内：bash -c "$(curl -sSL https://cdn.jsdelivr.net/gh/xihe41017/confession-wall@main/deploy/install.sh)"
#    海外：bash -c "$(curl -sSL https://raw.githubusercontent.com/xihe41017/confession-wall/main/deploy/install.sh)"
#
#  可选环境变量（提前 export 可覆盖默认值）：
#    DOMAIN=你的域名        # 配置到 Nginx（可选，默认用 IP）
#    ADMIN_PASSWORD=xxx      # 表白墙超管密码（默认随机生成）
#    RADIO_ADMIN_PASSWORD=xxx # 点歌系统管理员密码（默认随机生成）
# ============================================================
set -euo pipefail

# ---------- 颜色 ----------
C_G='\033[0;32m'; C_Y='\033[0;33m'; C_B='\033[0;34m'; C_R='\033[0;31m'; C_0='\033[0m'
info() { echo -e "${C_B}[信息]${C_0} $*"; }
ok()   { echo -e "${C_G}[成功]${C_0} $*"; }
warn() { echo -e "${C_Y}[注意]${C_0} $*"; }
err()  { echo -e "${C_R}[错误]${C_0} $*"; exit 1; }

# ---------- 配置 ----------
GIT_USER="xihe41017"
BASE="/opt/campus"
CONF_REPO="confession-wall"
RADIO_REPO="radio-song"
CONF_DIR="$BASE/$CONF_REPO"
RADIO_DIR="$BASE/$RADIO_REPO"
DOMAIN="${DOMAIN:-_}"

# 生成随机密码/密钥（|| true 避免 pipefail 下 head 提前退出触发 SIGPIPE）
rand() { head -c 48 /dev/urandom | base64 | tr -dc 'a-zA-Z0-9' | head -c "${1:-18}" || true; }
ADMIN_PASSWORD="${ADMIN_PASSWORD:-$(rand)}"
JWT_SECRET="${JWT_SECRET:-$(rand 32)$(rand 32)}"
RADIO_ADMIN_PASSWORD="${RADIO_ADMIN_PASSWORD:-$(rand)}"
RADIO_JWT_SECRET="${RADIO_JWT_SECRET:-$(rand 32)$(rand 32)}"

# ---------- 前置检查 ----------
[ "$(id -u)" -eq 0 ] || err "请用 root 运行：sudo bash -c \"\$(curl ...)\""
if command -v apt-get >/dev/null 2>&1; then PKG=apt
elif command -v yum >/dev/null 2>&1; then PKG=yum
else err "仅支持 Debian/Ubuntu/CentOS/RHEL"; fi
command -v curl >/dev/null 2>&1 || { info "安装 curl..."; $PKG install -y curl >/dev/null 2>&1; }

echo ""
info "============================================"
info "  校园墙 + 点歌系统  一键部署"
info "  系统: $PKG   目录: $BASE"
info "============================================"
echo ""

# ---------- 安装系统依赖 ----------
info "安装依赖（python3 / node / ffmpeg / nginx / git）..."
if [ "$PKG" = "apt" ]; then
  export DEBIAN_FRONTEND=noninteractive
  apt-get update -qq
  apt-get install -y -qq git python3 python3-venv python3-pip ffmpeg nginx >/dev/null
else
  yum install -y -q git python3 python3-pip python3-devel ffmpeg nginx >/dev/null 2>&1 || yum install -y -q git python3 python3-pip ffmpeg nginx >/dev/null
fi

# ---------- Node.js（Vite 8 需要 Node >= 20） ----------
if ! command -v node >/dev/null 2>&1 || [ "$(node -v | tr -dc '0-9' | cut -c1-2)" -lt 20 ]; then
  info "安装 Node.js 20 ..."
  if [ "$PKG" = "apt" ]; then
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash - >/dev/null 2>&1
    apt-get install -y -qq nodejs >/dev/null
  else
    curl -fsSL https://rpm.nodesource.com/setup_20.x | bash - >/dev/null 2>&1
    yum install -y -q nodejs >/dev/null
  fi
fi
node -v >/dev/null 2>&1 || err "Node.js 安装失败"
info "Node $(node -v) OK"

# ---------- 克隆项目 ----------
info "拉取项目代码..."
mkdir -p "$BASE"
cd "$BASE"
[ -d "$CONF_REPO" ] || git clone --depth 1 "https://github.com/$GIT_USER/$CONF_REPO.git"
[ -d "$RADIO_REPO" ] || git clone --depth 1 "https://github.com/$GIT_USER/$RADIO_REPO.git"

# ---------- 部署函数：后端 venv + 前端构建 ----------
deploy_backend() {
  local dir="$1" py
  info "配置后端依赖 $dir ..."
  cd "$dir/backend"
  python3 -m venv .venv
  .venv/bin/pip install --quiet --upgrade pip
  .venv/bin/pip install --quiet -r requirements.txt
}
deploy_frontend() {
  local dir="$1"
  info "构建前端 $dir ..."
  cd "$dir/frontend"
  npm install --no-audit --no-fund
  npm run build
}

info "========== 部署表白墙 =========="
deploy_backend "$CONF_DIR"
deploy_frontend "$CONF_DIR"
info "========== 部署点歌系统 =========="
deploy_backend "$RADIO_DIR"
deploy_frontend "$RADIO_DIR"

# ---------- 环境变量 ----------
info "写入环境配置（管理员密码/密钥）..."
mkdir -p /etc/campus
cat > /etc/campus/confession.env <<EOF
ADMIN_PASSWORD=$ADMIN_PASSWORD
JWT_SECRET=$JWT_SECRET
EOF
cat > /etc/campus/radio.env <<EOF
ADMIN_PASSWORD=$RADIO_ADMIN_PASSWORD
JWT_SECRET=$RADIO_JWT_SECRET
EOF
chmod 600 /etc/campus/*.env

# ---------- systemd 服务 ----------
info "创建 systemd 服务（开机自启 + 崩溃自动重启）..."
cat > /etc/systemd/system/campus-confession.service <<EOF
[Unit]
Description=Campus Wall (Confession Wall)
After=network.target
[Service]
WorkingDirectory=$CONF_DIR/backend
EnvironmentFile=/etc/campus/confession.env
ExecStart=$CONF_DIR/backend/.venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=3
[Install]
WantedBy=multi-user.target
EOF
cat > /etc/systemd/system/campus-radio.service <<EOF
[Unit]
Description=Campus Radio Song Request
After=network.target
[Service]
WorkingDirectory=$RADIO_DIR/backend
EnvironmentFile=/etc/campus/radio.env
ExecStart=$RADIO_DIR/backend/.venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 8001
Restart=always
RestartSec=3
[Install]
WantedBy=multi-user.target
EOF
systemctl daemon-reload
systemctl enable campus-confession campus-radio >/dev/null 2>&1
systemctl restart campus-confession campus-radio

# ---------- Nginx ----------
info "配置 Nginx 反向代理..."
if [ "$PKG" = "apt" ]; then
  NGINX_SITE=/etc/nginx/sites-available/campus
  NGINX_ENABLED=/etc/nginx/sites-enabled/campus
else
  NGINX_SITE=/etc/nginx/conf.d/campus.conf
  NGINX_ENABLED=/etc/nginx/conf.d/campus.conf
fi
cat > "$NGINX_SITE" <<EOF
# 校园墙（表白墙）：http://服务器IP/
server {
    listen 80;
    server_name $DOMAIN;
    client_max_body_size 60m;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Forwarded-For \$remote_addr;
        proxy_read_timeout 60s;
    }
}
EOF
if [ "$PKG" = "apt" ]; then
  ln -sf "$NGINX_SITE" "$NGINX_ENABLED"
  rm -f /etc/nginx/sites-enabled/default 2>/dev/null || true
fi
nginx -t >/dev/null 2>&1 && systemctl reload nginx || warn "Nginx 配置未通过测试，请手动检查"

# ---------- 防火墙 ----------
if command -v ufw >/dev/null 2>&1; then
  ufw allow 80/tcp >/dev/null 2>&1
  ufw allow 8001/tcp >/dev/null 2>&1
fi

# ---------- 结果 ----------
sleep 2
CONF_OK=$(curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:8000/ || true)
RADIO_OK=$(curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:8001/ || true)

echo ""
ok "============================================"
ok "  部署完成！"
ok "============================================"
echo ""
echo -e "${C_Y}  校园墙：${C_0}   http://服务器IP/         (状态: $CONF_OK)"
echo -e "${C_Y}  点歌台：${C_0}   http://服务器IP:8001/   (状态: $RADIO_OK)"
echo ""
echo -e "  ${C_B}表白墙超管：${C_0} admin / ${C_G}$ADMIN_PASSWORD${C_0}"
echo -e "  ${C_B}点歌管理员：${C_0} admin / ${C_G}$RADIO_ADMIN_PASSWORD${C_0}"
echo ""
warn "请立即保存上面的密码！"
warn "若配置了域名，可手动把 Nginx 的 server_name 改为你的域名。"
warn "常用命令："
echo "    systemctl status campus-confession   # 查看表白墙服务"
echo "    systemctl status campus-radio        # 查看点歌服务"
echo "    systemctl restart campus-confession campus-radio  # 重启"
echo ""
