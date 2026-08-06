"""端到端测试：账号、匿名限发、权限、拉黑、设置、限流。
所有请求走前端代理(5173)或后端(8000)。用法：.venv/Scripts/python e2e_test.py [base_url]
"""
import json
import sys
import urllib.error
import urllib.request

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8000"

_passed = 0
_failed = 0


def req(method, path, data=None, headers=None):
    body = json.dumps(data, ensure_ascii=False).encode("utf-8") if data is not None else None
    r = urllib.request.Request(
        BASE + path, data=body, method=method,
        headers={"Content-Type": "application/json", "X-Device-Id": "test-device-001", **(headers or {})},
    )
    try:
        with urllib.request.urlopen(r) as resp:
            txt = resp.read().decode("utf-8")
            return resp.status, json.loads(txt) if txt else None
    except urllib.error.HTTPError as e:
        txt = e.read().decode("utf-8")
        return e.code, json.loads(txt) if txt else None


def check(name, cond, extra=""):
    global _passed, _failed
    if cond:
        _passed += 1
        print(f"[PASS] {name} {extra}")
    else:
        _failed += 1
        print(f"[FAIL] {name} {extra}")


A = lambda ip: {"X-Forwarded-For": ip}  # 模拟不同 IP

# ---------- 1. 站点信息 ----------
s, d = req("GET", "/api/site/info")
check("站点信息", s == 200 and d["site_name"] and d["anonymous_post_limit"] == 3,
      f"name={d.get('site_name')} limit={d.get('anonymous_post_limit')}")

# ---------- 2. 注册 ----------
s, d = req("POST", "/api/auth/register", {
    "username": "student1", "password": "pass123456",
    "nickname": "小明", "class_name": "高一3班", "school": "第一中学",
}, A("100.1.1.1"))
check("注册(含班级学校)", s == 201 and d["user"]["school"] == "第一中学" and d.get("token"), "")
u1 = d["user"]
tok1 = d["token"]
T1 = {"Authorization": f"Bearer {tok1}"}

s, d = req("GET", "/api/auth/me", headers=T1)
check("me 接口", s == 200 and d["nickname"] == "小明", f"nickname={d.get('nickname')}")

# ---------- 3. 匿名限发（IP 200.1.1.1） ----------
for i in range(3):
    s, d = req("POST", "/api/posts", {"content": f"匿名内容 {i}"}, A("200.1.1.1"))
    check(f"匿名发布第{i+1}条", s == 201, "")
s, d = req("POST", "/api/posts", {"content": "第4条，应被拒"}, A("200.1.1.1"))
check("匿名第4条被限发", s == 429, f"code={s}")

# ---------- 4. 登录用户不限发 ----------
s, d = req("POST", "/api/posts", {"content": "登录用户发布，内容属于账号"}, headers=T1)
check("登录用户发布", s == 201 and d["author"] is not None and d["author"]["role"] == "user",
      f"author_role={d.get('author')}")

# ---------- 5. 管理员登录 & 统计 ----------
s, d = req("POST", "/api/admin/login", {"username": "admin", "password": "admin123"})
# 注意：登录用的是 /api/auth/login
s, d = req("POST", "/api/auth/login", {"username": "admin", "password": "admin123"})
check("超管登录", s == 200 and d["user"]["role"] == "super_admin", f"role={d.get('user',{}).get('role')}")
tokA = d["token"]
TA = {"Authorization": f"Bearer {tokA}"}

s, d = req("GET", "/api/admin/stats", headers=TA)
check("管理统计", s == 200 and d["total_users"] >= 1 and d["total_posts"] >= 4,
      f"users={d.get('total_users')} posts={d.get('total_posts')}")

# ---------- 6. 用户管理（超管） ----------
s, d = req("GET", "/api/admin/users?page_size=50", headers=TA)
check("用户列表", s == 200 and any(u["username"] == "student1" for u in d["items"]), f"total={d.get('total')}")
uid = next(u["id"] for u in d["items"] if u["username"] == "student1")

s, d = req("POST", f"/api/admin/users/{uid}/title", {"title": "校园之星"}, headers=TA)
check("下发头衔", s == 200 and d["title"] == "校园之星", f"title={d.get('title')}")

s, d = req("POST", f"/api/admin/users/{uid}/role", {"role": "admin"}, headers=TA)
check("提升为管理员", s == 200 and d["role"] == "admin", f"role={d.get('role')}")

# 管理员权限：改普通设置可以
s, d = req("GET", "/api/admin/settings", headers=T1)  # student1 已是 admin
check("管理员看设置列表", s == 200 and all(not (x["sensitive"] and x["value"] != "••••••") for x in d),
      "")
# 管理员改敏感项应 403
s, d = req("PUT", "/api/admin/settings/jwt_secret", {"value": "hacked"}, headers=T1)
check("管理员改敏感项被拒", s == 403, f"code={s}")
# 管理员改普通项可以
s, d = req("PUT", "/api/admin/settings/site_name", {"value": "校园墙"}, headers=T1)
check("管理员改站点名", s == 200, "")

# 超管改敏感项可以
s, d = req("PUT", "/api/admin/settings/jwt_secret", {"value": "new-secret-abc"}, headers=TA)
check("超管改敏感项", s == 200, "")
# 改密钥后旧 token 失效
s, d = req("GET", "/api/auth/me", headers=T1)
check("改密钥后旧token失效", s == 401, f"code={s}")
# 超管重新登录（旧 token 已失效）
s, d = req("POST", "/api/auth/login", {"username": "admin", "password": "admin123"})
TA = {"Authorization": f"Bearer {d['token']}"}
check("超管改密钥后重新登录", s == 200, "")

# ---------- 7. 拉黑账号 ----------
s, d = req("POST", f"/api/admin/users/{uid}/status", {"status": "banned"}, headers=TA)
check("拉黑账号", s == 200 and d["status"] == "banned", "")
# 被拉黑账号再登录应 403（student1 已拉黑；token 也已因改密钥失效）
s, d = req("POST", "/api/auth/login", {"username": "student1", "password": "pass123456"})
check("被拉黑账号登录被拒", s == 403, f"code={s}")

# ---------- 8. 拉黑 IP ----------
s, d = req("POST", "/api/admin/users/banned-ips", {"ip": "200.1.1.1", "reason": "刷屏"}, headers=TA)
check("拉黑IP", s == 201, "")
s, d = req("POST", "/api/posts", {"content": "被拉黑IP的匿名发布"}, A("200.1.1.1"))
check("拉黑IP发布被拒", s == 403, f"code={s}")
s, d = req("GET", "/api/admin/users/banned-ips", headers=TA)
check("黑名单列表", s == 200 and len(d) == 1, f"len={len(d) if s==200 else '-'}")

# ---------- 9. 注册审批设置 ----------
req("PUT", "/api/admin/settings/register_approval", {"value": "1"}, headers=TA)
s, d = req("POST", "/api/auth/register", {
    "username": "student2", "password": "pass123456", "nickname": "小红", "school": "第二中学",
}, A("100.2.2.2"))
check("注册审批模式下新用户待激活", s == 201 and d["user"]["status"] == "pending", f"status={d.get('user',{}).get('status')}")
s, d = req("POST", "/api/auth/login", {"username": "student2", "password": "pass123456"})
check("待激活用户登录被拒", s == 403, f"code={s}")
# 超管激活
s, d = req("GET", "/api/admin/users?search=student2", headers=TA)
uid2 = d["items"][0]["id"]
s, d = req("POST", f"/api/admin/users/{uid2}/status", {"status": "active"}, headers=TA)
check("超管激活用户", s == 200 and d["status"] == "active", "")
s, d = req("POST", "/api/auth/login", {"username": "student2", "password": "pass123456"})
check("激活后登录成功", s == 200, f"code={s}")

# ---------- 10. 权限：普通用户访问管理被拒 ----------
tok2 = d["token"]
s, d = req("GET", "/api/admin/stats", headers={"Authorization": f"Bearer {tok2}"})
check("普通用户访问管理被拒", s == 403, f"code={s}")

# ---------- 11. 限流：注册 6 次超限 ----------
hits = [req("POST", "/api/auth/register", {
    "username": f"spam{i}", "password": "pass123456", "nickname": f"x{i}", "school": "x",
}, A("77.7.7.7"))[0] for i in range(7)]
check("注册接口限流(5/分钟)", hits[5] == 429 or hits[6] == 429, f"codes={hits[-3:]}")

# ---------- 12. 大请求体拒绝 ----------
big = json.dumps({"content": "a" * 1000000}, ensure_ascii=False).encode()
r = urllib.request.Request(BASE + "/api/posts", data=big, method="POST",
                           headers={"Content-Type": "application/json"})
try:
    urllib.request.urlopen(r)
    check("大请求体被拒", False, "")
except urllib.error.HTTPError as e:
    check("大请求体被拒(413)", e.code == 413, f"code={e.code}")

print(f"\n===== 通过 {_passed} / {_passed + _failed} =====")
sys.exit(0 if _failed == 0 else 1)
