from odoo.fields import Domain
from odoo.orm import domains
from odoo import fields

GEO_OPERATORS = frozenset([
    "geo_greater", ">",
    "geo_lesser", "<",
    "geo_equal", "=",
    "geo_touch", "ST_Touches",
    "geo_within", "ST_Within",
    "geo_contains", "ST_Contains",
    "geo_intersect", "ST_Intersects",
])

# merge 2 frozen sets Domain.STANDARD_CONDITION_OPERATORS and GEO_OPERATORS
#domains.CONDITION_OPERATORS = domains.CONDITION_OPERATORS.union(GEO_OPERATORS)
print("test")
