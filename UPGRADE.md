# Upgrade log 19.0 -> 20.0

## base_geoengine

Version: `20.0.1.0.0`. `odev upgrade-code --from 19.0 --to 20.0` produced no changes.

### Technical changes

| Change | Reason (20.0 breaking change) | Odoo source |
|---|---|---|
| `security/ir.model.access.csv` -> `security/ir.access.csv` (`operation` + `domain` columns) | `ir.model.access` removed; replaced by `ir.access` | `odoo/addons/base/models/ir_access.py` |
| `Domain._to_sql(self, table)` / `Field._condition_to_sql(self, table, field_expr, operator, value)` | ORM SQL generation now takes a `TableSQL` instead of `(model, alias, query)` | `odoo/orm/query.py` (`TableSQL`) |
| `model._check_field_access` -> `model.check_field_access` | Method made public | `odoo/orm/models.py` |
| `where_calc()` uses `model._access_domain("read")` + `Domain.optimize_full()` | Mirrors 20.0 `BaseModel._search` so record rules apply to indirect geo sub-queries | `odoo/orm/models.py` |
| `Query.add_where()` gets `SQL` objects (`SQL.identifier`) | Raw strings deprecated ("Since 20.0, use only SQL in the where clause") | [odoo/odoo@b38925c050f8](https://github.com/odoo/odoo/commit/b38925c050f8) |
| `CREATE INDEX` built with `SQL`/`SQL.identifier` | `cr.execute` with f-strings is rejected by the 20.0 linters | `odoo/tools/sql.py` |
| `attribute_field_id_domain`: `Binary` -> `Json` (non-stored compute, no data migration) | Domain values for fields are JSON in 20.0 | - |
| `geoengine` view-type icon `fa fa-globe` -> `map` | 20.0 view switcher uses the new icon set | `ir.ui.view._get_view_info` |
| OWL/JS components, templates (controller, renderer, layers/records panels, search bar, domain selector) adapted | 20.0 web client API changes | see commit `c3915d97` |

### Data migration

None required: no stored field or model was renamed. Existing ACL rows
(`ir.model.access` -> `ir.access`) are converted by Odoo's standard upgrade.
Note: the Odoo upgrade-scripts repository was not available locally (empty
directory), so this conversion could not be checked against its scripts.

### Validation

- Install on `demo_bulletin_board_20_0_upgrade`: OK.
- Fresh DB `geo_test_20b` (`-i base_geoengine -t /base_geoengine`): 33 tests, 0 failed, 0 warnings.
- Re-validated on fresh DB `geo_test_20c` (2026-10-08): 33 tests, 0 failed.
- Knowledge base: `/knowledge/base_geoengine/19.0_to_20.0.md`.

### Functional test scenarios

1. Settings > Users: give a user "Geoengine / User"; check they can read layers but not edit them. An admin can create/edit them.
2. Open a model with a geoengine view (e.g. via `base_geoengine_demo`): the map renders with raster + vector layers, and the layers panel toggles them.
3. Records panel: search a record, click it, and check the map zooms to its geometry.
4. Vector layer form: pick a geo field and check the attribute-field domain only offers numeric fields of the same model.
5. Indirect geo search (`geo_intersect` with `{'model.field': domain}`) as a non-admin user with a record rule: records hidden by the rule must not influence results.
