"""写入示例内容数据（仅本地开发用）。用法：.venv/Scripts/python seed_demo.py"""
import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from datetime import datetime, timedelta

from app.database import Base, SessionLocal, engine
from app.models import Comment, Post, PostLike

Base.metadata.create_all(bind=engine)
db = SessionLocal()
db.query(Comment).delete()
db.query(PostLike).delete()
db.query(Post).delete()

demo = [
    {
        "to_name": "隔壁班的周同学",
        "nickname": "篮球场的常客",
        "content": "每次路过你们班门口都会偷偷看你一眼，\n你穿校服的样子真的很好看。\n毕业前，我一定要把这句话说出口。",
        "theme": "pink",
        "days_ago": 2,
        "likes": 128,
    },
    {
        "to_name": "图书馆四楼的小姐姐",
        "nickname": "占座选手",
        "content": "你每天下午都在图书馆四楼靠窗的位置，\n我在这张桌子上坐了两个月，\n其实只是想多看你几眼。",
        "theme": "blue",
        "days_ago": 3,
        "likes": 96,
    },
    {
        "to_name": None,
        "nickname": "匿名同学",
        "content": "喜欢你三年了，从高一军训开始。\n今天我终于鼓起勇气写了这张纸条，\n如果看到，能不能回我一个小微笑？",
        "theme": "purple",
        "days_ago": 5,
        "likes": 201,
    },
    {
        "to_name": "合唱团的学长",
        "nickname": "小透明",
        "content": "你的声音真的很好听。\n每次文艺汇演我都在台下，\n这首歌唱给你，也唱给我自己的青春。",
        "theme": "mint",
        "days_ago": 7,
        "likes": 74,
    },
]

now = datetime.now()
for i, d in enumerate(demo):
    post = Post(
        to_name=d["to_name"],
        nickname=d["nickname"],
        content=d["content"],
        theme=d["theme"],
        likes=d["likes"],
        status="approved",
        ip=f"127.0.0.{i + 1}",
        created_at=now - timedelta(days=d["days_ago"]),
    )
    db.add(post)
    db.flush()
    if i == 0:
        db.add(
            Comment(
                post_id=post.id, nickname="热心同学",
                content="冲鸭！毕业前一定要说出来！",
                created_at=now - timedelta(days=1),
            )
        )
        db.add(
            Comment(
                post_id=post.id, nickname="课代表",
                content="我支持你，勇敢一点！",
                created_at=now - timedelta(hours=5),
            )
        )

db.commit()
print(f"已写入 {len(demo)} 条示例内容（账号、设置保持不变）")
db.close()
