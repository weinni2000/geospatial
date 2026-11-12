# Copyright 2026 mytime.click
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Geospatial Advanced Features",
    "summary": "Extra drawing options for the vector layers of geoengine views, "
    "e.g. a color for features without value",
    "version": "20.0.1.0.0",
    "category": "GeoBI",
    "author": "mytime.click,Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "website": "https://github.com/OCA/geospatial",
    "depends": ["base_geoengine"],
    "data": [
        "views/geo_vector_layer_views.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "base_geoengine_advanced_features/static/src/js/*.esm.js",
        ],
    },
    "installable": True,
}
