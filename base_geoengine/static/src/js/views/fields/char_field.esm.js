import {CharField} from "@web/views/fields/char_field";
import {patch} from "@web/core/utils/patch";
import {xml} from "@odoo/owl";

patch(CharField, {
    template: xml`
    <t t-if="props.readonly">
        <span t-esc="formattedValue" />
        </t>
        <t t-else="">
        <input
            class="o_input"
            t-att-class="{
                'o_field_translate': isTranslatable,
                'o_field_placeholder': hasDynamicPlaceholder
            }"
            t-att-id="props.id"
            t-att-type="props.isPassword ? 'password' : 'text'"
            t-att-autocomplete="props.autocomplete or (props.isPassword ? 'new-password' : 'off')"
            t-att-maxlength="maxLength > 0 and maxLength"
            t-att-placeholder="placeholder"
            t-on-blur="onBlur"
            t-ref="input"
        />
        <div class="o_field_char_buttons position-absolute d-inline">
            <t t-if="isTranslatable">
                <TranslationButton
                    fieldName="props.name"
                    record="props.record"
                />
            </t>
            <button t-if="hasDynamicPlaceholder"
                class="btn m-0 py-0 px-2 fa fa-magic"
                title="Insert Field"
                t-on-click="onDynamicPlaceholderOpen"
            />
        </div>
        </t>
        `,
});

export default CharField;
