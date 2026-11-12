# Copyright 2026 mytime.click
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.exceptions import ValidationError
from odoo.tests import TransactionCase


class TestEmptyValueColor(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.layer_model = cls.env["geoengine.vector.layer"]

    def test_hex_color_accepted(self):
        layer = self.layer_model.new({"empty_value_color": "#FF0000"})
        layer._check_empty_value_color()

    def test_invalid_color_rejected(self):
        for color in ("red", "#F00", "FF0000", "#GG0000"):
            layer = self.layer_model.new({"empty_value_color": color})
            with self.subTest(color=color), self.assertRaises(ValidationError):
                layer._check_empty_value_color()
