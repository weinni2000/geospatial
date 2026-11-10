1. Go to *GeoEngine \> Configuration \> View Management* and open a
   geoengine view.
2. On the *GeoEngine Data* tab, set *Record Image Field* to an image field of
   the view's model (e.g. *Image* of contacts).

3. To draw the image on the polygons, open a vector layer of the view and set
   *Record Image on Polygons* to *Background (tiled)* or *Centered*.

   *Centered* draws the image once per polygon, on the point farthest from its
   edges (of the largest part of a multipolygon). At every zoom level it uses
   the largest height between *Maximum Image Height* and *Minimum Image
   Height* at which at least *Minimum Visible Share* of the image lies inside
   the polygon; when even the minimum height doesn't fit, the image appears
   only after zooming in.

A module can also set it in XML:

```xml
<record id="my_geoengine_view" model="ir.ui.view">
    <field
        name="geoengine_record_image_field_id"
        ref="my_module.field_my_model__image_128"
    />
</record>
```
