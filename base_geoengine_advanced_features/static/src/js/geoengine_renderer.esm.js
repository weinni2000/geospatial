/* Copyright 2026 mytime.click
 * License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl). */

/* global ol */

import {GeoengineRenderer} from "@base_geoengine/js/views/geoengine/geoengine_renderer/geoengine_renderer.esm";
import {_t} from "@web/core/l10n/translation";
import {patch} from "@web/core/utils/patch";

// Representations that color the features by their attribute value
const VALUE_REPRESENTATIONS = ["proportion", "colored"];

/**
 * CSS color of a #RRGGBB hex color with the given opacity.
 * @param {String} hex
 * @param {Number} opacity
 * @returns {String}
 */
function hexToRgba(hex, opacity) {
    const value = parseInt(hex.slice(1), 16);
    const red = Math.floor(value / 65536) % 256;
    const green = Math.floor(value / 256) % 256;
    const blue = value % 256;
    const alpha = opacity === undefined || opacity === false ? 1 : opacity;
    return `rgba(${red}, ${green}, ${blue}, ${alpha})`;
}

/**
 * Text escaped for use in HTML.
 * @param {String} text
 * @returns {String}
 */
function escapeHtml(text) {
    const element = document.createElement("div");
    element.textContent = text;
    return element.innerHTML;
}

/**
 * A value counts as empty when it is 0, false, null, undefined, NaN or "".
 * @param {*} value
 * @returns {Boolean}
 */
function isEmptyValue(value) {
    return !value;
}

/**
 * Legend line of the empty value color, added to the legend of the layer.
 * @param {String} legend
 * @param {String} color
 * @param {String} layerName
 * @returns {String}
 */
function addEmptyValueLegend(legend, color, layerName) {
    const line =
        `<div><div class="geostats-legend-block" style="background-color:${color}">` +
        `</div> ${escapeHtml(_t("0 / empty"))}</div>`;
    if (!legend) {
        return (
            '<div class="geostats-legend">' +
            `<div class="geostats-legend-title">${escapeHtml(layerName)}</div>` +
            `${line}</div>`
        );
    }
    const end = legend.lastIndexOf("</div>");
    return legend.slice(0, end) + line + legend.slice(end);
}

patch(GeoengineRenderer.prototype, {
    /**
     * Opt-in: the symbols get the color of their value's class, as on a
     * colored range layer; their size stays proportional to the value.
     */
    styleVectorLayerProportion(cfg, data) {
        const sizeInfo = super.styleVectorLayerProportion(cfg, data);
        if (!cfg.proportion_colored) {
            return sizeInfo;
        }
        // The classification is only required in the form: default quantile
        const colorInfo = this.styleVectorLayerColored(
            {...cfg, classification: cfg.classification || "quantile"},
            data
        );
        const styles = {};
        return {
            style: (feature) => {
                const sizeStyles = sizeInfo.style(feature);
                let colorStyles = null;
                try {
                    colorStyles = colorInfo.style(feature);
                } catch {
                    // Value in no class: keep the begin color
                }
                if (!sizeStyles || !colorStyles) {
                    return sizeStyles;
                }
                const radius = sizeStyles[0].getImage().getRadius();
                const fill = colorStyles[0].getFill();
                const stroke = colorStyles[0].getStroke();
                const key = `${radius}|${fill.getColor()}`;
                if (!styles[key]) {
                    styles[key] = [
                        new ol.style.Style({
                            image: new ol.style.Circle({fill, stroke, radius}),
                            fill,
                            stroke,
                        }),
                    ];
                }
                return styles[key];
            },
            legend: colorInfo.legend,
        };
    },

    styleVectorLayer(cfg, data) {
        const styleInfo = super.styleVectorLayer(cfg, data);
        if (
            !cfg.empty_value_color ||
            !cfg.attribute_field_id ||
            !VALUE_REPRESENTATIONS.includes(cfg.geo_repr)
        ) {
            return styleInfo;
        }
        const indicator = cfg.attribute_field_id[1];
        const color = hexToRgba(cfg.empty_value_color, cfg.layer_opacity);
        const emptyStyles = this.createStylesWithColors([color])[color];
        const valueStyle = styleInfo.style;
        return {
            ...styleInfo,
            style: (feature) => {
                if (isEmptyValue(feature.get("attributes")[indicator])) {
                    return emptyStyles;
                }
                return valueStyle(feature);
            },
            legend: addEmptyValueLegend(styleInfo.legend, color, cfg.name),
        };
    },
});
