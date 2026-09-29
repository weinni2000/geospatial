/** @odoo-module */

/**
 * Copyright 2023 ACSONE SA/NV
 */

import {Component, signal, useProps} from "@odoo/owl";

export class SearchBarRecords extends Component {
    setup() {
        this.props = useProps();
        this.searchComponent = signal.ref();
    }

    /**
     * When a key is pressed, the props onInputKeyup method is called.
     * @param {*} ev
     */
    onInputKeyup(ev) {
        this.props.onInputKeyup(this.searchComponent().value);
        ev.preventDefault();
        ev.stopPropagation();
    }
}

SearchBarRecords.template = "base_geoengine.SearchBarRecords";
