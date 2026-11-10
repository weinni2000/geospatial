# Copyright 2026 mytime.click
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import api, models


class Base(models.AbstractModel):
    _inherit = "base"

    @api.model
    def get_geoengine_record_images(self, view_id=None, record_ids=None):
        """Image field of a geoengine view and the records that have an image.

        :param view_id: id of the geoengine view (default: the model's
            default geoengine view)
        :param record_ids: ids of the records shown in the records panel
        :return: {"field": field name or False, "record_ids": [ids with image]}
        """
        if view_id:
            view = self.env["ir.ui.view"].browse(view_id)
        else:
            view = self._get_geo_view()
        field = view.sudo().geoengine_record_image_field_id
        if not field or field.model != self._name or field.name not in self._fields:
            return {"field": False, "record_ids": []}
        records = self.browse(record_ids or []).exists()
        rows = records.with_context(bin_size=True).read([field.name])
        return {
            "field": field.name,
            "record_ids": [row["id"] for row in rows if row[field.name]],
        }
