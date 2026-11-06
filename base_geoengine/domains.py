# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo.fields import Domain
from odoo.orm.domains import OptimizationLevel, operator_optimization

from .expressions import GEO_OPERATORS, spatial_condition_sql


@operator_optimization(GEO_OPERATORS, level=OptimizationLevel.FULL)
def optimize_spatial_condition(condition, model):
    """Compile geo operators after core field and relational path validation."""
    field_expr, operator, value = (
        condition.field_expr,
        condition.operator,
        condition.value,
    )
    return Domain.custom(
        to_sql=lambda table: spatial_condition_sql(table, field_expr, operator, value)
    )
