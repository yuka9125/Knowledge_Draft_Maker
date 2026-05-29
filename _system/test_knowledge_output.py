#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ナレッジ候補出力の単体テスト。
"""

import unittest

from knowledge_output_utils import (
    build_existing_faq_diff_analysis,
    build_review_reason,
    build_source_logs,
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


if __name__ == "__main__":
    unittest.main()
