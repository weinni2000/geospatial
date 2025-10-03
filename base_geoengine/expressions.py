# Copyright 2023 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


# from odoo.osv.Domain import TERM_OPERATORS


# original___condition_to_sql = BaseModel._condition_to_sql

"""
GEO_OPERATORS = {
    "geo_greater": ">",
    "geo_lesser": "<",
    "geo_equal": "=",
    "geo_touch": "ST_Touches",
    "geo_within": "ST_Within",
    "geo_contains": "ST_Contains",
    "geo_intersect": "ST_Intersects",
}
GEO_SQL_OPERATORS = {
    "geo_greater": SQL(">"),
    "geo_lesser": SQL("<"),
    "geo_equal": SQL("="),
    "geo_touch": SQL("ST_Touches"),
    "geo_within": SQL("ST_Within"),
    "geo_contains": SQL("ST_Contains"),
    "geo_intersect": SQL("ST_Intersects"),
}
TERM_OPERATORS = [] # TERM_OPERATORS in expressions don't exits anymore
term_operators_list = list(TERM_OPERATORS)
for op in GEO_OPERATORS:
    term_operators_list.append(op)

#Domain.TERM_OPERATORS = tuple(term_operators_list)
#Domain.SQL_OPERATORS.update(GEO_SQL_OPERATORS)


#depricated
def _condition_to_sql(
    self, alias: str, fname: str, operator: str, value, query: Query
) -> SQL:
    if operator in GEO_OPERATORS.keys():
        current_field = self._fields.get(fname)
        current_operator = GeoOperator(current_field)
        if current_field and isinstance(current_field, GeoField):
            params = []
            if isinstance(value, dict):
                # We are having indirect geo_operator like (‘geom’, ‘geo_...’,
                # {‘res.zip.poly’: [‘id’, ‘in’, [1,2,3]] })
                ref_search = value
                sub_queries = []
                for key in ref_search:
                    i = key.rfind(".")
                    rel_model = key[0:i]
                    rel_col = key[i + 1 :]
                    rel_model = self.env[rel_model]
                    # we compute the attributes search on spatial rel
                    if ref_search[key]:
                        rel_alias = (
                            rel_model._table
                            + "_"
                            + "".join(random.choices(string.ascii_lowercase, k=5))
                        )
                        rel_query = where_calc(
                            rel_model,
                            ref_search[key],
                            active_test=True,
                            alias=rel_alias,
                        )
                        self._apply_ir_rules(rel_query, "read")
                        if operator == "geo_equal":
                            rel_query.add_where(
                                f'"{alias}"."{fname}" {GEO_OPERATORS[operator]} '
                                f"{rel_alias}.{rel_col}"
                            )
                        elif operator in ("geo_greater", "geo_lesser"):
                            rel_query.add_where(
                                f"ST_Area({alias}.{fname}) {GEO_OPERATORS[operator]} "
                                f"ST_Area({rel_alias}.{rel_col})"
                            )
                        else:
                            rel_query.add_where(
                                f'{GEO_OPERATORS[operator]}("{alias}"."{fname}", '
                                f"{rel_alias}.{rel_col})"
                            )

                        subquery, subparams = rel_query.subselect("1")
                        sub_query_mogrified = (
                            self.env.cr.mogrify(subquery, subparams)
                            .decode("utf-8")
                            .replace(f"'{rel_model._table}'", f'"{rel_model._table}"')
                            .replace("%", "%%")
                        )
                        sub_queries.append(f"EXISTS({sub_query_mogrified})")
                query = " AND ".join(sub_queries)
            else:
                query = get_geo_func(
                    current_operator, operator, fname, value, params, self._table
                )
            return SQL(query, *params)
    return original___condition_to_sql(
        self, alias=alias, fname=fname, operator=operator, value=value, query=query
    )
"""
