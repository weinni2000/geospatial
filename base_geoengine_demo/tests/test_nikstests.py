# Copyright 2023 ACSONE SA/NV

import geojson
from shapely import wkt
from shapely.geometry import shape

from odoo.tests.common import TransactionCase

class TestCreateCreationOfEntity(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()


    def test_create_polygon_geojson_format(self):
        res = """
        <record model="geoengine.demo.automatic.retailing.machine" id="machine_1">
        <field name="name">1</field>
        <field name="total_sales">1057</field>
        <field name="money_level">low</field>
        <field name="the_point">POINT(746676.106813609 5865349.7175855)</field>
        <field name="state">ok</field>
    </record>"""

        model = self.env["geoengine.demo.automatic.retailing.machine"]
        model.create(
            {
                "name": "1",
                "total_sales": 1057,
                "money_level": "low",
                "the_point": geojson.loads(
                    '{"type": "Point", "coordinates": [746676.106813609, 5865349.7175855]}'
                ),
                "state": "ok",
            }
        )

        self.assertTrue(
            False
        )
