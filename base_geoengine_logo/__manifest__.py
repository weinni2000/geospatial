# Copyright 2026 mytime.click
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Geospatial Record Images",
    "summary": "Show an image (e.g. a logo) next to each record in the "
    "records panel of geoengine views",
    "version": "20.0.1.0.0",
    "category": "GeoBI",
    "author": "mytime.click,Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "website": "https://github.com/OCA/geospatial",
    "depends": ["base_geoengine"],
    "data": [
        "views/geo_vector_layer_views.xml",
        "views/ir_ui_view_views.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "base_geoengine_logo/static/src/js/*.esm.js",
            "base_geoengine_logo/static/src/xml/*.xml",
            "base_geoengine_logo/static/src/scss/*.scss",
        ],
    },
    "installable": True,
}
