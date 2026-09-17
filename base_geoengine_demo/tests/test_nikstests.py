# Copyright 2023 ACSONE SA/NV

import geojson

from odoo.tests.common import TransactionCase


class TestCreateCreationOfEntity(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

    def test_create_polygon_geojson_format(self):
        model = self.env["geoengine.demo.automatic.retailing.machine"]
        model.create(
            {
                "name": "1",
                "total_sales": 1057,
                "money_level": "low",
                "the_point": geojson.loads(
                    '{"type": "Point", "coordinates": '
                    "[746676.106813609, 5865349.7175855]}"
                ),
                "state": "ok",
            }
        )

        self.assertTrue(False)
