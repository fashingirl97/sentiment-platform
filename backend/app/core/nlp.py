"""NLP 认知分析：情感倾向、细粒度情绪、风险等级、舆情烈度指数。

采用规则引擎实现（情感词典 + 敏感词 + 互动量 + KOL 权重），
无需外部模型即可离线运行，保证演示效果稳定可控。
"""
import math

# ---------- 情感词典 ----------
POSITIVE_WORDS = {
    "优秀", "满意", "好评", "流畅", "稳定", "续航强", "散热好", "推荐", "值得", "性价比高",
    "给力", "不错", "完美", "惊喜", "赞", "喜欢", "支持", "放心", "耐用", "清晰", "轻薄",
    "美观", "快速", "好用", "安全", "及时", "专业", "负责", "真诚", "处理迅速", "退款到账",
    "补偿", "道歉", "改进", "修复", "固件升级", "优化", "解决", "换新", "召回", "承诺",
}
NEGATIVE_WORDS = {
    "发热", "烫手", "续航差", "掉电", "卡顿", "死机", "重启", "黑屏", "闪退", "缺陷",
    "翻车", "垃圾", "差评", "失望", "退货", "投诉", "维权", "虚假宣传", "夸大", "缩水",
    "瑕疵", "品控差", "做工差", "偷工减料", "欺骗", "坑", "闹心", "后悔", "崩溃",
    "漏液", "鼓包", "爆炸", "起火", "冒烟", "售后差", "推诿", "踢皮球", "不处理",
    "变质", "拉肚子", "腹泻", "呕吐", "过期", "异物", "脏", "老鼠", "蟑螂", "卫生差",
}

# 负向情绪细分词典
EMOTION_DICT = {
    "愤怒": {"欺骗", "坑", "垃圾", "爆炸", "起火", "起火爆炸", "恶劣", "无耻", "黑心", "愤怒", "可恨", "抵制"},
    "失望": {"失望", "后悔", "翻车", "缩水", "虚假宣传", "夸大", "不如", "落差", "心寒"},
    "恐慌": {"安全", "隐患", "起火", "爆炸", "漏液", "鼓包", "危险", "恐慌", "担心", "不敢用", "致癌", "有毒"},
    "质疑": {"质疑", "凭什么", "真的吗", "公关", "掩盖", "洗白", "甩锅", "敷衍", "为什么", "怎么回事", "水分", "造假"},
}

# 高危敏感词（命中即触发高危预警）
HIGH_RISK_WORDS = {
    "爆炸", "起火", "致癌", "有毒", "死亡", "致伤", "安全事故", "大规模", "集体", "维权群",
    "监管部门", "市场监管局", "消协", "媒体曝光", "热搜", "抵制", "召回", "重大事故",
    "食物中毒", "传染病", "鼠疫", "疫情", "违法", "欺诈", "跑路", "诈骗", "退一赔三",
}


def analyze_sentiment(text: str) -> dict:
    """情感倾向 + 细粒度情绪识别。"""
    pos = sum(1 for w in POSITIVE_WORDS if w in text)
    neg = sum(1 for w in NEGATIVE_WORDS if w in text)

    if neg > pos:
        sentiment = "negative"
    elif pos > neg:
        sentiment = "positive"
    else:
        sentiment = "neutral"

    # 细粒度情绪（仅负向时细分）
    emotion = ""
    if sentiment == "negative":
        best_score = 0
        for emo, words in EMOTION_DICT.items():
            score = sum(1 for w in words if w in text)
            if score > best_score:
                best_score = score
                emotion = emo
    return {"sentiment": sentiment, "emotion": emotion, "pos_count": pos, "neg_count": neg}


def detect_high_risk(text: str) -> list[str]:
    """命中高危敏感词列表。"""
    return [w for w in HIGH_RISK_WORDS if w in text]


def compute_heat_index(
    sentiment: str,
    emotion: str,
    like: int = 0,
    comment: int = 0,
    share: int = 0,
    author_type: str = "normal",
    high_risk_hits: int = 0,
) -> float:
    """计算舆情烈度指数（0~100）。

    综合：情感负向、情绪强度、互动量、KOL 权重、高危敏感词命中。
    """
    score = 0.0

    # 1. 情感基础分
    if sentiment == "negative":
        score += 30
    elif sentiment == "neutral":
        score += 10

    # 2. 细粒度情绪加成
    emotion_bonus = {"愤怒": 22, "恐慌": 20, "质疑": 15, "失望": 12}
    score += emotion_bonus.get(emotion, 0)

    # 3. 互动量（转评赞）—— 对数平滑
    engagement = like + comment * 2 + share * 3
    score += min(20, math.log1p(engagement) * 2.2)

    # 4. KOL 账号权重
    author_bonus = {"kol": 15, "normal": 5, "water": -8}
    score += author_bonus.get(author_type, 5)

    # 5. 高危敏感词命中
    score += min(25, high_risk_hits * 15)

    return round(max(0.0, min(100.0, score)), 1)


def risk_level_from_heat(heat: float) -> str:
    """由舆情烈度映射为 S/A/B/C 四级风险。"""
    if heat >= 85:
        return "S"
    if heat >= 65:
        return "A"
    if heat >= 40:
        return "B"
    return "C"


RISK_LEVEL_TEXT = {"S": "极高危", "A": "高危", "B": "中危", "C": "低危"}
