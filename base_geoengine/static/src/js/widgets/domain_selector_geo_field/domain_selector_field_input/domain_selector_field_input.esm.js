/** @odoo-module **/

import {Component, useProps} from "@odoo/owl";
import {registry} from "@web/core/registry";
const parsers = registry.category("parsers");

export class DomainSelectorFieldInput extends Component {
    setup() {
        this.props = useProps();
    }

    parseValue(value) {
        const parser = parsers.get(this.props.field.type, (val) => val);
        try {
            return parser(value);
            // eslint-disable-next-line no-unused-vars
        } catch (_) {
            return value;
        }
    }

    onChange(ev) {
        this.props.update({value: this.parseValue(ev.target.value)});
    }
}
DomainSelectorFieldInput.template = "base_geoengine.DomainSelectorFieldInput";
