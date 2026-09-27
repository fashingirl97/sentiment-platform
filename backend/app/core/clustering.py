"""核心观点聚类与意图提炼（基于关键词 + SimHash 相似度）。"""
from collections import Counter, defaultdict

from .simhash import compute_simhash, hamming_distance

# 观点类别库（关键词 -> 观点标签）
OPINION_RULES = [
    ({"发热", "烫手", "烫", "过热", "暖手宝"}, "产品发热严重", "negative"),
    ({"续航", "掉电", "电量", "耗电", "续航崩"}, "续航虚标不耐用", "negative"),
    ({"卡顿", "死机", "重启", "黑屏", "闪退", "掉帧"}, "性能卡顿/系统不稳定", "negative"),
    ({"售后", "推诿", "踢皮球", "退货难", "不处理", "客服"}, "售后推诿难处理", "negative"),
    ({"虚假宣传", "夸大", "缩水", "宣传", "广告"}, "宣传夸大涉嫌虚假", "negative"),
    ({"品控", "做工", "瑕疵", "漏液", "鼓包"}, "品控做工差", "negative"),
    ({"召回", "换新", "退款", "补偿", "道歉", "整改"}, "要求召回与补偿", "negative"),
    ({"固件", "升级", "优化", "修复", "推送"}, "期待官方修复优化", "neutral"),
    ({"流畅", "好用", "满意", "散热好", "续航强"}, "体验满意支持", "positive"),
]

# 公众诉求意图
INTENT_RULES = [
    ({"退款"}, "退款诉求"),
    ({"换新", "换机", "更换"}, "换新诉求"),
    ({"召回"}, "召回诉求"),
    ({"道歉", "公开说明"}, "官方道歉诉求"),
    ({"补偿", "赔偿"}, "补偿诉求"),
    ({"整改", "改进", "优化"}, "整改优化诉求"),
    ({"澄清", "解释", "声明"}, "官方澄清诉求"),
]


def _match_rule(text: str, rules) -> str | None:
    best = None
    best_score = 0
    for words, label in rules:
        score = sum(1 for w in words if w in text)
        if score > best_score:
            best_score = score
            best = label
    return best


def cluster_opinions(posts: list, event_title: str = "") -> list[dict]:
    """将事件内的帖子聚类为核心观点。posts 为对象列表（含 content/sentiment）。"""
    groups = defaultdict(list)
    for p in posts:
        label = _match_rule(p.content, [(w, l) for w, l, _ in OPINION_RULES])
        if label is None:
            label = "其他讨论"
        groups[label].append(p)

    clusters = []
    for label, items in groups.items():
        sentiments = Counter(p.sentiment for p in items)
        dominant = sentiments.most_common(1)[0][0] if sentiments else "neutral"
        # 意图提炼
        intents = Counter()
        for p in items:
            intent = _match_rule(p.content, INTENT_RULES)
            if intent:
                intents[intent] += 1
        main_intent = intents.most_common(1)[0][0] if intents else "信息关注"
        # 代表性言论：选互动量最高的一条
        items_sorted = sorted(items, key=lambda p: p.like_count + p.comment_count * 2 + p.share_count * 3, reverse=True)
        representative = items_sorted[0].content[:120] if items_sorted else ""
        clusters.append({
            "label": label,
            "summary": f"共 {len(items)} 条相关言论，主要情绪为{dict(positive='正向', neutral='中性', negative='负向').get(dominant, '中性')}",
            "intent": main_intent,
            "count": len(items),
            "sentiment": dominant,
            "representative_text": representative,
        })
    # 按数量排序
    clusters.sort(key=lambda c: c["count"], reverse=True)
    return clusters


def deduplicate_posts(posts: list) -> list:
    """基于 SimHash 对帖子列表去重，返回去重后的帖子（标记 is_duplicate）。"""
    seen: dict[int, int] = {}  # fingerprint -> post index
    for p in posts:
        fp = compute_simhash(p.content)
        p.simhash = fp
        p.is_duplicate = False
        for existing_fp, _ in seen.items():
            if hamming_distance(fp, existing_fp) <= 3:
                p.is_duplicate = True
                break
        if not p.is_duplicate:
            seen[fp] = p.id
    return posts
