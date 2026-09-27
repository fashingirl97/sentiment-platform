"""实体抽取、关联图谱构建与传播溯源时间线。"""
from collections import Counter, defaultdict

# 内置实体词库（演示场景：消费电子品牌 / 产品 / 机构 / 人物）
BRAND_DICT = ["星耀", "蓝鲸", "云图", "极光", "NEX", "Vita", "曜石", "幻影", "锋尚"]
PRODUCT_DICT = ["X20", "X20 Pro", "Pro Max", "Note 12", "S 系列", "折叠屏", "旗舰机", "手机"]
ORG_DICT = ["市场监管局", "消费者协会", "消协", "品牌方", "客服中心", "质检总局", "售后部门"]
PERSON_DICT = ["老张测评", "数码阿峰", "科技大李", "极客小王", "退货小王子", "手机圈老王"]

# 产品名模式：品牌 + 型号
PRODUCT_PATTERNS = [f"{b}{m}" for b in BRAND_DICT for m in PRODUCT_DICT]


def extract_entities(text: str, author: str = "", author_type: str = "normal") -> list[tuple[str, str]]:
    """从文本中抽取 (实体名, 类型)。"""
    entities = []
    for brand in BRAND_DICT:
        if brand in text:
            entities.append((brand, "机构"))
    for prod in PRODUCT_PATTERNS:
        if prod in text:
            entities.append((prod, "产品"))
    # 通用产品词匹配
    for prod in PRODUCT_DICT:
        if prod in text:
            entities.append((prod, "产品"))
    for org in ORG_DICT:
        if org in text:
            entities.append((org, "机构"))
    for person in PERSON_DICT:
        if person in text or person == author:
            entities.append((person, "人物"))
    # KOL 作者视为人物实体
    if author_type == "kol" and author:
        entities.append((author, "人物"))
    # 去重
    seen = set()
    result = []
    for name, typ in entities:
        if name not in seen:
            seen.add(name)
            result.append((name, typ))
    return result


def build_graph(event_id: int, posts: list) -> tuple[list[dict], list[dict]]:
    """构建实体节点与关系边。"""
    node_counter = Counter()
    type_map = {}
    for p in posts:
        for name, typ in extract_entities(p.content, p.author, p.author_type):
            node_counter[name] += 1
            type_map[name] = typ

    nodes = [{"name": n, "type": type_map[n], "weight": c} for n, c in node_counter.items()]
    nodes.sort(key=lambda x: x["weight"], reverse=True)

    # 生成边：共现于同一条内容的实体对建立关系
    edge_counter = Counter()
    for p in posts:
        entities = [n for n, _ in extract_entities(p.content, p.author, p.author_type)]
        for i in range(len(entities)):
            for j in range(i + 1, len(entities)):
                a, b = sorted([entities[i], entities[j]])
                edge_counter[(a, b)] += 1

    edges = []
    for (a, b), w in edge_counter.items():
        edges.append({
            "source": a,
            "target": b,
            "relation": _relation_label(type_map.get(a, ""), type_map.get(b, "")),
            "weight": w,
        })
    return nodes, edges


def _relation_label(type_a: str, type_b: str) -> str:
    pair = {type_a, type_b}
    if pair == {"机构", "产品"}:
        return "发布"
    if pair == {"人物", "产品"}:
        return "评测"
    if pair == {"人物", "机构"}:
        return "声讨"
    if pair == {"产品", "产品"}:
        return "竞品"
    return "关联"


def _fmt(dt) -> str:
    """时间线节点时间格式化。"""
    return dt.strftime("%Y-%m-%d %H:%M") if dt else "-"


def build_timeline(event_id: int, posts: list) -> list[dict]:
    """构建传播溯源时间线：首发节点 + 引爆节点 + 扩散节点。"""
    if not posts:
        return []
    sorted_posts = sorted(posts, key=lambda p: p.publish_time)
    nodes = []

    # 首发节点
    first = sorted_posts[0]
    nodes.append({
        "node_type": "首发",
        "time": _fmt(first.publish_time),
        "title": f"首发信源：{first.platform} @{first.author}",
        "description": first.content[:100],
        "author": first.author,
        "platform": first.platform,
        "influence": first.like_count + first.comment_count + first.share_count,
        "post_id": first.id,
    })

    # 引爆节点：互动量突增（相对前序平均的显著提升）
    prev_avg = 0
    for i, p in enumerate(sorted_posts[1:], start=1):
        influence = p.like_count + p.comment_count + p.share_count
        if i >= 2 and influence >= prev_avg * 3 and influence > 200:
            nodes.append({
                "node_type": "引爆",
                "time": _fmt(p.publish_time),
                "title": f"引爆节点：{p.platform} @{p.author}（{p.author_type}）",
                "description": p.content[:100],
                "author": p.author,
                "platform": p.platform,
                "influence": influence,
                "post_id": p.id,
            })
            break
        prev_avg = (prev_avg * (i - 1) + influence) / i if i > 1 else influence

    # 关键扩散节点：KOL 或高互动内容（取 3 条）
    kol_posts = [p for p in sorted_posts if p.author_type == "kol" or (p.like_count + p.comment_count + p.share_count) > 300]
    kol_posts = kol_posts[:3]
    for p in kol_posts:
        nodes.append({
            "node_type": "扩散",
            "time": _fmt(p.publish_time),
            "title": f"关键扩散：{p.platform} @{p.author}",
            "description": p.content[:100],
            "author": p.author,
            "platform": p.platform,
            "influence": p.like_count + p.comment_count + p.share_count,
            "post_id": p.id,
        })

    nodes.sort(key=lambda n: n["time"])
    return nodes
