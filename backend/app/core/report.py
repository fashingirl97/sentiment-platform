"""结构化舆情研判报告生成（Markdown）。"""
from datetime import datetime

from .nlp import RISK_LEVEL_TEXT


def _fmt_time(dt) -> str:
    """兼容 datetime 与已格式化字符串（如时间线节点时间）。"""
    if not dt:
        return "-"
    if isinstance(dt, str):
        return dt[:16]
    return dt.strftime("%Y-%m-%d %H:%M")


def build_event_report(event, posts: list, clusters: list, timeline: list,
                       dispositions: list, sources: list) -> str:
    """根据事件全周期研判数据组装 Markdown 报告。"""
    total = len(posts)
    neg = sum(1 for p in posts if p.sentiment == "negative")
    pos = sum(1 for p in posts if p.sentiment == "positive")
    neu = total - neg - pos
    neg_ratio = round(neg / total * 100, 1) if total else 0.0

    source_names = "、".join([s.name for s in sources]) if sources else "全网多源"
    time_span = "-"
    if posts:
        times = sorted(p.publish_time for p in posts)
        time_span = f"{_fmt_time(times[0])} 至 {_fmt_time(times[-1])}"

    lines = []
    lines.append(f"# 舆情事件研判报告\n")
    lines.append(f"> 生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    # 一、事件基本信息
    lines.append("## 一、事件基本信息\n")
    lines.append("| 项目 | 内容 |")
    lines.append("| --- | --- |")
    lines.append(f"| 事件主题 | {event.title} |")
    lines.append(f"| 事件性质 | {event.category} |")
    lines.append(f"| 监测周期 | {time_span} |")
    lines.append(f"| 覆盖信源 | {source_names} |")
    lines.append(f"| 全网总声量 | {total} 条 |")
    lines.append(f"| 负面率 | {neg_ratio}% |")
    lines.append("")

    # 二、传播态势分析
    lines.append("## 二、传播态势分析\n")
    lines.append(f"### 2.1 声量与情感分布\n")
    lines.append(f"- 正向：{pos} 条（{round(pos/total*100,1) if total else 0}%）")
    lines.append(f"- 中性：{neu} 条（{round(neu/total*100,1) if total else 0}%）")
    lines.append(f"- 负向：{neg} 条（{neg_ratio}%）\n")
    lines.append(f"### 2.2 传播关键节点\n")
    if timeline:
        for node in timeline:
            lines.append(f"- **{node['node_type']}**（{_fmt_time(node['time'])}）：{node['title']}")
    else:
        lines.append("- 暂无传播节点数据")
    lines.append("")

    # 三、舆论焦点与观点矩阵
    lines.append("## 三、舆论焦点与观点矩阵\n")
    if clusters:
        lines.append("| 观点 | 数量 | 情绪 | 公众诉求 | 代表性言论 |")
        lines.append("| --- | --- | --- | --- | --- |")
        for c in clusters:
            lines.append(
                f"| {c['label']} | {c['count']} | {c['sentiment']} | {c['intent']} | {c['representative_text'][:40]} |"
            )
    else:
        lines.append("- 暂无观点聚类数据")
    lines.append("")

    # 四、风险研判结论
    lines.append("## 四、风险研判结论\n")
    lines.append(f"- **综合风险等级**：{event.risk_level} 级（{RISK_LEVEL_TEXT.get(event.risk_level, event.risk_level)}）")
    lines.append(f"- **舆情烈度指数**：{event.heat_index}")
    lines.append(f"- **潜在影响**：{_impact_text(event.category, event.risk_level)}")
    lines.append("")

    # 五、应对与处置建议
    lines.append("## 五、应对与处置建议\n")
    if dispositions:
        for d in dispositions:
            lines.append(f"### 处置记录（{_fmt_time(d.created_at)} · {d.operator}）")
            lines.append(f"- 处置动作：{d.action}")
            if d.note:
                lines.append(f"- 备注：{d.note}")
            if d.draft_response:
                lines.append(f"\n{d.draft_response}\n")
    lines.append(f"### 后续监测重点")
    lines.append(f"1. 持续监测「{event.title}」相关声量与情感走势，关注是否出现二次发酵；")
    lines.append(f"2. 重点跟踪高危敏感词命中情况与高权重账号动态；")
    lines.append(f"3. 跟踪处置措施发布后的舆论反馈，评估应对效果。\n")

    return "\n".join(lines)


def _impact_text(category: str, risk_level: str) -> str:
    base = {
        "质量争议": "品牌声誉受损、产品口碑下滑、可能引发退货与销量下降",
        "服务纠纷": "客户满意度下降、投诉量上升、影响复购与口碑传播",
        "合规风险": "可能触发监管关注、行政处罚或法律诉讼",
    }.get(category, "品牌声誉与经营业务受到不同程度影响")
    if risk_level in ("S", "A"):
        base += "，存在舆情进一步扩大并冲击股价/经营的风险"
    return base
