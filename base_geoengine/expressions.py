# Copyright 2023 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import collections
import collections.abc
import json
import logging
import random
import reprlib
import string
import traceback
from datetime import date, datetime, time

import pytz

from odoo.models import READ_GROUP_NUMBER_GRANULARITY, check_property_field_value_name
from odoo.osv import expression
from odoo.osv.expression import (
    AND,
    AND_OPERATOR,
    ANY_IN,
    FALSE_LEAF,
    NEGATIVE_TERM_OPERATORS,
    NOT_OPERATOR,
    OR,
    SQL_OPERATORS,
    TERM_OPERATORS,
    TERM_OPERATORS_NEGATION,
    TRUE_LEAF,
    WILDCARD_OPERATORS,
    check_leaf,
    domain_combine_anies,
    is_operator,
    normalize_leaf,
)
from odoo.tools import SQL, Query, get_lang
from odoo.tools.sql import (
    pattern_to_translated_trigram_pattern,
    value_to_translated_trigram_pattern,
)

from .fields import GeoField
from .geo_operators import GeoOperator

_logger = logging.getLogger(__name__)

GEO_OPERATORS = {
    "geo_greater": ">",
    "geo_lesser": "<",
    "geo_equal": "=",
    "geo_touch": "ST_Touches",
    "geo_within": "ST_Within",
    "geo_contains": "ST_Contains",
    "geo_intersect": "ST_Intersects",
}
term_operators_list = list(TERM_OPERATORS)
for op in GEO_OPERATORS:
    term_operators_list.append(op)

expression.TERM_OPERATORS = tuple(term_operators_list)
TERM_OPERATORS = expression.TERM_OPERATORS

GEO_SQL_OPERATORS = {
    "geo_greater": SQL(">"),
    "geo_lesser": SQL("<"),
    "geo_equal": SQL("="),
    "geo_touch": SQL("ST_Touches"),
    "geo_within": SQL("ST_Within"),
    "geo_contains": SQL("ST_Contains"),
    "geo_intersect": SQL("ST_Intersects"),
}

expression.SQL_OPERATORS.update(GEO_SQL_OPERATORS)


def __leaf_to_sql(leaf, model, alias):  # noqa: C901
    # This method has been monkey patched in order to be able to include
    # geo_operators into the Odoo search method.
    left, operator, right = leaf
    if isinstance(leaf, list | tuple):
        current_field = model._fields.get(left)
        current_operator = GeoOperator(current_field)
        if current_field and isinstance(current_field, GeoField):
            params = []
            if isinstance(right, dict):
                # We are having indirect geo_operator like (‘geom’, ‘geo_...’,
                # {‘res.zip.poly’: [‘id’, ‘in’, [1,2,3]] })
                ref_search = right
                sub_queries = []
                for key in ref_search:
                    i = key.rfind(".")
                    rel_model = key[0:i]
                    rel_col = key[i + 1 :]
                    rel_model = model.env[rel_model]
                    # we compute the attributes search on spatial rel
                    if ref_search[key]:
                        rel_alias = rel_model._table + "_" + "".join(random.choices(string.ascii_lowercase, k=5))

                        rel_query = where_calc(
                            rel_model,
                            ref_search[key],
                            active_test=True,
                            alias=rel_alias,
                        )
                        model._apply_ir_rules(rel_query, "read")
                        if operator == "geo_equal":
                            rel_query.add_where(
                                f'"{alias}"."{left}" {GEO_OPERATORS[operator]} ' f"{rel_alias}.{rel_col}"
                            )
                        elif operator in ("geo_greater", "geo_lesser"):
                            rel_query.add_where(
                                f"ST_Area({alias}.{left}) {GEO_OPERATORS[operator]} "
                                f"ST_Area({rel_alias}.{rel_col})"
                            )
                        else:
                            rel_query.add_where(
                                f'{GEO_OPERATORS[operator]}("{alias}"."{left}", ' f"{rel_alias}.{rel_col})"
                            )

                        subquery, subparams = rel_query.subselect("1")
                        sub_queries.append(f"EXISTS({subquery})")
                        params += subparams
                query = " AND ".join(sub_queries)
            else:
                query = get_geo_func(current_operator, operator, left, right, params, model._table)

            for idx, param in enumerate(params):
                if isinstance(param, str):
                    if "%" in param:  # or "POINT" in param:
                        param = param.replace("%", "%%")
                        params[idx] = f"'{param}'"
                        continue
                    try:
                        param = int(param)
                        continue
                    except ValueError as e:
                        _logger.info(e)

                if isinstance(param, tuple):
                    entries = []
                    is_number = False
                    for entry in param:
                        try:
                            int(entry)
                            is_number = True
                        except ValueError as e:
                            _logger.info(e)
                        entries.append(entry)
                    if is_number:
                        # fix
                        entries = [str(entry) for entry in entries]
                        params[idx] = f'({",".join(entries)})'
                    else:
                        entries_escaped = '","'.join(entries)
                        params[idx] = f'("{entries_escaped}")'
            return SQL(query % tuple(params))


def get_geo_func(current_operator, operator, left, right, params, table):
    """
    This method will call the SQL query corresponding to the requested geo operator
    """
    match operator:
        case "geo_greater":
            query = current_operator.get_geo_greater_sql(table, left, right, params)
        case "geo_lesser":
            query = current_operator.get_geo_lesser_sql(table, left, right, params)
        case "geo_equal":
            query = current_operator.get_geo_equal_sql(table, left, right, params)
        case "geo_touch":
            query = current_operator.get_geo_touch_sql(table, left, right, params)
        case "geo_within":
            query = current_operator.get_geo_within_sql(table, left, right, params)
        case "geo_contains":
            query = current_operator.get_geo_contains_sql(table, left, right, params)
        case "geo_intersect":
            query = current_operator.get_geo_intersect_sql(table, left, right, params)
        case _:
            raise NotImplementedError(f"The operator {operator} is not supported")
    return query


def where_calc(model, domain, active_test=True, alias=None):
    """
    This method is copied from base, we need to create our own query.
    """
    # if the object has an active field ('active', 'x_active'), filter out all
    # inactive records unless they were explicitly asked for
    if model._active_name and active_test and model._context.get("active_test", True):
        # the item[0] trick below works for domain items and '&'/'|'/'!'
        # operators too
        if not any(item[0] == model._active_name for item in domain):
            domain = [(model._active_name, "=", 1)] + domain

    query = Query(model.env.cr, alias, model._table)
    if domain:
        return expression.expression(domain, model, alias=alias, query=query).query
    return query


def parse(self):  # noqa: C901
    """Transform the leaves of the expression

    The principle is to pop elements from a leaf stack one at a time.
    Each leaf is processed. The processing is a if/elif list of various
    cases that appear in the leafs (many2one, function fields, ...).

    Three things can happen as a processing result:

    - the leaf is a logic operator, and updates the result stack
        accordingly;
    - the leaf has been modified and/or new leafs have to be introduced
        in the expression; they are pushed into the leaf stack, to be
        processed right after;
    - the leaf is converted to SQL and added to the result stack

    Example:

    =================== =================== =====================
    step                stack               result_stack
    =================== =================== =====================
                        ['&', A, B]         []
    substitute B        ['&', A, B1]        []
    convert B1 in SQL   ['&', A]            ["B1"]
    substitute A        ['&', '|', A1, A2]  ["B1"]
    convert A2 in SQL   ['&', '|', A1]      ["B1", "A2"]
    convert A1 in SQL   ['&', '|']          ["B1", "A2", "A1"]
    apply operator OR   ['&']               ["B1", "A1 or A2"]
    apply operator AND  []                  ["(A1 or A2) and B1"]
    =================== =================== =====================

    Some internal var explanation:

    :var list path: left operand seen as a sequence of field names
        ("foo.bar" -> ["foo", "bar"])
    :var obj model: model object, model containing the field
        (the name provided in the left operand)
    :var obj field: the field corresponding to `path[0]`
    :var obj column: the column corresponding to `path[0]`
    :var obj comodel: relational model of field (field.comodel)
        (res_partner.bank_ids -> res.partner.bank)
    """

    def to_ids(value, comodel, leaf):
        """Normalize a single id or name, or a list of those, into a list of ids

        :param comodel:
        :param leaf:
        :param int|str|list|tuple value:

            - if int, long -> return [value]
            - if basestring, convert it into a list of basestrings, then
            - if list of basestring ->

                - perform a name_search on comodel for each name
                - return the list of related ids
        """
        names = []
        if isinstance(value, str):
            names = [value]
        elif value and isinstance(value, tuple | list) and all(isinstance(item, str) for item in value):
            names = value
        elif isinstance(value, int):
            if not value:
                # given this nonsensical domain, it is generally cheaper to
                # interpret False as [], so that "X child_of False" will
                # match nothing
                _logger.warning("Unexpected domain [%s], interpreted as False", leaf)
                return []
            return [value]
        if names:
            return list({rid for name in names for rid in comodel._search([("display_name", "ilike", name)])})
        return list(value)

    def child_of_domain(left, ids, left_model, parent=None, prefix=""):
        """Return a domain implementing the child_of operator for [(left,child_of,ids)],
        either as a range using the parent_path tree lookup field
        (when available), or as an expanded [(left,in,child_ids)]"""
        if not ids:
            return [FALSE_LEAF]
        left_model_sudo = left_model.sudo().with_context(active_test=False)
        if left_model._parent_store:
            domain = OR([[("parent_path", "=like", rec.parent_path + "%")] for rec in left_model_sudo.browse(ids)])
        else:
            # recursively retrieve all children nodes with sudo(); the
            # filtering of forbidden records is done by the rest of the
            # domain
            parent_name = parent or left_model._parent_name
            if left_model._name != left_model._fields[parent_name].comodel_name:
                raise ValueError(f"Invalid parent field: {left_model._fields[parent_name]}")
            child_ids = set()
            records = left_model_sudo.browse(ids)
            while records:
                child_ids.update(records._ids)
                records = records.search([(parent_name, "in", records.ids)], order="id") - records.browse(
                    child_ids
                )
            domain = [("id", "in", list(child_ids))]
        if prefix:
            return [(left, "in", left_model_sudo._search(domain))]
        return domain

    def parent_of_domain(left, ids, left_model, parent=None, prefix=""):
        """Return a domain implementing the parent_of operator
        for [(left,parent_of,ids)],
        either as a range using the parent_path tree lookup field
        (when available), or as an expanded [(left,in,parent_ids)]"""
        ids = [id for id in ids if id]  # ignore (left, 'parent_of', [False])
        if not ids:
            return [FALSE_LEAF]
        left_model_sudo = left_model.sudo().with_context(active_test=False)
        if left_model._parent_store:
            parent_ids = [
                int(label) for rec in left_model_sudo.browse(ids) for label in rec.parent_path.split("/")[:-1]
            ]
            domain = [("id", "in", parent_ids)]
        else:
            # recursively retrieve all parent nodes with sudo() to avoid
            # access rights errors; the filtering of forbidden records is
            # done by the rest of the domain
            parent_name = parent or left_model._parent_name
            parent_ids = set()
            records = left_model_sudo.browse(ids)
            while records:
                parent_ids.update(records._ids)
                records = records[parent_name] - records.browse(parent_ids)
            domain = [("id", "in", list(parent_ids))]
        if prefix:
            return [(left, "in", left_model_sudo._search(domain))]
        return domain

    HIERARCHY_FUNCS = {"child_of": child_of_domain, "parent_of": parent_of_domain}

    def pop():
        """Pop a leaf to process."""
        return stack.pop()

    def push(leaf, model, alias):
        """Push a leaf to be processed right after."""
        leaf = normalize_leaf(leaf)
        check_leaf(leaf)
        stack.append((leaf, model, alias))

    def pop_result():
        return result_stack.pop()

    def push_result(sql):
        result_stack.append(sql)

    # process domain from right to left; stack contains domain leaves, in
    # the form: (leaf, corresponding model, corresponding table alias)
    stack = []
    for leaf in self.expression:
        push(leaf, self.root_model, self.root_alias)

    # stack of SQL expressions
    result_stack = []

    while stack:
        # Get the next leaf to process
        leaf, model, alias = pop()

        # ----------------------------------------
        # SIMPLE CASE
        # 1. leaf is an operator
        # 2. leaf is a true/false leaf
        # -> convert and add directly to result
        # ----------------------------------------

        if is_operator(leaf):
            if leaf == NOT_OPERATOR:
                push_result(SQL("(NOT (%s))", pop_result()))
            elif leaf == AND_OPERATOR:
                push_result(SQL("(%s AND %s)", pop_result(), pop_result()))
            else:
                push_result(SQL("(%s OR %s)", pop_result(), pop_result()))
            continue

        if leaf == TRUE_LEAF:
            push_result(SQL("TRUE"))
            continue
        if leaf == FALSE_LEAF:
            push_result(SQL("FALSE"))
            continue

        # Get working variables

        left, operator, right = leaf

        path = left.split(".", 1)

        field = model._fields[path[0]]
        if field.type == "many2one":
            comodel = model.env[field.comodel_name].with_context(active_test=False)
        elif field.type in ("one2many", "many2many"):
            comodel = model.env[field.comodel_name].with_context(**field.context)

        if (
            field.company_dependent
            and field.index == "btree_not_null"
            and not isinstance(right, SQL | Query)
            and not (
                field.type in ("datetime", "date") and len(path) > 1
            )  # READ_GROUP_NUMBER_GRANULARITY is not supported
            and model.env["ir.default"]._evaluate_condition_with_fallback(model._name, leaf) is False
        ):
            push("&", model, alias)
            sql_col_is_not_null = SQL("%s.%s IS NOT NULL", SQL.identifier(alias), SQL.identifier(field.name))
            push_result(sql_col_is_not_null)

        if field.inherited:
            parent_model = model.env[field.related_field.model_name]
            parent_fname = model._inherits[parent_model._name]
            # LEFT JOIN parent_model._table AS parent_alias
            # ON alias.parent_fname = parent_alias.id
            parent_alias = self.query.make_alias(alias, parent_fname)
            self.query.add_join(
                "LEFT JOIN",
                parent_alias,
                parent_model._table,
                SQL(
                    "%s = %s",
                    model._field_to_sql(alias, parent_fname, self.query),
                    SQL.identifier(parent_alias, "id"),
                ),
            )
            push(leaf, parent_model, parent_alias)

        elif left == "id" and operator in HIERARCHY_FUNCS:
            ids2 = to_ids(right, model, leaf)
            dom = HIERARCHY_FUNCS[operator](left, ids2, model)
            for dom_leaf in dom:
                push(dom_leaf, model, alias)

        elif field.type == "properties":
            if len(path) != 2 or "." in path[1]:
                raise ValueError(f"Wrong path {path}")
            elif operator not in (
                "=",
                "!=",
                ">",
                ">=",
                "<",
                "<=",
                "in",
                "not in",
                "like",
                "ilike",
                "not like",
                "not ilike",
            ):
                raise ValueError(f"Wrong search operator {operator!r}")
            property_name = path[1]
            check_property_field_value_name(property_name)

            if (isinstance(right, bool) or right is None) and operator in ("=", "!="):
                # check for boolean value but also for key existence
                if right:
                    # inverse the condition
                    right = False
                    operator = "!=" if operator == "=" else "="

                sql_field = model._field_to_sql(alias, field.name, self.query)
                sql_operator = SQL_OPERATORS[operator]
                sql_extra = SQL()
                if operator == "=":  # property == False
                    sql_extra = SQL(
                        "OR (%s IS NULL) OR NOT (%s ? %s)",
                        sql_field,
                        sql_field,
                        property_name,
                    )

                push_result(
                    SQL(
                        "((%s -> %s) %s '%s' %s)",
                        sql_field,
                        property_name,
                        sql_operator,
                        right,
                        sql_extra,
                    )
                )

            else:
                sql_field = model._field_to_sql(alias, field.name, self.query)

                if operator in ("in", "not in"):
                    sql_not = SQL("NOT") if operator == "not in" else SQL()
                    sql_left = SQL("%s -> %s", sql_field, property_name)  # raw value
                    sql_operator = SQL("<@") if isinstance(right, list | tuple) else SQL("@>")
                    sql_right = SQL("%s", json.dumps(right))
                    push_result(
                        SQL(
                            "(%s (%s) %s (%s))",
                            sql_not,
                            sql_left,
                            sql_operator,
                            sql_right,
                        )
                    )

                elif isinstance(right, str):
                    if operator in ("ilike", "not ilike"):
                        right = f"%{right}%"
                        unaccent = self._unaccent
                    else:
                        unaccent = lambda x: x  # noqa: E731
                    sql_left = SQL("%s ->> %s", sql_field, property_name)  # JSONified value
                    sql_operator = SQL_OPERATORS[operator]
                    sql_right = SQL("%s", right)
                    push_result(
                        SQL(
                            "((%s) %s (%s))",
                            unaccent(sql_left),
                            sql_operator,
                            unaccent(sql_right),
                        )
                    )

                else:
                    sql_left = SQL("%s -> %s", sql_field, property_name)  # raw value
                    sql_operator = SQL_OPERATORS[operator]
                    sql_right = SQL("%s", json.dumps(right))
                    push_result(
                        SQL(
                            "((%s) %s (%s))",
                            sql_left,
                            sql_operator,
                            sql_right,
                        )
                    )
        elif field.type in ("datetime", "date") and len(path) == 2:
            if path[1] not in READ_GROUP_NUMBER_GRANULARITY:
                raise ValueError(
                    f"Error when processing the field {field!r}, "
                    f"the granularity {path[1]} is not supported. "
                    "Only {', '.join(READ_GROUP_NUMBER_GRANULARITY.keys())}"
                    " are supported"
                )
            sql_field = model._field_to_sql(alias, field.name, self.query)
            if model._context.get("tz") in pytz.all_timezones_set and field.type == "datetime":
                sql_field = SQL("timezone(%s, timezone('UTC', %s))", model._context["tz"], sql_field)
            if path[1] == "day_of_week":
                first_week_day = int(get_lang(model.env, model._context.get("tz")).week_start)
                sql = SQL(
                    "mod(7 - %s + date_part(%s, %s)::int, 7) %s %s",
                    first_week_day,
                    READ_GROUP_NUMBER_GRANULARITY[path[1]],
                    sql_field,
                    SQL_OPERATORS[operator],
                    right,
                )
            else:
                sql = SQL(
                    "date_part(%s, %s) %s %s",
                    READ_GROUP_NUMBER_GRANULARITY[path[1]],
                    sql_field,
                    SQL_OPERATORS[operator],
                    right,
                )
            push_result(sql)

        # ----------------------------------------
        # PATH SPOTTED
        # -> many2one or one2many with _auto_join:
        #    - add a join, then jump into linked column: column.remaining on
        #      src_table is replaced by remaining on dst_table,
        #      and set for re-evaluation
        #    - if a domain is defined on the column, add it into evaluation
        #      on the relational table
        # -> many2one, many2many, one2many: replace by an equivalent computed
        #    domain, given by recursively searching on the remaining of the path
        # -> note: hack about columns.property should not be necessary anymore
        #    as after transforming the column, it will go through this loop once again
        # ----------------------------------------

        elif operator in ("any", "not any") and field.store and field.type == "many2one" and field.auto_join:
            # res_partner.state_id = res_partner__state_id.id
            coalias = self.query.make_alias(alias, field.name)
            self.query.add_join(
                "LEFT JOIN",
                coalias,
                comodel._table,
                SQL(
                    "%s = %s",
                    model._field_to_sql(alias, field.name, self.query),
                    SQL.identifier(coalias, "id"),
                ),
            )

            if operator == "not any":
                right = ["|", ("id", "=", False), "!", *right]

            for leaf in right:
                push(leaf, comodel, coalias)

        elif operator in ("any", "not any") and field.store and field.type == "one2many" and field.auto_join:
            # use a subquery bypassing access rules and business logic
            domain = right + field.get_domain_list(model)
            query = comodel._where_calc(domain)
            sql = query.subselect(
                comodel._field_to_sql(comodel._table, field.inverse_name, query),
            )
            push(("id", ANY_IN[operator], sql), model, alias)

        elif operator in ("any", "not any") and field.store and field.auto_join:
            raise NotImplementedError(f"auto_join attribute not supported on field {field}")

        elif operator in ("any", "not any") and field.type == "many2one":
            right_ids = comodel._search(right)
            if operator == "any":
                push((left, "in", right_ids), model, alias)
            else:
                for dom_leaf in ("|", (left, "not in", right_ids), (left, "=", False)):
                    push(dom_leaf, model, alias)

        # Making search easier when there is a left operand as one2many or many2many
        elif operator in ("any", "not any") and field.type in ("many2many", "one2many"):
            domain = field.get_domain_list(model)
            domain = AND([domain, right])
            right_ids = comodel._search(domain)
            push((left, ANY_IN[operator], right_ids), model, alias)

        elif not field.store:
            # Non-stored field should provide an implementation of search.
            if not field.search:
                # field does not support search!
                _logger.error("Non-stored field %s cannot be searched.", field, exc_info=True)
                if _logger.isEnabledFor(logging.DEBUG):
                    _logger.debug("".join(traceback.format_stack()))
                # Ignore it: generate a dummy leaf.
                domain = []
            else:
                # Let the field generate a domain.
                if len(path) > 1:
                    right = comodel._search([(path[1], operator, right)])
                    operator = "in"
                domain = field.determine_domain(model, operator, right)

            for elem in domain_combine_anies(domain, model):
                push(elem, model, alias)

        # -------------------------------------------------
        # RELATIONAL FIELDS
        # -------------------------------------------------

        # Applying recursivity on field(one2many)
        elif field.type == "one2many" and operator in HIERARCHY_FUNCS:
            ids2 = to_ids(right, comodel, leaf)
            if field.comodel_name != model._name:
                dom = HIERARCHY_FUNCS[operator](left, ids2, comodel, prefix=field.comodel_name)
            else:
                dom = HIERARCHY_FUNCS[operator]("id", ids2, comodel, parent=left)
            for dom_leaf in dom:
                push(dom_leaf, model, alias)

        elif field.type == "one2many":
            domain = field.get_domain_list(model)
            inverse_field = comodel._fields[field.inverse_name]
            inverse_is_int = inverse_field.type in ("integer", "many2one_reference")
            unwrap_inverse = (lambda ids: ids) if inverse_is_int else (lambda recs: recs.ids)

            if right is not False:
                # determine ids2 in comodel
                if isinstance(right, str):
                    op2 = TERM_OPERATORS_NEGATION[operator] if operator in NEGATIVE_TERM_OPERATORS else operator
                    ids2 = comodel._search(AND([domain or [], [("display_name", op2, right)]]))
                elif isinstance(right, collections.abc.Iterable):
                    ids2 = right
                else:
                    ids2 = [right]
                if inverse_is_int and domain:
                    ids2 = comodel._search([("id", "in", ids2)] + domain)

                if inverse_field.store:
                    # In the condition, one must avoid subqueries to return
                    # NULL values, since it makes the IN test NULL instead
                    # of FALSE.  This may discard expected results, as for
                    # instance "id NOT IN (42, NULL)" is never TRUE.
                    sql_in = SQL("NOT IN") if operator in NEGATIVE_TERM_OPERATORS else SQL("IN")
                    if not isinstance(ids2, Query):
                        ids2 = comodel.browse(ids2)._as_query(ordered=False)
                    sql_inverse = comodel._field_to_sql(ids2.table, inverse_field.name, ids2)
                    if not inverse_field.required:
                        ids2.add_where(SQL("%s IS NOT NULL", sql_inverse))
                    if (
                        inverse_field.company_dependent
                        and inverse_field.index == "btree_not_null"
                        and not inverse_field.get_company_dependent_fallback(comodel)
                    ):
                        ids2.add_where(
                            SQL(
                                "%s IS NOT NULL",
                                SQL.identifier(ids2.table, inverse_field.name),
                            )
                        )
                    push_result(
                        SQL(
                            "(%s %s %s)",
                            SQL.identifier(alias, "id"),
                            sql_in,
                            ids2.subselect(sql_inverse),
                        )
                    )
                else:
                    # determine ids1 in model related to ids2
                    recs = comodel.browse(ids2).sudo().with_context(prefetch_fields=False)
                    ids1 = unwrap_inverse(recs.mapped(inverse_field.name))
                    # rewrite condition in terms of ids1
                    op1 = "not in" if operator in NEGATIVE_TERM_OPERATORS else "in"
                    push(("id", op1, ids1), model, alias)

            else:
                if inverse_field.store and not (inverse_is_int and domain):
                    # rewrite condition to match records with/without lines
                    sub_op = "in" if operator in NEGATIVE_TERM_OPERATORS else "not in"
                    comodel_domain = [(inverse_field.name, "!=", False)]
                    query = comodel._where_calc(comodel_domain)
                    sql_inverse = comodel._field_to_sql(query.table, inverse_field.name, query)
                    sql = query.subselect(sql_inverse)
                    push(("id", sub_op, sql), model, alias)
                else:
                    comodel_domain = [(inverse_field.name, "!=", False)]
                    if inverse_is_int and domain:
                        comodel_domain += domain
                    recs = comodel.search(comodel_domain, order="id").sudo().with_context(prefetch_fields=False)
                    # determine ids1 = records with lines
                    ids1 = unwrap_inverse(recs.mapped(inverse_field.name))
                    # rewrite condition to match records with/without lines
                    op1 = "in" if operator in NEGATIVE_TERM_OPERATORS else "not in"
                    push(("id", op1, ids1), model, alias)

        elif field.type == "many2many":
            rel_table, rel_id1, rel_id2 = field.relation, field.column1, field.column2

            if operator in HIERARCHY_FUNCS:
                # determine ids2 in comodel
                ids2 = to_ids(right, comodel, leaf)
                domain = HIERARCHY_FUNCS[operator]("id", ids2, comodel)
                ids2 = comodel._search(domain)
                rel_alias = self.query.make_alias(alias, field.name)
                push_result(
                    SQL(
                        "EXISTS (SELECT 1 FROM %s AS %s WHERE %s = %s AND %s IN %s)",
                        SQL.identifier(rel_table),
                        SQL.identifier(rel_alias),
                        SQL.identifier(rel_alias, rel_id1),
                        SQL.identifier(alias, "id"),
                        SQL.identifier(rel_alias, rel_id2),
                        tuple(ids2) or (None,),
                    )
                )

            elif right is not False:
                # determine ids2 in comodel
                if isinstance(right, str):
                    domain = field.get_domain_list(model)
                    op2 = TERM_OPERATORS_NEGATION[operator] if operator in NEGATIVE_TERM_OPERATORS else operator
                    ids2 = comodel._search(AND([domain or [], [("display_name", op2, right)]]))
                elif isinstance(right, collections.abc.Iterable):
                    ids2 = right
                else:
                    ids2 = [right]

                if isinstance(ids2, Query):
                    # rewrite condition in terms of ids2
                    sql_ids2 = ids2.subselect()
                else:
                    # rewrite condition in terms of ids2
                    sql_ids2 = SQL("%s", tuple(it for it in ids2 if it) or (None,))

                if operator in NEGATIVE_TERM_OPERATORS:
                    sql_exists = SQL("NOT EXISTS")
                else:
                    sql_exists = SQL("EXISTS")

                rel_alias = self.query.make_alias(alias, field.name)
                push_result(
                    SQL(
                        "%s (SELECT 1 FROM %s AS %s WHERE %s = %s AND %s IN %s)",
                        sql_exists,
                        SQL.identifier(rel_table),
                        SQL.identifier(rel_alias),
                        SQL.identifier(rel_alias, rel_id1),
                        SQL.identifier(alias, "id"),
                        SQL.identifier(rel_alias, rel_id2),
                        sql_ids2,
                    )
                )

            else:
                # rewrite condition to match records with/without relations
                if operator in NEGATIVE_TERM_OPERATORS:
                    sql_exists = SQL("EXISTS")
                else:
                    sql_exists = SQL("NOT EXISTS")
                rel_alias = self.query.make_alias(alias, field.name)
                push_result(
                    SQL(
                        "%s (SELECT 1 FROM %s AS %s WHERE %s = %s)",
                        sql_exists,
                        SQL.identifier(rel_table),
                        SQL.identifier(rel_alias),
                        SQL.identifier(rel_alias, rel_id1),
                        SQL.identifier(alias, "id"),
                    )
                )

        elif field.type == "many2one":
            if operator in HIERARCHY_FUNCS:
                ids2 = to_ids(right, comodel, leaf)
                if field.comodel_name != model._name:
                    dom = HIERARCHY_FUNCS[operator](left, ids2, comodel, prefix=field.comodel_name)
                else:
                    dom = HIERARCHY_FUNCS[operator]("id", ids2, comodel, parent=left)
                for dom_leaf in dom:
                    push(dom_leaf, model, alias)

            elif (
                isinstance(right, str)
                or isinstance(right, tuple | list)
                and right
                and all(isinstance(item, str) for item in right)
            ):
                # resolve string-based m2o criterion into IDs subqueries

                # Special treatment to ill-formed domains
                operator = "in" if operator in ("<", ">", "<=", ">=") else operator
                dict_op = {"not in": "!=", "in": "=", "=": "in", "!=": "not in"}
                if isinstance(right, tuple):
                    right = list(right)
                if not isinstance(right, list) and operator in ("not in", "in"):
                    operator = dict_op[operator]
                elif isinstance(right, list) and operator in (
                    "!=",
                    "=",
                ):  # for domain (FIELD,'=',['value1','value2'])
                    operator = dict_op[operator]
                if operator in NEGATIVE_TERM_OPERATORS:
                    res_ids = comodel._search([("display_name", TERM_OPERATORS_NEGATION[operator], right)])
                    for dom_leaf in (
                        "|",
                        (left, "not in", res_ids),
                        (left, "=", False),
                    ):
                        push(dom_leaf, model, alias)
                else:
                    res_ids = comodel._search([("display_name", operator, right)])
                    push((left, "in", res_ids), model, alias)

            else:
                # right == [] or right == False
                # and all other cases are handled by _condition_to_sql()
                push_result(model._condition_to_sql(alias, left, operator, right, self.query))

        # -------------------------------------------------
        # BINARY FIELDS STORED IN ATTACHMENT
        # -> check for null only
        # -------------------------------------------------

        elif field.type == "binary" and field.attachment:
            if operator in ("=", "!=") and not right:
                sub_op = "in" if operator in NEGATIVE_TERM_OPERATORS else "not in"
                sql = SQL(
                    ("(SELECT res_id FROM ir_attachment " "WHERE res_model = %s AND res_field = %s)"),
                    model._name,
                    left,
                )
                push(("id", sub_op, sql), model, alias)
            else:
                _logger.error(
                    "Binary field '%s' stored in attachment: ignore %s %s %s",
                    field.string,
                    left,
                    operator,
                    reprlib.repr(right),
                )
                push(TRUE_LEAF, model, alias)

        # -------------------------------------------------
        # OTHER FIELDS
        # -> datetime fields: manage time part of the datetime
        #    column when it is not there
        # -> manage translatable fields
        # -------------------------------------------------

        elif field.type in [
            "geo_polygon",
            "geo_multi_polygon",
            "geo_point",
            "geo_multi_point",
            "geo_line",
            "geo_multi_line",
        ]:
            push_result(__leaf_to_sql(leaf, model, alias))
        else:
            if field.type == "datetime" and right:
                if isinstance(right, str) and len(right) == 10:
                    if operator in (">", "<="):
                        right += " 23:59:59"
                    else:
                        right += " 00:00:00"
                    push((left, operator, right), model, alias)
                elif isinstance(right, date) and not isinstance(right, datetime):
                    if operator in (">", "<="):
                        right = datetime.combine(right, time.max)
                    else:
                        right = datetime.combine(right, time.min)
                    push((left, operator, right), model, alias)
                else:
                    push_result(model._condition_to_sql(alias, left, operator, right, self.query))

            elif (
                field.translate
                and (isinstance(right, str) or right is False)
                and left == field.name
                and self._has_trigram
                and field.index == "trigram"
                and operator in ("=", "like", "ilike", "=like", "=ilike")
            ):
                right = right or ""
                sql_operator = SQL_OPERATORS[operator]
                need_wildcard = operator in WILDCARD_OPERATORS

                if need_wildcard and not right:
                    push_result(SQL("FALSE") if operator in NEGATIVE_TERM_OPERATORS else SQL("TRUE"))
                    continue
                push_result(model._condition_to_sql(alias, left, operator, right, self.query))

                if not need_wildcard:
                    right = field.convert_to_column(right, model, validate=False)

                # a prefilter using trigram index to speed up '=', 'like', 'ilike'
                # '!=', '<=', '<', '>', '>=', 'in', 'not in',
                # 'not like', 'not ilike' cannot use this trick
                if operator == "=":
                    _right = value_to_translated_trigram_pattern(right)
                else:
                    _right = pattern_to_translated_trigram_pattern(right)

                if _right != "%":
                    # combine both generated SQL expressions
                    # (above and below) with an AND
                    push("&", model, alias)
                    sql_column = SQL("%s.%s", SQL.identifier(alias), SQL.identifier(field.name))
                    indexed_value = self._unaccent(SQL("jsonb_path_query_array(%s, '$.*')::text", sql_column))
                    _sql_operator = SQL("LIKE") if operator == "=" else sql_operator
                    push_result(
                        SQL(
                            "%s %s %s",
                            indexed_value,
                            _sql_operator,
                            self._unaccent(SQL("%s", _right)),
                        )
                    )
            else:
                push_result(model._condition_to_sql(alias, left, operator, right, self.query))

    # ----------------------------------------
    # END OF PARSING FULL DOMAIN
    # -> put result in self.result and self.query
    # ----------------------------------------
    [self.result] = result_stack
    self.query.add_where(self.result)


expression.expression.parse = parse
