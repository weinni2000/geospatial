/** @odoo-module **/

/**
 * Copyright 2023 ACSONE SA/NV
 */

import {
    Component,
    onWillStart,
    onWillUpdateProps,
    proxy,
    t,
    usePlugin,
    useProps,
} from "@odoo/owl";
import {useOwnedDialogs, useService} from "@web/core/utils/hooks";
import {DebugModePlugin} from "@web/core/debug_mode_plugin";
import {Domain} from "@web/core/domain";
import {DomainSelectorGeoFieldDialog} from "../domain_selector_geo_field_dialog/domain_selector_geo_field_dialog.esm";
import {Expression} from "@web/core/tree_editor/condition_tree";
import {Select} from "@web/core/tree_editor/tree_editor_components";
import {_t} from "@web/core/l10n/translation";
import {formatAST} from "@web/core/py_js/py";

let referenceModelsPromise = null;

/**
 * Load (once) the models having geo fields that can be used as reference in
 * an indirect geo condition.
 * @param {*} orm
 * @param {String} resModel
 * @returns {Promise<Array>}
 */
export function loadGeoReferenceModels(orm, resModel) {
    if (!referenceModelsPromise) {
        referenceModelsPromise = orm
            .call(resModel, "get_geo_reference_models", [])
            .catch((error) => {
                referenceModelsPromise = null;
                throw error;
            });
    }
    return referenceModelsPromise;
}

/**
 * Parse the right operand of a geo condition. It is either a geometry
 * (WKT/GeoJSON string) or a reference to the records of another model
 * ({"<model>.<geo field>": <domain>}), kept as a python dict expression.
 * @param {*} value
 * @returns {Object|null}
 */
export function parseGeoValue(value) {
    if (typeof value === "string") {
        return {mode: "geometry", geometry: value};
    }
    if (!(value instanceof Expression)) {
        return null;
    }
    const ast = value.toAST();
    // 11: python dictionary
    if (ast.type !== 11) {
        return null;
    }
    const keys = Object.keys(ast.value);
    if (keys.length > 1) {
        return null;
    }
    const key = keys[0] || "";
    const index = key.lastIndexOf(".");
    return {
        mode: "records",
        resModel: key ? key.substring(0, index) : "",
        fieldName: key ? key.substring(index + 1) : "",
        domain: key ? formatAST(ast.value[key]) : "[]",
    };
}

export function isGeoValue(value) {
    return parseGeoValue(value) !== null;
}

/**
 * Build the right operand of an indirect geo condition.
 * @param {Object} params
 * @returns {Expression}
 */
export function makeGeoValue({resModel, fieldName, domain = "[]"} = {}) {
    const value = {};
    if (resModel && fieldName) {
        value[`${resModel}.${fieldName}`] = new Domain(domain).ast;
    }
    // 11: python dictionary
    return new Expression({type: 11, value});
}

/**
 * Value editor of the domain selector for the geo operators: either the
 * records of a model (through one of its geo fields, filtered by a
 * sub-domain) or a WKT/GeoJSON geometry.
 */
export class DomainSelectorGeoFieldInput extends Component {
    static template = "base_geoengine.DomainSelectorGeoFieldInput";
    static components = {Select};
    props = useProps({
        value: t.any(),
        update: t.function(),
        resModel: t.string(),
    });

    setup() {
        this.orm = useService("orm");
        this.treeProcessor = useService("tree_processor");
        this.addDialog = useOwnedDialogs();
        this.debugMode = usePlugin(DebugModePlugin);
        this.state = proxy({referenceModels: [], domainDescription: ""});
        this.modeOptions = [
            ["records", _t("records of")],
            ["geometry", _t("geometry")],
        ];

        onWillStart(async () => {
            this.state.referenceModels = await loadGeoReferenceModels(
                this.orm,
                this.props.resModel
            );
            await this.loadDomainDescription(this.props);
        });
        onWillUpdateProps((nextProps) => this.loadDomainDescription(nextProps));
    }

    get geoValue() {
        return parseGeoValue(this.props.value) || {mode: "records"};
    }

    get modelOptions() {
        return this.state.referenceModels.map((info) => [info.model, info.name]);
    }

    get modelPlaceholder() {
        return _t("Select a model");
    }

    get fieldOptions() {
        const info = this.state.referenceModels.find(
            (model) => model.model === this.geoValue.resModel
        );
        return info ? info.fields : [];
    }

    async loadDomainDescription(props) {
        const {mode, resModel, domain} = parseGeoValue(props.value) || {};
        let description = "";
        if (mode === "records" && resModel) {
            if (new Domain(domain).toString() === "[]") {
                description = _t("all records");
            } else {
                try {
                    const tree = await this.treeProcessor.treeFromDomain(
                        resModel,
                        new Domain(domain)
                    );
                    description = await this.treeProcessor.getDomainTreeDescription(
                        resModel,
                        tree
                    );
                } catch {
                    description = domain;
                }
            }
        }
        this.state.domainDescription = description;
    }

    onModeChange(mode) {
        this.props.update(mode === "geometry" ? "" : makeGeoValue());
    }

    onModelChange(resModel) {
        const info = this.state.referenceModels.find(
            (model) => model.model === resModel
        );
        this.props.update(makeGeoValue({resModel, fieldName: info?.fields[0]?.[0]}));
    }

    onFieldChange(fieldName) {
        this.props.update(makeGeoValue({...this.geoValue, fieldName}));
    }

    onGeometryChange(ev) {
        this.props.update(ev.target.value.trim());
    }

    openDomainDialog() {
        const geoValue = this.geoValue;
        this.addDialog(DomainSelectorGeoFieldDialog, {
            resModel: geoValue.resModel,
            domain: geoValue.domain,
            readonly: false,
            isDebugMode: this.debugMode.isActive(),
            onConfirm: (domain) =>
                this.props.update(makeGeoValue({...geoValue, domain})),
            title: _t("Subdomain"),
        });
    }
}
