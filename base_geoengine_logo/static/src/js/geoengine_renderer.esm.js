/* Copyright 2026 mytime.click
 * License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl). */

/* global ol */

import {GeoengineRenderer} from "@base_geoengine/js/views/geoengine/geoengine_renderer/geoengine_renderer.esm";
import {patch} from "@web/core/utils/patch";

// Height of a record image in the tiled background, in pixels
const POLYGON_IMAGE_HEIGHT = 40;
// Space around each image in the tiled background, in pixels
const TILE_PADDING = 24;

/**
 * Load an image; resolves with null when it can't be loaded.
 * @param {String} url
 * @returns {Promise<HTMLImageElement|null>}
 */
async function loadImage(url) {
    const image = new Image();
    image.src = url;
    try {
        await image.decode();
    } catch {
        return null;
    }
    return image;
}

/**
 * Repeating canvas pattern: the image scaled to POLYGON_IMAGE_HEIGHT with
 * TILE_PADDING of transparent space around it.
 * @param {HTMLImageElement} image
 * @returns {CanvasPattern}
 */
function createTilePattern(image) {
    const scale = POLYGON_IMAGE_HEIGHT / image.naturalHeight;
    const width = Math.max(1, Math.round(image.naturalWidth * scale));
    const canvas = document.createElement("canvas");
    canvas.width = width + TILE_PADDING;
    canvas.height = POLYGON_IMAGE_HEIGHT + TILE_PADDING;
    const context = canvas.getContext("2d");
    context.drawImage(
        image,
        TILE_PADDING / 2,
        TILE_PADDING / 2,
        width,
        POLYGON_IMAGE_HEIGHT
    );
    return context.createPattern(canvas, "repeat");
}

// Placement of a centered image: candidate grid per refinement step and steps
const POLE_GRID = 12;
const POLE_STEPS = 3;
// Sample points per side of the image when measuring its visible share
const COVERAGE_SAMPLES = 10;
// Factor between two tried image heights
const SIZE_STEP = 0.85;
// Outline simplification for the placement: share of the polygon's extent
const SIMPLIFY_SHARE = 1 / 300;

/**
 * The largest part of a (multi)polygon, simplified for fast placement.
 * @param {ol.geom.Geometry} geometry
 * @returns {ol.geom.Polygon|null}
 */
function largestPolygon(geometry) {
    let polygon = null;
    if (geometry.getType() === "Polygon") {
        polygon = geometry;
    } else if (geometry.getType() === "MultiPolygon") {
        for (const part of geometry.getPolygons()) {
            if (!polygon || part.getArea() > polygon.getArea()) {
                polygon = part;
            }
        }
    }
    if (!polygon) {
        return null;
    }
    const [minX, minY, maxX, maxY] = polygon.getExtent();
    const tolerance = Math.max(maxX - minX, maxY - minY) * SIMPLIFY_SHARE;
    return polygon.simplify(tolerance);
}

/**
 * Distance of a coordinate to the nearest edge of the polygon.
 * @param {ol.geom.Polygon} polygon
 * @param {Array} coordinate
 * @returns {Number}
 */
function distanceToEdges(polygon, coordinate) {
    let distance = Infinity;
    for (const ring of polygon.getLinearRings()) {
        const closest = ring.getClosestPoint(coordinate);
        distance = Math.min(
            distance,
            Math.hypot(closest[0] - coordinate[0], closest[1] - coordinate[1])
        );
    }
    return distance;
}

/**
 * Pole of inaccessibility: the point inside the polygon farthest from its
 * edges (center of the largest inscribed circle), by a refined grid search.
 * @param {ol.geom.Polygon} polygon
 * @returns {Array} coordinate
 */
function poleOfInaccessibility(polygon) {
    let [minX, minY, maxX, maxY] = polygon.getExtent();
    let best = null;
    for (let step = 0; step < POLE_STEPS; step++) {
        const dx = (maxX - minX) / POLE_GRID;
        const dy = (maxY - minY) / POLE_GRID;
        for (let i = 0; i < POLE_GRID; i++) {
            for (let j = 0; j < POLE_GRID; j++) {
                const coordinate = [minX + (i + 0.5) * dx, minY + (j + 0.5) * dy];
                if (!polygon.intersectsCoordinate(coordinate)) {
                    continue;
                }
                const distance = distanceToEdges(polygon, coordinate);
                if (!best || distance > best.distance) {
                    best = {coordinate, distance};
                }
            }
        }
        if (!best) {
            break;
        }
        // Search again, finer, around the best cell
        [minX, maxX] = [best.coordinate[0] - dx, best.coordinate[0] + dx];
        [minY, maxY] = [best.coordinate[1] - dy, best.coordinate[1] + dy];
    }
    return best
        ? best.coordinate
        : polygon.getInteriorPoint().getCoordinates().slice(0, 2);
}

/**
 * Share (0-1) of a rectangle centered on `center` that lies inside the
 * polygon, measured on a grid of sample points.
 * @param {ol.geom.Polygon} polygon
 * @param {Array} center
 * @param {Number} width map units
 * @param {Number} height map units
 * @returns {Number}
 */
function visibleShare(polygon, center, width, height) {
    let inside = 0;
    for (let i = 0; i < COVERAGE_SAMPLES; i++) {
        for (let j = 0; j < COVERAGE_SAMPLES; j++) {
            const coordinate = [
                center[0] + ((i + 0.5) / COVERAGE_SAMPLES - 0.5) * width,
                center[1] + ((j + 0.5) / COVERAGE_SAMPLES - 0.5) * height,
            ];
            if (polygon.intersectsCoordinate(coordinate)) {
                inside++;
            }
        }
    }
    return inside / COVERAGE_SAMPLES ** 2;
}

patch(GeoengineRenderer.prototype, {
    setup() {
        super.setup(...arguments);
        this.state.popupImageUrl = false;
    },

    /**
     * Add the record images to the layer style when the layer shows them on
     * its polygons (record_image_display).
     * @override
     */
    styleVectorLayerAndLegend(cfg, data, lv) {
        super.styleVectorLayerAndLegend(...arguments);
        if (cfg.record_image_display && cfg.record_image_display !== "none") {
            this.addRecordImagesToLayer(cfg, data, lv);
        }
    },

    async addRecordImagesToLayer(cfg, data, lv) {
        const model = cfg.model || this.props.data.resModel;
        const ids = data
            .map((item) => (item._values === undefined ? item.id : item._values.id))
            .filter(Boolean);
        const result = await this.orm.call(model, "get_geoengine_record_images", [
            this.env.config.viewId || null,
            ids,
        ]);
        if (!result.field || !result.record_ids.length) {
            return;
        }
        const images = {};
        await Promise.all(
            result.record_ids.map(async (id) => {
                const image = await loadImage(
                    `/web/image/${model}/${id}/${result.field}/256x256`
                );
                if (image) {
                    images[id] = image;
                }
            })
        );
        const fillStyles = {};
        if (cfg.record_image_display === "fill") {
            for (const [id, image] of Object.entries(images)) {
                fillStyles[id] = new ol.style.Style({
                    fill: new ol.style.Fill({color: createTilePattern(image)}),
                });
            }
        }
        // Per feature: placement point and the style chosen per resolution
        const placements = new WeakMap();
        const baseStyle = lv.getStyle();
        lv.setStyle((feature, resolution) => {
            const base =
                typeof baseStyle === "function"
                    ? baseStyle(feature, resolution)
                    : baseStyle;
            const styles = Array.isArray(base) ? base : [base].filter(Boolean);
            const id = (feature.get("attributes") || {}).id;
            if (!images[id]) {
                return styles;
            }
            const imageStyle =
                cfg.record_image_display === "fill"
                    ? fillStyles[id]
                    : this.getCenteredImageStyle(
                          feature,
                          images[id],
                          resolution,
                          cfg,
                          placements
                      );
            // Labels are drawn after fills and icons, so they stay on top
            return imageStyle ? [...styles, imageStyle] : styles;
        });
    },

    /**
     * One image per feature, on its pole of inaccessibility, at the largest
     * height (between the layer's maximum and minimum) where at least the
     * layer's minimum share of the image lies inside the polygon; nothing when
     * even the minimum height doesn't fit.
     * @param {ol.Feature} feature
     * @param {HTMLImageElement} image
     * @param {Number} resolution map units per pixel
     * @param {Object} cfg vector layer
     * @param {WeakMap} placements cache per feature
     * @returns {ol.style.Style|null}
     */
    getCenteredImageStyle(feature, image, resolution, cfg, placements) {
        let placement = placements.get(feature);
        if (!placement) {
            const polygon = largestPolygon(feature.getGeometry());
            placement = {
                polygon,
                point: polygon && new ol.geom.Point(poleOfInaccessibility(polygon)),
                styles: new Map(),
            };
            placements.set(feature, placement);
        }
        if (!placement.polygon) {
            return null;
        }
        if (placement.styles.has(resolution)) {
            return placement.styles.get(resolution);
        }
        const minVisible = (cfg.record_image_min_visible || 70) / 100;
        const minHeight = cfg.record_image_min_size || 24;
        const maxHeight = cfg.record_image_max_size || 96;
        const aspect = image.naturalWidth / image.naturalHeight;
        const center = placement.point.getCoordinates();
        let style = null;
        for (let height = maxHeight; height >= minHeight; height *= SIZE_STEP) {
            const share = visibleShare(
                placement.polygon,
                center,
                height * aspect * resolution,
                height * resolution
            );
            if (share >= minVisible) {
                style = new ol.style.Style({
                    geometry: placement.point,
                    image: new ol.style.Icon({
                        img: image,
                        scale: height / image.naturalHeight,
                    }),
                });
                break;
            }
        }
        placement.styles.set(resolution, style);
        return style;
    },

    /**
     * Show the record image of the view (if the record has one) at the top
     * of the info box.
     */
    mountGeoengineRecord() {
        super.mountGeoengineRecord(...arguments);
        this.state.popupImageUrl = false;
        this.loadPopupImage(this.record);
    },

    async loadPopupImage(record) {
        if (!record || !record.resId) {
            return;
        }
        const result = await this.orm.call(
            record.resModel,
            "get_geoengine_record_images",
            [this.env.config.viewId || null, [record.resId]]
        );
        // The user may have clicked another feature meanwhile
        if (this.record !== record || !result.record_ids.includes(record.resId)) {
            return;
        }
        this.state.popupImageUrl = `/web/image/${record.resModel}/${record.resId}/${result.field}/256x128`;
    },

    hidePopup() {
        super.hidePopup(...arguments);
        this.state.popupImageUrl = false;
    },
});
