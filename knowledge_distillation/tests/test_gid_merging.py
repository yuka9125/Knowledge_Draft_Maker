#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""GID統合ロジックの単体テスト。"""

import unittest
import contextlib
import io

import numpy as np
import pandas as pd

from knowledge_distillation.deduplication_system import Phase31Deduplicator
from knowledge_distillation.pre_deduplication import TextDeduplicator
from knowledge_distillation.verification_excel import GIDTracker, ProcessingRecord


class GidMergingTest(unittest.TestCase):
    """GID=0を含む統合が落ちないことを検証する。"""

    def test_phase2_merges_zero_gid_into_representative_gid(self):
        df = pd.DataFrame(
            [
                {
                    "質問": "VPNに接続できない場合は？",
                    "回答": "A",
                    "カテゴリ": "IT",
                },
                {
                    "質問": "VPNに接続できない場合は？",
                    "回答": "より長い採用回答です。",
                    "カテゴリ": "IT",
                },
            ],
            index=[0, 1],
        )
        records = {
            0: ProcessingRecord(original_idx=0, p0_gid=0, final_gid=0),
            1: ProcessingRecord(original_idx=1, p0_gid=1, final_gid=1),
        }
        tracker = GIDTracker()
        tracker.register(0)
        tracker.register(1)

        deduplicator = TextDeduplicator(similarity_threshold=0.9)
        with contextlib.redirect_stdout(io.StringIO()):
            deduplicator.find_duplicates(
                df=df,
                target_col="質問",
                sort_by_col="回答",
                phase_name="P2",
                question_col="質問",
                answer_col="回答",
                processing_records=records,
                gid_tracker=tracker,
                check_short_response=False,
            )

        self.assertEqual(tracker.get_final_gid(0), 1)
        self.assertEqual(records[0].final_gid, 1)
        self.assertEqual(records[1].final_gid, 1)

    def test_phase31_merges_zero_gid_into_representative_gid(self):
        df = pd.DataFrame(
            [
                {
                    "質問": "VPNに接続できない場合は？",
                    "回答": "A",
                    "カテゴリ": "IT",
                },
                {
                    "質問": "VPNに接続できない場合は？",
                    "回答": "より長い採用回答です。",
                    "カテゴリ": "IT",
                },
            ],
            index=[0, 1],
        )
        records = {
            0: ProcessingRecord(original_idx=0, p0_gid=0, final_gid=0),
            1: ProcessingRecord(original_idx=1, p0_gid=1, final_gid=1),
        }
        tracker = GIDTracker()
        tracker.register(0)
        tracker.register(1)

        deduplicator = Phase31Deduplicator(threshold=0.75)
        deduplicator.processing_records = records
        deduplicator.gid_tracker = tracker
        deduplicator.similarity_matrix = np.array([[0.0, 0.9], [0.9, 0.0]])
        deduplicator._create_groups(
            df=df,
            labels=np.array([1, 1]),
            question_col="質問",
            answer_col="回答",
            raw_overview_col="概要",
            raw_response_col="対応結果",
            category_col="カテゴリ",
            keywords_col="キーワード",
            link_names_col="リンク名",
        )
        tracker.update_all_records(records)

        self.assertEqual(tracker.get_final_gid(0), 1)
        self.assertEqual(records[0].final_gid, 1)
        self.assertEqual(records[1].final_gid, 1)

    def test_phase2_merges_same_category_and_link_name(self):
        df = pd.DataFrame(
            [
                {
                    "質問": "VPN接続時に認証エラーが出る場合はどうしますか",
                    "回答": "VPNクライアントを最新版に更新し、端末を再起動してください。",
                    "カテゴリ": "ITサポート",
                    "リンク名": "VPN更新手順",
                },
                {
                    "質問": "社外からファイル共有を開けない場合の対応は",
                    "回答": "VPN更新手順に沿ってクライアントを更新してから再接続してください。改善しない場合はITへ連絡してください。",
                    "カテゴリ": "ITサポート",
                    "リンク名": "VPN更新手順",
                },
            ],
            index=[0, 1],
        )
        records = {
            0: ProcessingRecord(original_idx=0, p0_gid=0, final_gid=0),
            1: ProcessingRecord(original_idx=1, p0_gid=1, final_gid=1),
        }
        tracker = GIDTracker()
        tracker.register(0)
        tracker.register(1)

        deduplicator = TextDeduplicator(similarity_threshold=0.99)
        with contextlib.redirect_stdout(io.StringIO()):
            groups = deduplicator.find_duplicates(
                df=df,
                target_col="質問",
                sort_by_col="回答",
                phase_name="P2",
                question_col="質問",
                answer_col="回答",
                category_col="カテゴリ",
                link_names_col="リンク名",
                processing_records=records,
                gid_tracker=tracker,
                check_short_response=False,
            )

        self.assertEqual(len(groups), 1)
        self.assertEqual(tracker.get_final_gid(0), 1)
        self.assertEqual(records[0].final_gid, 1)
        self.assertEqual(records[1].final_gid, 1)


if __name__ == "__main__":
    unittest.main()
