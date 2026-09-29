/** @odoo-module **/

/**
 * Copyright 2023 ACSONE SA/NV
 */

import {Component, onMounted, onPatched, useProps} from "@odoo/owl";

/**
 * It allows you to set a default value for the field and a readonly property for the active_ids value.
 */
export class DomainSelectorFieldInputForActiveIds extends Component {
    setup() {
        this.props = useProps();
        // Owl 3 has no onRendered hook anymore: onMounted + onPatched together
        // cover "after every render" (initial and subsequent).
        const setActiveIds = () => {
            if (this.props.value !== "{ACTIVE_IDS}") {
                this.props.update({value: "{ACTIVE_IDS}"});
            }
        };
        onMounted(setActiveIds);
        onPatched(setActiveIds);
    }
}
DomainSelectorFieldInputForActiveIds.template =
    "base_geoengine.DomainSelectorFieldInputForActiveIds";
