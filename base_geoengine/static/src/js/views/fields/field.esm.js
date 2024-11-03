import {Field} from "@web/views/fields/field";
import {patch} from "@web/core/utils/patch";
import {xml} from "@odoo/owl";

patch(Field, {
    template: xml`
   <div t-att-name="props.name" t-att-class="classNames" t-att-style="props.style" t-att-data-tooltip-template="tooltip and 'web.FieldTooltip'" t-att-data-tooltip-info="tooltip">
    <t t-component="field.component" t-props="fieldComponentProps"/>
</div>
        `,
});

export default Field;
