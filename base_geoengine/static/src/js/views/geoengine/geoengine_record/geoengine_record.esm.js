/**
 * Copyright 2023 ACSONE SA/NV
 */

import {GeoengineCompiler} from "../geoengine_compiler.esm";
import {INFO_BOX_ATTRIBUTE} from "../geoengine_arch_parser.esm";
import {registry} from "@web/core/registry";
import {useViewCompiler} from "@web/views/view_compiler";
import {Component, onWillUpdateProps, xml} from "@odoo/owl";
import {user} from "@web/core/user";
import {Field} from "@web/views/fields/field";

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
    static template = xml`
    <!--
    <p>hello from original2</p>
    <p t-out="props.record.data.name"></p>
    -->

    <div
            t-att-data-id="props.record.data.id"
            t-att-tabindex="props.record.model.useSampleModel ? -1 : 0"
        >

            <t
t-call="{{ templates[this.constructor.INFO_BOX_ATTRIBUTE] }}"
t-call-context="this.renderingContext"
            />


        </div>

        `;

    setup() {
        this.user = user;
        const {Compiler, templates} = this.props;
        const ViewCompiler = Compiler || this.constructor.Compiler;

        this.templates = useViewCompiler(ViewCompiler, templates);
        this.createRecord(this.props);
        onWillUpdateProps(this.createRecord);
    }

    /**
     * Create record with formatter.
     * @param {*} props
     */
    createRecord(props) {
        // Const record = props.record;
        // this.record = Object.create(null); Breaks in Dev Mode
        // this.props.record = Object.create({});
        for (const fieldName in props.record._values) {
            this.props.record[fieldName] = {
                get value() {
                    return getValue(props.record, fieldName);
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
GeoengineRecord.components = {Field};
GeoengineRecord.INFO_BOX_ATTRIBUTE = INFO_BOX_ATTRIBUTE;
