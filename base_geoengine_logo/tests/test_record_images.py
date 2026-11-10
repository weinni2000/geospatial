# Copyright 2026 mytime.click
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.exceptions import ValidationError
from odoo.tests import TransactionCase

# 1x1 PNG
PNG = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8"
    "AAAAASUVORK5CYII="
)


class TestRecordImages(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.view = cls.env["ir.ui.view"].create(
            {
                "name": "res.partner.geoengine.test",
                "model": "res.partner",
                "arch": '<geoengine><field name="name"/></geoengine>',
            }
        )
        cls.image_field = cls.env["ir.model.fields"]._get("res.partner", "image_128")
        cls.partner_with_image = cls.env["res.partner"].create(
            {"name": "With image", "image_1920": PNG}
        )
        cls.partner_without_image = cls.env["res.partner"].create(
            {"name": "Without image"}
        )
        cls.partner_ids = (cls.partner_with_image | cls.partner_without_image).ids

    def test_no_image_field(self):
        result = self.env["res.partner"].get_geoengine_record_images(
            self.view.id, self.partner_ids
        )
        self.assertEqual(result, {"field": False, "record_ids": []})

    def test_image_field(self):
        self.view.geoengine_record_image_field_id = self.image_field
        result = self.env["res.partner"].get_geoengine_record_images(
            self.view.id, self.partner_ids
        )
        self.assertEqual(result["field"], "image_128")
        self.assertEqual(result["record_ids"], [self.partner_with_image.id])

    def test_field_of_other_model(self):
        other_field = self.env["ir.model.fields"]._get("res.users", "image_128")
        with self.assertRaises(ValidationError):
            self.view.geoengine_record_image_field_id = other_field

    def test_layer_record_image_display(self):
        layer = self.env["geoengine.vector.layer"].new({"name": "Test layer"})
        self.assertEqual(layer.record_image_display, "none")
        self.assertEqual(layer.record_image_min_visible, 70)
        self.assertEqual(layer.record_image_min_size, 24)
        self.assertEqual(layer.record_image_max_size, 96)
