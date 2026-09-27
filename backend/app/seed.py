"""模拟数据初始化：用户、信源、主题、配置、事件、舆情内容、预警、报告。

演示场景：星耀 X20 Pro 手机发布后「发热/续航」质量争议舆情。
"""
import json
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from .core.report import build_event_report
from .database import Base, engine, SessionLocal
from .models import (Alert, Config, Disposition, Event, Post, Report, Source,
                     Topic, User)
from .pipeline import analyze_post, reset_dedup_index
from .security import hash_password

# ---------- 信源 ----------
SOURCES = [
    {"name": "微博", "type": "social"},
    {"name": "今日头条", "type": "news"},
    {"name": "抖音", "type": "video"},
    {"name": "知乎", "type": "forum"},
    {"name": "数码论坛", "type": "forum"},
]

# ---------- 默认用户 ----------
USERS = [
    {"username": "admin", "password": "admin123", "name": "系统管理员", "role": "admin"},
    {"username": "analyst", "password": "analyst123", "name": "张分析", "role": "analyst"},
    {"username": "pr", "password": "pr123", "name": "李公关", "role": "pr"},
]

# ---------- 监测主题 ----------
TOPIC = {
    "name": "星耀 X20 Pro 质量舆情",
    "description": "监测星耀 X20 Pro 手机发布后的发热、续航、品控、售后等质量相关舆情",
    "keywords": ["星耀", "X20 Pro", "发热", "续航", "烫手", "死机", "品控", "退货", "售后"],
}

# ---------- 舆情内容模板（消费电子质量争议） ----------
# 每项: content, author, author_type, platform(信源名), hours_ago, like, comment, share, 可选 ocr/asr/images
DEMO_POSTS = [
    # ===== 阶段一：首发（48~36h 前）=====
    {"content": "刚入手的星耀 X20 Pro，玩游戏半小时就烫得拿不住，续航也崩，一天两充都顶不住，太失望了。", "author": "数码小白", "author_type": "normal", "platform": "微博", "hours_ago": 48, "like": 32, "comment": 18, "share": 5},
    {"content": "星耀 X20 Pro 到手三天，发热问题确实存在，但续航我觉得还行，轻度使用一天没问题。", "author": "手机爱好者", "author_type": "normal", "platform": "微博", "hours_ago": 46, "like": 12, "comment": 8, "share": 1},
    {"content": "星耀 X20 Pro 打原神直接掉帧卡顿，机身温度飙到 45 度，这散热设计是认真的吗？", "author": "游戏党阿凯", "author_type": "normal", "platform": "数码论坛", "hours_ago": 44, "like": 45, "comment": 30, "share": 8},
    {"content": "新买的星耀 X20 Pro 用了两天，屏幕显示很细腻，拍照也不错，就是玩游戏发热有点明显。", "author": "科技小白兔", "author_type": "normal", "platform": "知乎", "hours_ago": 42, "like": 20, "comment": 6, "share": 0},
    {"content": "星耀 X20 Pro 续航虚标了吧，官方说一天一充，我下午三点就 20% 了，就刷个视频。", "author": "打工人小李", "author_type": "normal", "platform": "微博", "hours_ago": 40, "like": 58, "comment": 42, "share": 12},

    # ===== 阶段二：扩散（36~24h 前）=====
    {"content": "抖音刷到星耀 X20 Pro 发热的短视频，评论区都在说烫手，这机子是不是翻车了？", "author": "吃瓜群众", "author_type": "normal", "platform": "抖音", "hours_ago": 35, "like": 120, "comment": 86, "share": 23, "asr_text": "大家看，星耀 X20 Pro 玩了二十分钟游戏，机身温度已经到了四十六度，烫手得很"},
    {"content": "星耀 X20 Pro 发热问题冲上热搜了，我看了一眼自己的手机，也烫，品控真不行。", "author": "路人甲", "author_type": "normal", "platform": "微博", "hours_ago": 34, "like": 210, "comment": 150, "share": 40},
    {"content": "星耀 X20 Pro 的散热模块设计有缺陷，高负载下热量集中在摄像头下方，这是工程问题。", "author": "老张测评", "author_type": "kol", "platform": "数码论坛", "hours_ago": 33, "like": 850, "comment": 320, "share": 180},
    {"content": "星耀官方客服让我送检测，来回要一周，这售后也太能推诿了，消费者权益谁来保障？", "author": "退货小王子", "author_type": "kol", "platform": "微博", "hours_ago": 31, "like": 640, "comment": 280, "share": 150},
    {"content": "星耀 X20 Pro 续航确实一般，但也没到不能用的程度，网上有点夸大了吧。", "author": "理性看机", "author_type": "normal", "platform": "知乎", "hours_ago": 30, "like": 90, "comment": 55, "share": 8},
    {"content": "我用了星耀 X20 Pro 一周，日常不玩游戏，发热基本无感，续航一天一充，挺满意的。", "author": "上班族小王", "author_type": "normal", "platform": "微博", "hours_ago": 29, "like": 40, "comment": 20, "share": 3},
    {"content": "星耀 X20 Pro 的品控堪忧，我和同事一起买的，他的机身有瑕疵，屏幕边缘漏液了。", "author": "真实用户", "author_type": "normal", "platform": "数码论坛", "hours_ago": 28, "like": 180, "comment": 95, "share": 30},
    {"content": "星耀 X20 Pro 玩游戏发热卡顿，退货还要自己承担检测费，这售后政策霸王条款。", "author": "愤怒的买家", "author_type": "normal", "platform": "微博", "hours_ago": 27, "like": 156, "comment": 88, "share": 26},
    {"content": "星耀 X20 Pro 视频里实测温度 46 度，大家注意了，这散热真的有问题，别买。", "author": "数码阿峰", "author_type": "kol", "platform": "抖音", "hours_ago": 26, "like": 1200, "comment": 460, "share": 320, "asr_text": "实测星耀 X20 Pro 游戏十五分钟，正面最高温度四十六点三度，背面四十四度，这个散热确实不太行"},
    {"content": "感觉星耀 X20 Pro 的发热是系统优化问题，等固件升级应该能解决，先观望。", "author": "数码老兵", "author_type": "normal", "platform": "知乎", "hours_ago": 25, "like": 75, "comment": 40, "share": 6},
    {"content": "星耀 X20 Pro 续航崩了，早上满电出门，中午就 30%，就聊微信刷短视频。", "author": "学生党小陈", "author_type": "normal", "platform": "微博", "hours_ago": 24, "like": 130, "comment": 70, "share": 18},

    # ===== 阶段三：引爆（24~12h 前）=====
    {"content": "星耀 X20 Pro 发热和续航问题，官方到现在没有正式回应，是不是在掩盖什么？消费者需要真相！", "author": "科技大李", "author_type": "kol", "platform": "微博", "hours_ago": 23, "like": 2100, "comment": 980, "share": 650},
    {"content": "星耀 X20 Pro 翻车了！发热、续航、品控三大问题集中爆发，买到就是踩坑。", "author": "极客小王", "author_type": "kol", "platform": "今日头条", "hours_ago": 22, "like": 1800, "comment": 760, "share": 500},
    {"content": "星耀 X20 Pro 用户集体维权，要求官方召回问题批次，这已经不是个例了。", "author": "手机圈老王", "author_type": "kol", "platform": "微博", "hours_ago": 21, "like": 1560, "comment": 720, "share": 480},
    {"content": "星耀 X20 Pro 相关话题阅读量破亿，市场监管局和消协是不是该介入了？", "author": "媒体观察员", "author_type": "normal", "platform": "今日头条", "hours_ago": 20, "like": 980, "comment": 460, "share": 210},
    {"content": "我买的星耀 X20 Pro 三天就死机重启了三次，找售后让我恢复出厂设置，根本不管用，失望透顶。", "author": "苦主一号", "author_type": "normal", "platform": "微博", "hours_ago": 19, "like": 420, "comment": 230, "share": 65},
    {"content": "星耀 X20 Pro 的电池健康度掉得飞快，用了两周就掉到 95%，这续航和电池质量都有问题。", "author": "技术宅小林", "author_type": "normal", "platform": "知乎", "hours_ago": 18, "like": 350, "comment": 180, "share": 40},
    {"content": "星耀官方客服说发热是正常现象，游戏手机都这样，这解释也太敷衍了吧，质疑！", "author": "维权群众", "author_type": "normal", "platform": "微博", "hours_ago": 17, "like": 520, "comment": 310, "share": 90},
    {"content": "对比了同价位的友商旗舰，星耀 X20 Pro 发热和续航确实垫底，宣传的散热系统去哪了？", "author": "数码阿峰", "author_type": "kol", "platform": "数码论坛", "hours_ago": 16, "like": 1450, "comment": 560, "share": 390},
    {"content": "星耀 X20 Pro 是不是虚假宣传？发布会吹的散热黑科技，实际烫手，这算不算欺诈？", "author": "较真先生", "author_type": "normal", "platform": "知乎", "hours_ago": 15, "like": 680, "comment": 320, "share": 140},
    {"content": "星耀 X20 Pro 质量争议上热搜了，作为首批用户，我只想说品控确实该抓一抓了。", "author": "首批用户", "author_type": "normal", "platform": "微博", "hours_ago": 14, "like": 310, "comment": 150, "share": 35},
    {"content": "星耀 X20 Pro 退货排队都排到一周后了，售后电话打不通，这用户体验绝了。", "author": "退货运费险", "author_type": "normal", "platform": "微博", "hours_ago": 13, "like": 270, "comment": 140, "share": 30},
    {"content": "其实星耀 X20 Pro 拍照和屏幕都不错，就是发热拖了后腿，希望官方出个降频补丁。", "author": "理性消费者", "author_type": "normal", "platform": "知乎", "hours_ago": 12, "like": 150, "comment": 80, "share": 12},

    # ===== 阶段四：高峰（12~2h 前）=====
    {"content": "星耀 X20 Pro 官方终于发声明了，说会推出固件优化散热和续航，还承诺延长保修，大家怎么看？", "author": "媒体观察员", "author_type": "normal", "platform": "今日头条", "hours_ago": 10, "like": 890, "comment": 430, "share": 180},
    {"content": "星耀官方回应了，态度还算诚恳，但光道歉不行，得拿出实际行动来。", "author": "理智用户", "author_type": "normal", "platform": "微博", "hours_ago": 9, "like": 240, "comment": 120, "share": 25},
    {"content": "星耀 X20 Pro 固件升级之后发热确实好了一些，续航也有改善，希望继续优化。", "author": "科技小白兔", "author_type": "normal", "platform": "微博", "hours_ago": 8, "like": 180, "comment": 90, "share": 20},
    {"content": "星耀这次回应还算快，承诺召回问题批次，支持有担当的企业。", "author": "普通消费者", "author_type": "normal", "platform": "微博", "hours_ago": 7, "like": 160, "comment": 70, "share": 15},
    {"content": "星耀 X20 Pro 问题批次召回，我正好是那批，已经登记换新了，处理还算顺利。", "author": "苦主一号", "author_type": "normal", "platform": "微博", "hours_ago": 6, "like": 130, "comment": 60, "share": 10},
    {"content": "星耀 X20 Pro 售后现在响应快了，检测免费，还提供备用机，这次改进点赞。", "author": "上班族小王", "author_type": "normal", "platform": "数码论坛", "hours_ago": 5, "like": 90, "comment": 45, "share": 8},
    {"content": "星耀 X20 Pro 发热争议慢慢平息了，官方处理及时，品牌信任算是保住了。", "author": "数码老兵", "author_type": "normal", "platform": "知乎", "hours_ago": 4, "like": 110, "comment": 55, "share": 9},
    {"content": "星耀 X20 Pro 新固件推送了，我升级后玩原神温度降了 5 度，散热优化有效果。", "author": "游戏党阿凯", "author_type": "normal", "platform": "数码论坛", "hours_ago": 3, "like": 140, "comment": 70, "share": 18},
    {"content": "星耀 X20 Pro 换了新机，这次没有发热问题，看来是批次品控问题，官方态度可以。", "author": "换新用户", "author_type": "normal", "platform": "微博", "hours_ago": 2, "like": 120, "comment": 58, "share": 12},

    # ===== 水军刷量样本（高度重复，SimHash 去重演示）=====
    {"content": "星耀 X20 Pro 太棒了，性能强劲，续航持久，散热出色，强烈推荐大家购买！", "author": "用户889123", "author_type": "water", "platform": "微博", "hours_ago": 20, "like": 1, "comment": 0, "share": 0},
    {"content": "星耀 X20 Pro 太棒了，性能强劲，续航持久，散热出色，强烈推荐大家购买！", "author": "用户665211", "author_type": "water", "platform": "微博", "hours_ago": 20, "like": 1, "comment": 0, "share": 0},
    {"content": "星耀 X20 Pro 太棒了，性能强劲，续航持久，散热出色，强烈推荐大家购买！", "author": "用户332456", "author_type": "water", "platform": "微博", "hours_ago": 20, "like": 1, "comment": 0, "share": 0},
    {"content": "星耀 X20 Pro 质量非常好，用了都说好，散热一流，续航无敌，买它准没错。", "author": "用户998712", "author_type": "water", "platform": "数码论坛", "hours_ago": 19, "like": 2, "comment": 0, "share": 0},
    {"content": "星耀 X20 Pro 质量非常好，用了都说好，散热一流，续航无敌，买它准没错。", "author": "用户775210", "author_type": "water", "platform": "数码论坛", "hours_ago": 19, "like": 1, "comment": 0, "share": 0},
]

# 事件概要
EVENT = {
    "title": "星耀 X20 Pro 发热与续航质量争议",
    "category": "质量争议",
    "summary": "星耀 X20 Pro 发布后，用户在社交媒体与论坛集中反馈游戏发热烫手、续航虚标、偶发死机等问题，随后 KOL 评测与新闻媒体跟进，事件快速发酵并冲上热搜，星耀官方回应后推出固件优化与召回政策，舆情逐步平息。",
}


def init_db():
    """初始化数据库结构与演示数据。"""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        _init_base_data(db)
        _init_demo_event(db)
        db.commit()
        print("[seed] 演示数据初始化完成")
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()


def _init_base_data(db: Session):
    # 用户
    for u in USERS:
        db.add(User(username=u["username"], password_hash=hash_password(u["password"]), name=u["name"], role=u["role"]))
    # 信源
    for s in SOURCES:
        db.add(Source(name=s["name"], type=s["type"], enabled=True))
    # 主题
    db.add(Topic(name=TOPIC["name"], description=TOPIC["description"], keywords=json.dumps(TOPIC["keywords"], ensure_ascii=False)))
    # 配置
    configs = [
        {"key": "negative_surge_threshold", "value": "2.0", "description": "单小时负向声量环比激增阈值（倍）"},
        {"key": "alert_channels", "value": json.dumps(["站内信", "邮件", "短信"], ensure_ascii=False), "description": "告警通知渠道"},
        {"key": "risk_threshold_s", "value": "85", "description": "S 级极高危烈度阈值"},
        {"key": "risk_threshold_a", "value": "65", "description": "A 级高危烈度阈值"},
        {"key": "risk_threshold_b", "value": "40", "description": "B 级中危烈度阈值"},
        {"key": "llm_enabled", "value": "false", "description": "是否启用外部大模型（未配置密钥自动降级规则引擎）"},
    ]
    for c in configs:
        db.add(Config(**c))
    db.flush()


def _init_demo_event(db: Session):
    event = Event(
        title=EVENT["title"],
        summary=EVENT["summary"],
        category=EVENT["category"],
        risk_level="A",
        status="handling",
        heat_index=78.5,
        created_at=datetime.now() - timedelta(hours=48),
    )
    db.add(event)
    db.flush()

    # 信源 id 映射
    sources = {s.name: s.id for s in db.query(Source).all()}
    topic_id = db.query(Topic).first().id

    reset_dedup_index()
    posts = []
    for raw in DEMO_POSTS:
        raw = dict(raw)
        raw["topic_id"] = topic_id
        raw["source_id"] = sources.get(raw["platform"], sources["微博"])
        raw["event_id"] = event.id
        posts.append(analyze_post(db, raw))

    # 更新事件统计
    real_posts = [p for p in posts if not p.is_duplicate]
    if real_posts:
        sorted_posts = sorted(real_posts, key=lambda p: p.publish_time)
        event.total_volume = len(real_posts)
        event.first_post_id = sorted_posts[0].id
        event.first_source = sorted_posts[0].platform
        event.first_time = sorted_posts[0].publish_time
        neg = sum(1 for p in real_posts if p.sentiment == "negative")
        event.sentiment_negative_ratio = round(neg / len(real_posts) * 100, 1)
        event.heat_index = round(max(p.heat_index for p in real_posts), 1)

    # 预生成一份专项报告
    content = build_event_report(
        event,
        [p for p in posts if not p.is_duplicate],
        __import__("app.core.clustering", fromlist=["cluster_opinions"]).cluster_opinions([p for p in posts if not p.is_duplicate]),
        __import__("app.core.graph", fromlist=["build_timeline"]).build_timeline(event.id, [p for p in posts if not p.is_duplicate]),
        [],
        db.query(Source).all(),
    )
    db.add(Report(title=f"{event.title} 舆情专项研判报告", type="special", event_id=event.id, content_md=content, created_by="系统"))


if __name__ == "__main__":
    init_db()
