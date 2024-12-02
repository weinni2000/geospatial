import {IntegerField} from "@web/views/fields/integer/integer_field";
import {patch} from "@web/core/utils/patch";
import {xml} from "@odoo/owl";

patch(IntegerField, {
    template: xml`
            <span t-if="props.readonly" t-esc="formattedValue" />
        <input
            t-else=""
            t-ref="numpadDecimal"
            t-on-focusin="onFocusIn"
            t-on-focusout="onFocusOut"
            t-att-id="props.id"
            t-att-type="props.inputType"
            t-att-placeholder="props.placeholder"
            inputmode="numeric"
            class="o_input"
            autocomplete="off"
            t-att-step="props.step" />
        `,
});

export default IntegerField;
