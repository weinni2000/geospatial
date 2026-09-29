/** @odoo-module **/

/**
 * Copyright 2023 ACSONE SA/NV
 */

import {DomainSelectorDialog} from "@web/core/domain_selector_dialog/domain_selector_dialog";
import {_t} from "@web/core/l10n/translation";
import {t, useProps} from "@odoo/owl";

/**
 * This class is extended from DomainSelectorGeoField in order to be able to
 * modify the title of the dialog window and to add some props to it.
 */
export class DomainSelectorGeoFieldDialog extends DomainSelectorDialog {
    props = useProps({
        close: t.function(),
        onConfirm: t.function(),
        resModel: t.string(),
        className: t.string().optional(),
        readonly: t.boolean().optional(true),
        isDebugMode: t.boolean().optional(false),
        defaultLeafValue: t.array().optional(),
        domain: t.string().optional(""),
        fieldName: t.string().optional(),
        title: t.string().optional("Domain"),
        model: t.object().optional(),
    });

    get dialogTitle() {
        return _t(this.props.title);
    }
}

DomainSelectorGeoFieldDialog.template = "base_geoengine.DomainSelectorGeoFieldDialog";
