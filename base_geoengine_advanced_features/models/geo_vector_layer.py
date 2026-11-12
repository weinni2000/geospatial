# Copyright 2026 mytime.click
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import re

from odoo import api, fields, models
from odoo.exceptions import ValidationError

HEX_COLOR_RE = re.compile(r"^#[0-9a-fA-F]{6}$")


class GeoVectorLayer(models.Model):
    _inherit = "geoengine.vector.layer"

    proportion_colored = fields.Boolean(
        string="Colored Proportional Symbols",
        help="Proportional symbols: color the symbols by their value too, with "
        "the classification, end color and number of classes of the layer, "
        "like a colored range layer. Without it all symbols get the begin color.",
    )
    empty_value_color = fields.Char(
        string="Color for 0 / Empty Values",
        help="Proportional symbols and colored ranges: features whose attribute "
        "value is 0 or empty are drawn in this color (e.g. #FF0000) instead of "
        "the color of their class. Leave empty to draw them like any other value.",
    )

    @api.constrains("empty_value_color")
    def _check_empty_value_color(self):
        for rec in self:
            if rec.empty_value_color and not HEX_COLOR_RE.match(rec.empty_value_color):
                raise ValidationError(
                    self.env._(
                        "The Color for 0 / Empty Values must be a hex color, "
                        "e.g. #FF0000."
                    )
                )
