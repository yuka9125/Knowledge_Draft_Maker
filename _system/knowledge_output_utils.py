"""
ナレッジ候補出力の共通ロジック。
"""

from __future__ import annotations

import re
from typing import Any, Dict, List


def normalize_text_for_conflict(text: str) -> str:
    """矛盾判定用にテキストを正規化する。"""
    if text is None:
        return ""
    return re.sub(r"\s+", " ", str(text)).strip()


def build_existing_faq_diff_analysis(
    max_similarity: float | None,
    threshold: float,
    faq_checked: bool,
) -> str:
    """既存FAQとの差分分析結果を返す。"""
    if not faq_checked:
        return "既存FAQ照合未実施（FAQ未指定）"
    if max_similarity is None:
        return "既存FAQとの差分判定不可"
    if max_similarity >= threshold:
        return f"既存FAQ重複候補（最大類似度: {max_similarity:.3f}）"
    return f"既存FAQとの差分あり（最大類似度: {max_similarity:.3f}）"


def build_existing_faq_diff_reason(
    max_similarity: float | None,
    threshold: float,
    faq_checked: bool,
) -> str:
    """既存FAQ差分の短い理由を返す。"""
    if not faq_checked:
        return "FAQ未指定"
    if max_similarity is None:
        return "判定情報なし"
    if max_similarity >= threshold + 0.10:
        return "既存FAQとほぼ同一"
    if max_similarity >= threshold:
        return "既存FAQと類似度高"
    if max_similarity >= max(0.0, threshold - 0.10):
        return "回答内容に一部変更あり"
    return "回答内容に大きく変更あり"


def determine_risk_level(answer: str, category: str) -> str:
    """回答文とカテゴリからリスクレベルを判定する。"""
    target_text = f"{answer} {category}"
    critical_keywords = ["認証", "権限", "管理者"]
    high_keywords = ["人事", "給与", "セキュリティ", "パスワード", "個人情報"]

    if any(keyword in target_text for keyword in critical_keywords):
        return "critical"
    if any(keyword in target_text for keyword in high_keywords):
        return "high"
    return "low"


def build_review_reason(
    existing_faq_diff_reason: str,
    risk_level: str,
    confidence: float,
) -> str:
    """Excel向けのレビュー理由を生成する。"""
    if existing_faq_diff_reason in {"既存FAQとほぼ同一", "既存FAQと類似度高"}:
        return "既存FAQと重複する可能性があるため、既存記事との統合要否を確認してください。"
    if risk_level in {"critical", "high"}:
        return f"リスクレベルが{risk_level}のため、公開前レビューを推奨します。"
    if confidence < 0.7:
        return "信頼度が低めのため、内容確認を推奨します。"
    return "ドラフトの初稿です。公開前に内容確認してください。"


def build_source_logs(
    titles_by_index: Dict[Any, str], member_indices: List[Any]
) -> List[str]:
    """クラスタメンバーの件名一覧を生成（空欄時はidx補完）。"""
    source_logs: List[str] = []
    for member_idx in member_indices:
        title = str(titles_by_index.get(member_idx, "")).strip()
        source_logs.append(title if title else f"idx:{member_idx}")
    return source_logs
