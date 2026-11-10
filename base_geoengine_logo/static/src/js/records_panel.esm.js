/* Copyright 2026 mytime.click
 * License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl). */

import {onWillStart, onWillUpdateProps} from "@odoo/owl";
import {RecordsPanel} from "@base_geoengine/js/views/geoengine/records_panel/records_panel.esm";
import {patch} from "@web/core/utils/patch";

patch(RecordsPanel.prototype, {
    setup() {
        super.setup(...arguments);
        this.recordImage = {field: false, recordIds: new Set()};
        onWillStart(() => this.loadRecordImages(this.props));
        onWillUpdateProps((nextProps) => this.loadRecordImages(nextProps));
    },

    /**
     * Ask the server which image field the view shows and which of the
     * listed records have an image, so records without one get no
     * placeholder.
     * @param {Object} props
     */
    async loadRecordImages(props) {
        const result = await this.orm.call(
            props.list.resModel,
            "get_geoengine_record_images",
            [this.env.config.viewId || null, props.list.records.map((r) => r.resId)]
        );
        this.recordImage = {
            field: result.field,
            recordIds: new Set(result.record_ids),
        };
    },

    /**
     * URL of the record's image, or false when the view shows no image or the
     * record has none.
     * @param {Object} record
     * @returns {String|Boolean}
     */
    getRecordImageUrl(record) {
        const {field, recordIds} = this.recordImage;
        if (!field || !recordIds.has(record.resId)) {
            return false;
        }
        return `/web/image/${record.resModel}/${record.resId}/${field}/64x64`;
    },
});
