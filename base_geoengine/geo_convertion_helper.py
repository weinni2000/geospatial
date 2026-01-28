# Copyright 2011-2012 Nicolas Bessi (Camptocamp SA)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import logging

from shapely.errors import GEOSException

from odoo import _

_logger = logging.getLogger(__name__)

try:
    import geojson
    from shapely import wkb, wkt
    from shapely.geometry import shape
    from shapely.geometry.base import BaseGeometry
except ImportError:
    _logger.warning(_("Shapely or geojson are not available in the sys path"))  # pylint: disable=prefer-env-translation


def value_to_shape(value, use_wkb=False):
    """Transforms input into a Shapely object"""

    # always use_wkb for now
    use_wkb = True

    if not value:
        return wkt.loads("GEOMETRYCOLLECTION EMPTY")
    if isinstance(value, str):
        # We try to do this before parsing json exception
        # exception are ressource costly
        if "{" in value:
            geo_dict = geojson.loads(value)
            return shape(geo_dict)
        if use_wkb:
            try:
                res = wkb.loads(value, hex=True)
                return res
            except GEOSException as e:
                _logger.warning("GEOSException:")
                _logger.warning(e)
            except Exception as e:
                _logger.warning("WKB conversion failed:")
                _logger.warning(e)
        # elif len(value) == 42 and "POINT" not in value and "(" not in value:
        # not clear why use_wkb is not set correctly anymore.
        # if a record is stored it's instantly
        # executed again with the hash value
        # The hash value eg "0101000000A4703D0AD7232C400AD7A3703D0A4840"
        # is also possible, but we do not handle it now.
        #        value = wkb.loads(value, hex=True)
        #        return value
        # <NIKMOD>
        # 'POINT(0.0 0.0)'
        try:
            return wkt.loads(value)
        except Exception as e:
            # error = _("Failed to parse WKT: %(e)s") % {"e":e}
            error = f"Failed to parse WKT: {e}"
            _logger.warning(error)  # pylint: disable=prefer-env-translation
            empty = "POINT(0 0)"
            return wkt.loads(empty)
            # </NIKMOD>
    elif hasattr(value, "wkt"):
        return value if isinstance(value, BaseGeometry) else wkt.loads(value.wkt)
    else:
        raise TypeError(
            _(  # pylint: disable=prefer-env-translation
                "Write/create/search geo type must be wkt/geojson "
                "string or must respond to wkt"
            )
        )
