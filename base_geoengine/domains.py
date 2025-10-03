from odoo.fields import Domain, Field
from odoo.orm import domains
from odoo.orm.domains import DomainCondition, NEGATIVE_CONDITION_OPERATORS, Query, SQL, STANDARD_CONDITION_OPERATORS,CONDITION_OPERATORS
from odoo.orm.identifiers import NewId
from odoo import fields
from odoo.orm.models import BaseModel
import logging
import warnings
import typing

if typing.TYPE_CHECKING:
    from collections.abc import Callable, Collection, Iterable
    from .fields import Field
    from .models import BaseModel

    M = typing.TypeVar('M', bound=BaseModel)

_logger = logging.getLogger(__name__)

GEO_OPERATORS = frozenset([
    "geo_greater", ">",
    "geo_lesser", "<",
    "geo_equal", "=",
    "geo_touch", "ST_Touches",
    "geo_within", "ST_Within",
    "geo_contains", "ST_Contains",
    "geo_intersect", "ST_Intersects",
])

def checked(self) -> DomainCondition:
    """Validate `self` and return it if correct, otherwise raise an exception."""
    if not isinstance(self.field_expr, str) or not self.field_expr:
        self._raise("Empty field name", error=TypeError)
    operator = self.operator.lower()
    if operator != self.operator:
        warnings.warn(f"Deprecated since 19.0, the domain condition {(self.field_expr, self.operator, self.value)!r} should have a lower-case operator", DeprecationWarning)
        return DomainCondition(self.field_expr, operator, self.value).checked()
    if operator not in CONDITION_OPERATORS:

        # MOD
        if operator not in GEO_OPERATORS:
            self._raise("Invalid operator")
            # /MOD
        
    # check already the consistency for domain manipulation
    # these are common mistakes and optimizations, do them here to avoid recreating the domain
    # - NewId is not a value
    # - records are not accepted, use values
    # - Query and Domain values should be using a relational operator
    value = self.value
    if value is None:
        value = False
    elif isinstance(value, NewId):
        _logger.warning("Domains don't support NewId, use .ids instead, for %r", (self.field_expr, self.operator, self.value))
        operator = 'not in' if operator in NEGATIVE_CONDITION_OPERATORS else 'in'
        value = []
    elif isinstance(value, BaseModel):
        _logger.warning("The domain condition %r should not have a value which is a model", (self.field_expr, self.operator, self.value))
        value = value.ids
    elif isinstance(value, (Domain, Query, SQL)) and operator not in ('any', 'not any', 'any!', 'not any!', 'in', 'not in'):
        # accept SQL object in the right part for simple operators
        # use case: compare 2 fields
        _logger.warning("The domain condition %r should use the 'any' or 'not any' operator.", (self.field_expr, self.operator, self.value))
    if value is not self.value:
        return DomainCondition(self.field_expr, operator, value)
    return self

DomainCondition.checked = checked

# merge 2 frozen sets Domain.STANDARD_CONDITION_OPERATORS and GEO_OPERATORS
#domains.CONDITION_OPERATORS = domains.CONDITION_OPERATORS.union(GEO_OPERATORS)
print("test")
