# Copyright 2026 mytime.click
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import api, fields, models
from odoo.exceptions import ValidationError


class IrUiView(models.Model):
    _inherit = "ir.ui.view"

    geoengine_record_image_field_id = fields.Many2one(
        "ir.model.fields",
        string="Record Image Field",
        ondelete="set null",
        domain="[('model', '=', model), ('ttype', '=', 'binary')]",
        help="Image field (e.g. a logo) shown next to each record in the "
        "records panel of this geoengine view.",
    )

    @api.constrains("geoengine_record_image_field_id", "model")
    def _check_geoengine_record_image_field_id(self):
        for view in self:
            field = view.geoengine_record_image_field_id
            if field and field.model != view.model:
                message = self.env._(
                    "The record image field must be a field of the model %(model)s."
                )
                message = message % {"model": view.model}
                raise ValidationError(message)
