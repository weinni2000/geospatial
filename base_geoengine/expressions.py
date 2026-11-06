# Copyright 2023 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
# Odoo 20 port: compile spatial domains with TableSQL and parameterized SQL.
from uuid import uuid4

from odoo.fields import Domain
from odoo.orm.query import Query
from odoo.tools import SQL

from .fields import GeoField

GEO_OPERATORS = {
    "geo_greater": SQL(">"),
    "geo_lesser": SQL("<"),
    "geo_equal": SQL("="),
    "geo_touch": SQL("ST_Touches"),
    "geo_within": SQL("ST_Within"),
    "geo_contains": SQL("ST_Contains"),
    "geo_intersect": SQL("ST_Intersects"),
}


def where_calc(model, domain, active_test=True, alias=None):
    """Build an aliased related query while preserving Odoo 20 access restrictions."""
    domain = Domain(domain)
    if (
        model._active_name
        and active_test
        and model.env.context.get("active_test", True)
        and not any(
            c.field_expr == model._active_name for c in domain.iter_conditions()
        )
    ):
        domain &= Domain(model._active_name, "=", True)
    security = Domain.TRUE if model.env.su else model._access_domain("read")
    if security.is_false():
        model.browse().check_access("read")
    domain = domain.optimize_full(model)
    query = Query(model, alias=alias)
    query.add_where(domain._to_sql(query.table))
    if not security.is_true():
        model_sudo = model.sudo().with_context(active_test=False)
        query.add_where(
            security.optimize_full(model_sudo, search_domain=domain)._to_sql(
                query.table._with_model(model_sudo)
            )
        )
    return query


def spatial_condition_sql(table, field_expr, operator, value):
    model = table._model
    field = model._fields[field_expr]
    if not isinstance(field, GeoField):
        # Invalid domain operands follow the ORM's ValueError convention.
        raise ValueError(f"{field_expr} is not a spatial field")  # noqa: TRY004
    model.check_field_access(field, "read")
    left = table[field_expr]
    sql_operator = GEO_OPERATORS[operator]

    def compare(right):
        if operator in ("geo_greater", "geo_lesser"):
            return SQL("ST_Area(%s) %s ST_Area(%s)", left, sql_operator, right)
        if operator == "geo_equal":
            return SQL("%s = %s", left, right)
        return SQL("%s(%s, %s)", sql_operator, left, right)

    if isinstance(value, dict):
        if not value:
            raise ValueError(
                f"Missing geo reference for {field_expr!r}: expected "
                f"{{'<model>.<geo field>': <domain>}}"
            )
        conditions = []
        for key, domain in value.items():
            related_name, _, related_field = (
                key.rpartition(".") if isinstance(key, str) else ("", "", "")
            )
            if related_name not in model.env or not isinstance(
                model.env[related_name]._fields.get(related_field), GeoField
            ):
                raise ValueError(
                    f"Invalid geo reference {key!r}: expected '<model>.<geo field>'"
                )
            related = model.env[related_name]
            related.check_field_access(related._fields[related_field], "read")
            query = where_calc(related, domain, alias="geo_" + uuid4().hex)
            query.add_where(compare(query.table[related_field]))
            conditions.append(SQL("EXISTS(%s)", query.subselect(SQL("1"))))
        return SQL(" AND ").join(conditions)
    if operator in ("geo_greater", "geo_lesser") and isinstance(value, int | float):
        return SQL("ST_Area(%s) %s %s", left, sql_operator, value)
    shape = field.entry_to_shape(value, same_type=False)
    return compare(SQL("ST_GeomFromText(%s, %s)", shape.wkt, field.srid))
