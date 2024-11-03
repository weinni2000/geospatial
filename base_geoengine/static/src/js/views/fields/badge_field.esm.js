import {BadgeField} from "@web/views/fields/badge/badge_field";
import {patch} from "@web/core/utils/patch";
import {xml} from "@odoo/owl";

patch(BadgeField, {
    template: xml`
    <span t-if="props.record.data[props.name]" class="badge rounded-pill" t-att-class="classFromDecoration" t-esc="formattedValue" />
        `,
});

export default BadgeField;
