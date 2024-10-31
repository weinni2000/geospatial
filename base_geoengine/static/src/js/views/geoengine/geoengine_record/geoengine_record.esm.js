/** @odoo-module */

/**
 * Copyright 2023 ACSONE SA/NV
 */
import {Component, onWillUpdateProps, xml} from "@odoo/owl";
import {Field} from "@web/views/fields/field";
import {GeoengineCompiler} from "../geoengine_compiler.esm";
import {INFO_BOX_ATTRIBUTE} from "../geoengine_arch_parser.esm";
import {registry} from "@web/core/registry";
import {standardFieldProps} from "@web/views/fields/standard_field_props";
import {useViewCompiler} from "@web/views/view_compiler";
import {user} from "@web/core/user";

const formatters = registry.category("formatters");

function getValue(record, fieldName) {
    const field = record.fields[fieldName];
    const value = record._values[fieldName];
    const formatter = formatters.get(field.type, String);
    return formatter(value, {field, data: record._values});
}

export class GeoengineRecord extends Component {
    /**
     * Setup the record by compiling the arch and the info-box template.
     */
    static props = {...standardFieldProps};

    static components = {
        Field,
    };
    static template = xml`
<p t-out="special">hello</p>

    <div
            t-att-data-id="props.record.id"
            t-att-tabindex="props.record.model.useSampleModel ? -1 : 0"
        >
            <t
t-call="{{ special }}"
t-call-context="this.renderingContext"
            />
        </div>
        `;
    //
    //
    setup() {
        this.user = user;
        const {Compiler, templates} = this.props;
        const ViewCompiler = Compiler || this.constructor.Compiler;

        this.templates_A = useViewCompiler(ViewCompiler, templates);
        this.special_old = templates[this.constructor.INFO_BOX_ATTRIBUTE];
        this.special = this.templates_A[this.constructor.INFO_BOX_ATTRIBUTE];

        this.createRecord(this.props);
        onWillUpdateProps(this.createRecord);
    }

    /**
     * Create record with formatter.
     * @param {*} props
     */
    createRecord(props) {
        const {record} = props;
        this.record = Object.create(null);
        for (const fieldName in record._values) {
            this.record[fieldName] = {
                get value() {
                    return getValue(record, fieldName);
                },
            };
        }
    }

    get renderingContext() {
        return {
            context: this.props.record.context,
            JSON,
            record: this.props.record,
            read_only_mode: this.props.readonly,
            selection_mode: this.props.forceGlobalClick,
            user_context: this.user.context,
            __comp__: Object.assign(Object.create(this), {this: this}),
        };
    }
}
GeoengineRecord.Compiler = GeoengineCompiler;
// GeoengineRecord.components = { Field };
GeoengineRecord.INFO_BOX_ATTRIBUTE = INFO_BOX_ATTRIBUTE;
