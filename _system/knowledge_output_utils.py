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


def has_conflict_signal(candidate_answer: str, matched_faq_answer: str) -> bool:
    """回答同士に相反する運用の可能性を示す語があるか判定する。"""
    candidate = normalize_text_for_conflict(candidate_answer)
    faq = normalize_text_for_conflict(matched_faq_answer)
    conflict_pairs = [
        ("旧", "新"),
        ("古い", "最新"),
        ("古い", "新しい"),
        ("旧システム", "新システム"),
        ("廃止", "利用"),
        ("使用不可", "使用可能"),
        ("できません", "できます"),
        ("不要", "必要"),
    ]
    return any(
        (left in candidate and right in faq)
        or (right in candidate and left in faq)
        for left, right in conflict_pairs
    )


def classify_p32_result(
    max_similarity: float | None,
    candidate_answer: str,
    matched_faq_answer: str,
) -> str:
    """既存FAQ照合結果をP3-2確認ステータスへ分類する。"""
    if max_similarity is None:
        return "P3-2確認（既存FAQ更新候補）"

    if max_similarity >= 0.95:
        return "P3-2確認（既存FAQ完全一致）"
    if max_similarity >= 0.85:
        return "P3-2確認（既存FAQ類似）"
    if max_similarity >= 0.75:
        if has_conflict_signal(candidate_answer, matched_faq_answer):
            return "P3-2確認（既存FAQ矛盾可能性）"
        candidate = normalize_text_for_conflict(candidate_answer)
        faq = normalize_text_for_conflict(matched_faq_answer)
        if candidate and faq and candidate != faq:
            return "P3-2確認（既存FAQ更新候補）"
        return "P3-2確認（既存FAQ類似）"
    return "◯採用"


def build_recommended_action(final_result: str) -> str:
    """最終結果からSheet1向けの推奨アクションを返す。"""
    if final_result == "◯採用":
        return "新規FAQ作成"
    if final_result == "P3-2確認（既存FAQ完全一致）":
        return "既存FAQ維持"
    if final_result == "P3-2確認（既存FAQ類似）":
        return "既存FAQに統合"
    if final_result == "P3-2確認（既存FAQ更新候補）":
        return "既存FAQ更新"
    if final_result == "P3-2確認（既存FAQ矛盾可能性）":
        return "人間レビュー必須"
    if final_result == "FAQ対象外":
        return "FAQ対象外"
    return ""


def build_judgement_reason(final_result: str) -> str:
    """最終結果からSheet1向けの判定根拠を返す。"""
    reason_by_result = {
        "◯採用": "類似する既存FAQが見つからないため、新規FAQ候補として採用。",
        "P3-2確認（既存FAQ完全一致）": "既存FAQと質問・回答がほぼ一致しているため、既存FAQ維持候補として確認。",
        "P3-2確認（既存FAQ類似）": "既存FAQと同一テーマだが、表現や補足情報に差分があるため、統合候補として確認。",
        "P3-2確認（既存FAQ更新候補）": "既存FAQと同一テーマだが、回答内容に差分があるため、更新候補として確認。",
        "P3-2確認（既存FAQ矛盾可能性）": "既存FAQと新規候補で案内内容が異なるため、現行運用の確認が必要。",
    }
    return reason_by_result.get(final_result, "")


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
