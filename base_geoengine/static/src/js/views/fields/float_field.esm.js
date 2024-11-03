import {FloatField} from "@web/views/fields/float_field";
import {patch} from "@web/core/utils/patch";
import {xml} from "@odoo/owl";

patch(FloatField, {
    template: xml`
            <span t-if="props.readonly" t-esc="formattedValue" />
        <input
            t-else=""
            t-on-focusin="onFocusIn"
            t-on-focusout="onFocusOut"
            t-att-id="props.id"
            t-ref="numpadDecimal"
            t-att-placeholder="props.placeholder"
            t-att-type="props.inputType"
            inputmode="decimal"
            class="o_input"
            autocomplete="off"
            t-att-step="props.step" />
        `,
});

export default FloatField;
