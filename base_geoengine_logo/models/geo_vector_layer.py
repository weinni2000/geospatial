# Copyright 2026 mytime.click
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models


class GeoVectorLayer(models.Model):
    _inherit = "geoengine.vector.layer"

    record_image_display = fields.Selection(
        [
            ("none", "None"),
            ("fill", "Background (tiled)"),
            ("center", "Centered"),
        ],
        string="Record Image on Polygons",
        default="none",
        required=True,
        help="Show the record image of the geoengine view (e.g. a logo) on the "
        "polygons of this layer: repeated as their background, or once in "
        "their middle.",
    )
    record_image_min_visible = fields.Integer(
        string="Minimum Visible Share (%)",
        default=70,
        help="Centered: the image is only drawn at a size where at least this "
        "share of it lies inside the polygon.",
    )
    record_image_min_size = fields.Integer(
        string="Minimum Image Height (px)",
        default=24,
        help="Centered: smaller images are not drawn; the image appears when "
        "zooming in.",
    )
    record_image_max_size = fields.Integer(
        string="Maximum Image Height (px)",
        default=96,
    )
