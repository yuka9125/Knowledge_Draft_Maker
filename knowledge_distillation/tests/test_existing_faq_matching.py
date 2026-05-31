#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
既存FAQ照合（Phase 3-2）の補助ロジックのテスト。

質問＋回答を結合して照合する _combine_question_answer を検証する。
"""

import unittest

from knowledge_distillation.deduplication_system import _combine_question_answer


class CombineQuestionAnswerTest(unittest.TestCase):
    def test_combines_question_and_answer(self):
        self.assertEqual(
            _combine_question_answer("VPNに接続できません", "最新版へ更新してください"),
            "VPNに接続できません 最新版へ更新してください",
        )

    def test_question_only_when_answer_empty(self):
        self.assertEqual(_combine_question_answer("VPNの質問", ""), "VPNの質問")
        self.assertEqual(_combine_question_answer("VPNの質問", None), "VPNの質問")

    def test_dash_answer_is_treated_as_empty(self):
        # 回答が「-」（FAQ対象外）の場合は質問のみ
        self.assertEqual(_combine_question_answer("質問", "-"), "質問")

    def test_strips_whitespace(self):
        self.assertEqual(_combine_question_answer("  Q  ", "  A  "), "Q A")


if __name__ == "__main__":
    unittest.main()
