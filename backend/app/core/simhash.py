"""SimHash 指纹算法：识别高度重复内容与水军刷量信息。"""
import hashlib
import re

# 中文 + 英文 + 数字混合分词：提取连续片段作为 token
_TOKEN_RE = re.compile(r"[A-Za-z0-9\u4e00-\u9fff]+")


def tokenize(text: str) -> list[str]:
    """将文本切分为 token 序列。"""
    text = text or ""
    tokens = _TOKEN_RE.findall(text.lower())
    # 对较长的中文 token 再做 bigram 切分，增强召回
    result = []
    for tok in tokens:
        if len(tok) > 2 and re.fullmatch(r"[\u4e00-\u9fff]+", tok):
            result.extend(tok[i:i + 2] for i in range(len(tok) - 1))
        else:
            result.append(tok)
    return result


def _hash(token: str) -> int:
    """token -> 64 位无符号整数哈希。"""
    digest = hashlib.md5(token.encode("utf-8")).digest()[:8]
    return int.from_bytes(digest, "big", signed=False)


def compute_simhash(text: str) -> int:
    """计算 64 位 SimHash 指纹。"""
    tokens = tokenize(text)
    if not tokens:
        return 0
    vector = [0] * 64
    for tok in tokens:
        h = _hash(tok)
        for i in range(64):
            vector[i] += 1 if (h >> i) & 1 else -1
    fingerprint = 0
    for i in range(64):
        if vector[i] > 0:
            fingerprint |= 1 << i
    return fingerprint


def hamming_distance(a: int, b: int) -> int:
    """海明距离。"""
    return bin(a ^ b).count("1")


def is_similar(a: int, b: int, threshold: int = 3) -> bool:
    """判断两个指纹是否高度相似（海明距离 <= 阈值）。"""
    if a == 0 or b == 0:
        return False
    return hamming_distance(a, b) <= threshold


def simhash_hex(fp: int) -> str:
    return f"{fp:016x}"
