#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
approved_knowledge出力の単体テスト。
"""

import json
import tempfile
import unittest
from pathlib import Path

from openpyxl import Workbook

from approved_knowledge_exporter import (
    export_approved_knowledge_from_excel,
    load_approved_knowledge_from_excel,
)


class ApprovedKnowledgeExporterTest(unittest.TestCase):
    """レビュー済みExcelから採用行だけ出力することを検証。"""

    def _create_reviewed_excel(self) -> Path:
        tmp_dir = Path(tempfile.mkdtemp(prefix="approved_knowledge_test_"))
        xlsx_path = tmp_dir / "FAQ_final_result.xlsx"

        wb = Workbook()
        ws = wb.active
        ws.title = "最終ナレッジ候補一覧"
        ws.append(
            [
                "ナレッジID",
                "グループID",
                "候補_質問",
                "候補_回答",
                "カテゴリ",
                "統合件数",
                "既存FAQ_ID",
                "既存FAQ_質問",
                "既存FAQ_回答",
                "既存FAQ_比較",
                "リスクレベル",
                "信頼度",
                "推奨アクション",
                "判定根拠",
                "レビュー結果",
            ]
        )
        ws.append(
            [
                "k-001",
                1,
                "VPNにつながりません",
                "最新版VPNクライアントへ更新してください。",
                "IT",
                2,
                "",
                "",
                "",
                "既存FAQなし/未照合",
                "low",
                0.91,
                "新規FAQ作成",
                "信頼度理由: 0.91\nリスク理由: low",
                "採用",
            ]
        )
        ws.append(
            [
                "k-002",
                2,
                "未確認の質問",
                "未確認の回答",
                "IT",
                1,
                "",
                "",
                "",
                "既存FAQなし/未照合",
                "low",
                0.70,
                "新規FAQ作成",
                "",
                "未確認",
            ]
        )
        ws.append(
            [
                "k-003",
                3,
                "不採用の質問",
                "不採用の回答",
                "IT",
                1,
                "",
                "",
                "",
                "既存FAQなし/未照合",
                "low",
                0.70,
                "新規FAQ作成",
                "",
                "不採用",
            ]
        )
        wb.save(xlsx_path)
        return xlsx_path

    def test_load_only_approved_rows(self):
        """レビュー結果が採用の行だけ返す。"""
        xlsx_path = self._create_reviewed_excel()
        items = load_approved_knowledge_from_excel(
            xlsx_path,
            approved_at="2026-05-29T10:00:00+09:00",
        )

        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["knowledge_id"], "k-001")
        self.assertEqual(items[0]["question"], "VPNにつながりません")
        self.assertEqual(items[0]["answer"], "最新版VPNクライアントへ更新してください。")
        self.assertEqual(items[0]["category"], "IT")
        self.assertEqual(items[0]["approved_status"], "approved")
        self.assertEqual(items[0]["approved_at"], "2026-05-29T10:00:00+09:00")

    def test_export_approved_knowledge_json(self):
        """approved_knowledge.json の形式を検証。"""
        xlsx_path = self._create_reviewed_excel()
        output_path = xlsx_path.parent / "approved_knowledge.json"

        export_approved_knowledge_from_excel(
            xlsx_path,
            output_path,
            approved_at="2026-05-29T10:00:00+09:00",
        )

        with output_path.open(encoding="utf-8") as f:
            data = json.load(f)

        self.assertEqual(
            list(data[0].keys()),
            [
                "knowledge_id",
                "question",
                "answer",
                "category",
                "approved_status",
                "approved_at",
            ],
        )
        self.assertEqual(len(data), 1)


if __name__ == "__main__":
    unittest.main()
