#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ナレッジ候補出力の単体テスト。
"""

import unittest

from knowledge_output_utils import (
    build_existing_faq_comparison_label,
    build_judgement_reason,
    build_existing_faq_diff_analysis,
    build_recommended_action,
    build_review_reason,
    build_source_logs,
    classify_p32_result,
    determine_risk_level,
)


class KnowledgeOutputLogicTest(unittest.TestCase):
    """ナレッジ候補の判定ロジック検証。"""

    def test_risk_level_priority(self):
        """critical > high > low の優先順位を検証。"""
        self.assertEqual(
            determine_risk_level("管理者権限を付与してください", "パスワード管理"),
            "critical",
        )
        self.assertEqual(
            determine_risk_level("給与明細の確認方法", "人事"),
            "high",
        )
        self.assertEqual(
            determine_risk_level("プリンタ設定の方法", "周辺機器"),
            "low",
        )

    def test_existing_faq_diff_analysis(self):
        """既存FAQ差分分析判定を検証。"""
        self.assertEqual(
            build_existing_faq_diff_analysis(0.71, 0.75, True),
            "既存FAQとの差分あり（最大類似度: 0.710）",
        )
        self.assertEqual(
            build_existing_faq_diff_analysis(0.92, 0.75, True),
            "既存FAQ重複候補（最大類似度: 0.920）",
        )
        self.assertEqual(
            build_existing_faq_diff_analysis(None, 0.75, False),
            "既存FAQ照合未実施（FAQ未指定）",
        )

    def test_source_logs_fallback(self):
        """件名が空のときにidx補完されることを検証。"""
        titles_by_index = {
            10: "INC0001: VPN接続不可",
            11: "",
        }
        logs = build_source_logs(titles_by_index, [10, 11])
        self.assertEqual(logs, ["INC0001: VPN接続不可", "idx:11"])

    def test_review_reason(self):
        """レビュー理由生成を検証。"""
        self.assertIn(
            "重複",
            build_review_reason("既存FAQと類似度高", "low", 0.9),
        )
        self.assertIn(
            "critical",
            build_review_reason("none", "critical", 0.9),
        )

    def test_p32_classification(self):
        """P3-2確認ステータスの類似度しきい値を検証。"""
        self.assertEqual(
            classify_p32_result(0.96, "同じ回答", "同じ回答"),
            "P3-2確認（既存FAQ完全一致）",
        )
        self.assertEqual(
            classify_p32_result(0.88, "候補回答", "既存FAQ回答"),
            "P3-2確認（既存FAQ類似）",
        )
        self.assertEqual(
            classify_p32_result(0.76, "新しい手順です", "古い手順です"),
            "P3-2確認（既存FAQ矛盾可能性）",
        )
        self.assertEqual(
            classify_p32_result(0.76, "申請先が変わりました", "旧申請先です"),
            "P3-2確認（既存FAQ更新候補）",
        )

    def test_recommended_action_and_judgement_reason(self):
        """推奨アクションと判定根拠を検証。"""
        self.assertEqual(build_recommended_action("◯採用"), "新規FAQ作成")
        self.assertEqual(
            build_recommended_action("P3-2確認（既存FAQ完全一致）"),
            "既存FAQ維持",
        )
        self.assertEqual(
            build_recommended_action("P3-2確認（既存FAQ類似）"),
            "既存FAQに統合",
        )
        self.assertEqual(
            build_recommended_action("P3-2確認（既存FAQ更新候補）"),
            "既存FAQ更新",
        )
        self.assertEqual(
            build_recommended_action("P3-2確認（既存FAQ矛盾可能性）"),
            "人間レビュー必須",
        )
        reason = build_judgement_reason(
            confidence=0.91,
            similar_logs_count=2,
            faq_comparison="既存FAQと内容が一部異なる",
            answer="最新版VPNクライアントへ更新してください。手順に沿って再接続してください。",
            category="IT",
            risk_level="low",
            final_result="P3-2確認（既存FAQ更新候補）",
        )
        self.assertIn(
            "信頼度理由: 信頼度0.91",
            reason,
        )
        self.assertIn(
            "元ログ2件",
            reason,
        )
        self.assertIn(
            "既存FAQと内容が一部異なる",
            reason,
        )
        self.assertIn(
            "リスク理由: リスクレベルlow",
            reason,
        )

    def test_existing_faq_comparison_label(self):
        """既存FAQ比較は数値ではなく説明文で返す。"""
        self.assertEqual(
            build_existing_faq_comparison_label(0.96, True),
            "既存FAQと内容が近い",
        )
        self.assertEqual(
            build_existing_faq_comparison_label(0.88, True),
            "既存FAQと内容が近い（一部差分あり）",
        )
        self.assertEqual(
            build_existing_faq_comparison_label(0.76, True),
            "既存FAQと内容が一部異なる",
        )
        self.assertEqual(
            build_existing_faq_comparison_label(0.70, True),
            "既存FAQと内容が異なる",
        )
        self.assertEqual(
            build_existing_faq_comparison_label(None, False),
            "既存FAQなし/未照合",
        )


if __name__ == "__main__":
    unittest.main()
