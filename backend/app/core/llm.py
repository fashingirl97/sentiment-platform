"""大语言模型接口（预留）+ 规则引擎兜底。

优先调用外部大模型（通过环境变量配置），未配置密钥时自动降级为
规则/模板生成，保证完全离线可运行、效果可控。
"""
import logging
import os
from pathlib import Path

import httpx
from dotenv import load_dotenv

from .nlp import RISK_LEVEL_TEXT

logger = logging.getLogger("llm")

# 加载 backend/.env 中的密钥配置（override=True：项目 .env 优先于系统环境变量，
# 避免机器上残留的全局 LLM_API_KEY 覆盖本项目配置）
load_dotenv(Path(__file__).resolve().parents[2] / ".env", override=True)

LLM_API_KEY = os.getenv("LLM_API_KEY", "")
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://api.openai-proxy.org/v1")
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-5.4-mini")


def llm_available() -> bool:
    return bool(LLM_API_KEY)


def call_llm(prompt: str) -> str | None:
    """调用大模型生成文本；失败或未配置返回 None（走兜底）。"""
    if not LLM_API_KEY:
        return None
    try:
        resp = httpx.post(
            f"{LLM_BASE_URL}/chat/completions",
            headers={"Authorization": f"Bearer {LLM_API_KEY}"},
            json={
                "model": LLM_MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.6,
            },
            timeout=30,
            trust_env=False,  # 忽略系统代理环境变量（HTTP_PROXY/ALL_PROXY 等），直连 LLM 服务
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]
    except Exception as e:
        logger.warning("LLM 调用失败，降级为规则引擎：%s", e)
        return None


# ---------- 规则兜底：公关回应话术 ----------

def generate_response_draft(event_title: str, category: str, risk_level: str,
                            main_emotion: str, main_intent: str) -> str:
    """生成公关回应话术草案（事实澄清 + 情绪疏导 + 行动方案）。"""
    prompt = (
        f"你是企业公关负责人，针对舆情事件「{event_title}」"
        f"（性质：{category}，风险等级：{RISK_LEVEL_TEXT.get(risk_level, risk_level)}，"
        f"公众主要情绪：{main_emotion}，核心诉求：{main_intent}），"
        f"请生成包含「事实澄清」「情绪疏导」「行动方案」三部分的中文官方回应口径。"
    )
    llm_out = call_llm(prompt)
    if llm_out:
        return llm_out

    # 规则兜底模板
    emotion_text = {"愤怒": "失望与不满", "恐慌": "担忧与不安", "质疑": "关注与疑虑", "失望": "失望情绪"}.get(main_emotion, "关注")
    intent_action = {
        "退款诉求": "对符合退货退款条件的用户开通绿色通道，承诺 48 小时内完成退款处理",
        "换新诉求": "对确属质量问题的设备提供免费换新或维修服务",
        "召回诉求": "组织专业团队评估是否需要启动产品召回程序",
        "补偿诉求": "制定合理的补偿方案并及时向社会公布",
        "整改优化诉求": "成立专项整改小组，明确整改时间表并定期公示进展",
        "官方澄清诉求": "48 小时内发布官方声明，澄清事实与后续处理措施",
        "信息关注": "持续关注事件进展并保持信息公开透明",
    }.get(main_intent, "持续关注并公开处理进展")

    return f"""## 事实澄清

针对近期网络平台反映的「{event_title}」相关情况，我司高度重视，已第一时间成立专项工作组开展内部核查。目前相关产品的质量检测与售后数据正在紧急复盘核实中，我们将在事实查明后及时向公众公布权威结论，不回避、不隐瞒。

## 情绪疏导

我们充分理解广大用户对产品质量的{emotion_text}。对于给用户带来的困扰与不便，我们深表歉意。用户的信任是我们最宝贵的资产，我们承诺以负责任的态度直面问题，认真倾听每一位用户的反馈。

## 行动方案

1. {intent_action}；
2. 开通 7×24 小时专属客服通道与在线反馈专区，安排专人跟进；
3. 对涉及的质量问题进行技术溯源，若确认存在缺陷将第一时间公布原因与解决方案；
4. 定期通过官方渠道通报处理进展，接受媒体与公众监督。"""


def generate_strategy_suggestion(event_title: str, category: str, risk_level: str, main_intent: str) -> str:
    """生成处置策略建议。"""
    prompt = f"针对舆情事件「{event_title}」（性质：{category}，风险：{risk_level}，诉求：{main_intent}），给出 3~5 条公关应对策略建议。"
    llm_out = call_llm(prompt)
    if llm_out:
        return llm_out
    return f"""1. 快速响应：在事件发酵初期（4 小时内）发布首条官方声明，抢占话语权；
2. 事实核查：同步开展内部质量核查，用客观检测数据回应质疑；
3. 用户安抚：对受影响的用户主动联系，提供补偿/换新/退款等解决方案；
4. 意见领袖沟通：与关键 KOL 建立沟通渠道，推动客观测评发声；
5. 长效整改：公布产品改进与售后优化计划，修复品牌信任。"""
