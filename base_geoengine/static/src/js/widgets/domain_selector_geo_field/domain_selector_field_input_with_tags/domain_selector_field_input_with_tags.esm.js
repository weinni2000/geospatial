/** @odoo-module **/

import {Component, signal} from "@odoo/owl";

export class DomainSelectorFieldInputWithTags extends Component {
    inputRef = signal.ref();

    removeTag(tagIndex) {
        const value = [...this.props.value];
        value.splice(tagIndex, 1);
        this.props.update({value});
    }
    addTag(value) {
        this.props.update({value: this.props.value.concat(value)});
    }

    onBtnClick() {
        const value = this.inputRef().value;
        this.inputRef().value = "";
        this.addTag(value);
    }
}
DomainSelectorFieldInputWithTags.template =
    "base_geoengine.DomainSelectorFieldInputWithTags";
