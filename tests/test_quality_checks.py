import unittest

import pandas as pd

from painel_dados.quality import assert_required_columns, assert_unique


class QualityChecksTest(unittest.TestCase):
    def test_required_columns_accepts_contract(self) -> None:
        frame = pd.DataFrame({"id_municipio": ["4205407"], "ano": [2024]})
        assert_required_columns(frame, ["id_municipio", "ano"])

    def test_required_columns_reports_schema_change(self) -> None:
        frame = pd.DataFrame({"ano": [2024]})
        with self.assertRaisesRegex(ValueError, "id_municipio"):
            assert_required_columns(frame, ["id_municipio", "ano"])

    def test_unique_rejects_duplicate_territorial_key(self) -> None:
        frame = pd.DataFrame(
            {
                "id_municipio": ["4205407", "4205407"],
                "ano": [2024, 2024],
            }
        )
        with self.assertRaisesRegex(ValueError, "Chave duplicada"):
            assert_unique(frame, ["id_municipio", "ano"])


if __name__ == "__main__":
    unittest.main()
