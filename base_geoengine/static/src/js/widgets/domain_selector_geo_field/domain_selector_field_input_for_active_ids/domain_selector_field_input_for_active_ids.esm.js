/** @odoo-module **/

/**
 * Copyright 2023 ACSONE SA/NV
 */

import {Component} from "@odoo/owl";
import {useLayoutEffect} from "@web/owl2/utils";

/**
 * It allows you to set a default value for the field and a readonly property for the active_ids value.
 */
export class DomainSelectorFieldInputForActiveIds extends Component {
    setup() {
        useLayoutEffect(() => {
            if (this.props.value !== "{ACTIVE_IDS}") {
                this.props.update({value: "{ACTIVE_IDS}"});
            }
        });
    }
}
DomainSelectorFieldInputForActiveIds.template =
    "base_geoengine.DomainSelectorFieldInputForActiveIds";
