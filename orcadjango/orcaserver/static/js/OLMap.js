/* global ol */
'use strict';
function GeometryTypeControl(opt_options) {
    // Map control to switch type when geometry type is unknown
    const options = opt_options || {};

    const element = document.createElement('div');
    element.className = 'switch-type type-' + options.type + ' ol-control ol-unselectable';
    if (options.active) {
        element.classList.add("type-active");
    }

    const self = this;
    const switchType = function(e) {
        e.preventDefault();
        if (options.widget.currentGeometryType !== self) {
            options.widget.map.removeInteraction(options.widget.interactions.draw);
            options.widget.interactions.draw = new ol.interaction.Draw({
                features: options.widget.featureCollection,
                type: options.type
            });
            options.widget.map.addInteraction(options.widget.interactions.draw);
            options.widget.currentGeometryType.element.classList.remove('type-active');
            options.widget.currentGeometryType = self;
            element.classList.add("type-active");
        }
    };

    element.addEventListener('click', switchType, false);
    element.addEventListener('touchstart', switchType, false);

    ol.control.Control.call(this, {
        element: element
    });
};
ol.inherits(GeometryTypeControl, ol.control.Control);

// TODO: allow deleting individual features (#8972)
{
    const wktFormat = new ol.format.WKT();

    function MapWidget(options) {
        this.map = null;
        this.interactions = {draw: null, modify: null};
        this.typeChoices = false;
        this.ready = false;

        // Default options
        this.options = {
            default_lat: 0,
            default_lon: 0,
            default_zoom: 12,
            is_collection: options.geom_name.indexOf('Multi') > -1 || options.geom_name.indexOf('Collection') > -1
        };

        // Altering using user-provided options
        for (const property in options) {
            if (options.hasOwnProperty(property)) {
                this.options[property] = options[property];
            }
        }
        if (!options.base_layer) {
            this.options.base_layer = new ol.layer.Tile({source: new ol.source.OSM()});
        }

        this.map = this.createMap();
        this.featureCollection = new ol.Collection();
        this.featureOverlay = new ol.layer.Vector({
            map: this.map,
            source: new ol.source.Vector({
                features: this.featureCollection,
                useSpatialIndex: false // improve performance
            }),
            updateWhileAnimating: true, // optional, for instant visual feedback
            updateWhileInteracting: true // optional, for instant visual feedback
        });

        // Populate and set handlers for the feature container
        const self = this;
        this.featureCollection.on('add', function(event) {
            const feature = event.element;
            feature.on('change', function() {
                self.serializeFeatures();
            });
            if (self.ready) {
                self.serializeFeatures();
                if (!self.options.is_collection) {
                    self.disableDrawing(); // Only allow one feature at a time
                }
            }
        });

        this.createInteractions();
        const initial_value = document.getElementById(this.options.id).value;
        if (initial_value && !this.options.is_collection) {
            this.disableDrawing();
        }
        this.redraw();
        this.serializeFeatures();
        this.ready = true;
    }

    MapWidget.prototype.redraw = function() {
        let value = document.getElementById(this.options.id).value;
        this.clearFeatures();
        if (!value) {
            this.map.getView().setCenter(this.defaultCenter());
            return;
        }
        let re = new RegExp("SRID=[0-9]*;"),
            match = value.match(re);
        if (match){
            value = value.replace(match[0], '');
            re = new RegExp("[0-9]*;");
            let srid = parseInt(match[0].match(re)[0]);
            options = {
                dataProjection: 'EPSG:' + srid,
                featureProjection: 'EPSG:' + this.options.map_srid
            }
        }
        const features = wktFormat.readFeatures(value, options);
        const extent = ol.extent.createEmpty();
        features.forEach(function(feature) {
            this.featureOverlay.getSource().addFeature(feature);
            ol.extent.extend(extent, feature.getGeometry().getExtent());
        }, this);
        // Center/zoom the map
        this.map.getView().fit(extent);
    }

    MapWidget.prototype.createMap = function() {
        const map = new ol.Map({
            target: this.options.map_id,
            layers: [this.options.base_layer],
            view: new ol.View({
                zoom: this.options.default_zoom
            })
        });
        return map;
    };

    MapWidget.prototype.createInteractions = function() {
        const self = this;

        // Initialize the modify interaction
        this.interactions.modify = new ol.interaction.Modify({
            features: this.featureCollection,
            deleteCondition: function(event) {
                return ol.events.condition.shiftKeyOnly(event) &&
                    ol.events.condition.singleClick(event);
            }
        });

        // Initialize the draw interaction
        let geomType = this.options.geom_name;
        if (geomType === "Unknown" || geomType === "GeometryCollection") {
            // Default to Point, but create icons to switch type
            geomType = "Point";
            this.currentGeometryType = new GeometryTypeControl({widget: this, type: "Point", active: true});
            this.map.addControl(this.currentGeometryType);
            this.map.addControl(new GeometryTypeControl({widget: this, type: "LineString", active: false}));
            this.map.addControl(new GeometryTypeControl({widget: this, type: "Polygon", active: false}));
            this.typeChoices = true;
        }
        this.interactions.draw = new ol.interaction.Draw({
            features: this.featureCollection,
            type: geomType
        });

        this.interactions.select = new ol.interaction.Select({
            condition: ol.events.condition.click,
            toggleCondition: ol.events.condition.shiftKeyOnly
        });
        // select button
        var button = document.createElement('button'),
            icon = document.createElement('i');
        button.title = 'Select Feature (SHIFT+click to select multiple)';
        button.type = 'button';
        icon.classList.add('icon-hand-up');
        button.appendChild(icon);
        button.addEventListener('click', function(){
            self.interactions.select.setActive(true);
            self.interactions.modify.setActive(false);
            self.disableDrawing();
        });
        var element = document.createElement('div');
        element.className = 'toggle-select ol-unselectable ol-control';
        element.appendChild(button);
        var SelectControl = new ol.control.Control({
            element: element
        });
        // draw button
        button = document.createElement('button');
        button.title = 'Draw/Modify Feature';
        icon = document.createElement('i');
        button.type = 'button';
        icon.classList.add('icon-pencil');
        button.appendChild(icon);
        button.addEventListener('click', function(){
            self.interactions.select.setActive(false);
            self.interactions.modify.setActive(true);
            self.enableDrawing();
        });
        element = document.createElement('div');
        element.className = 'toggle-draw ol-unselectable ol-control';
        element.appendChild(button);
        var DrawControl = new ol.control.Control({
            element: element
        });
        this.map.addInteraction(this.interactions.draw);
        this.map.addInteraction(this.interactions.modify);
        this.map.addInteraction(this.interactions.select);
        this.interactions.select.setActive(false);

        this.map.addControl(SelectControl);
        this.map.addControl(DrawControl);
        this.map.addControl(new ol.control.FullScreen());

        this.map.on('pointermove', function (e) {
            if (!self.interactions.select.getActive()) return;
            var pixel = self.map.getEventPixel(e.originalEvent);
            var hit = self.map.hasFeatureAtPixel(pixel);
            self.map.getTargetElement().style.cursor = hit ? 'pointer' : '';
        });
    };

    MapWidget.prototype.toggleSelect = function(enable){
        if (enable === false)
            this.map.removeInteraction(this.interactions.select);
        else
            this.map.addInteraction(this.interactions.select);
    };

    MapWidget.prototype.toggleDraw = function(enable){
        if (enable === false){
            this.map.removeInteraction(this.interactions.draw);
            this.map.removeInteraction(this.interactions.modify);
        }
        else {
            this.map.addInteraction(this.interactions.draw);
            this.map.addInteraction(this.interactions.modify);
        }
    };

    MapWidget.prototype.defaultCenter = function() {
        const center = [this.options.default_lon, this.options.default_lat];
        if (this.options.map_srid) {
            return ol.proj.transform(center, 'EPSG:4326', this.map.getView().getProjection());
        }
        return center;
    };

    MapWidget.prototype.enableDrawing = function() {
        this.interactions.draw.setActive(true);
        if (this.typeChoices) {
            // Show geometry type icons
            const divs = document.getElementsByClassName("switch-type");
            for (let i = 0; i !== divs.length; i++) {
                divs[i].style.visibility = "visible";
            }
        }
    };

    MapWidget.prototype.disableDrawing = function() {
        if (this.interactions.draw) {
            this.interactions.draw.setActive(false);
            if (this.typeChoices) {
                // Hide geometry type icons
                const divs = document.getElementsByClassName("switch-type");
                for (let i = 0; i !== divs.length; i++) {
                    divs[i].style.visibility = "hidden";
                }
            }
        }
    };

    MapWidget.prototype.clearSelectedFeatures = function() {
        const self = this;
        this.interactions.select.getFeatures().forEach(function(feat){
            self.featureCollection.remove(feat);
        })
        this.interactions.select.getFeatures().clear();
        this.serializeFeatures();
    };

    MapWidget.prototype.clearFeatures = function() {
        this.featureCollection.clear();
        // Empty textarea widget
        document.getElementById(this.options.id).value = '';
        this.enableDrawing();
    };

    MapWidget.prototype.serializeFeatures = function() {
        // Three use cases: GeometryCollection, multigeometries, and single geometry
        let geometry = null;
        const features = this.featureOverlay.getSource().getFeatures();
        if (this.options.is_collection) {
            if (this.options.geom_name === "GeometryCollection") {
                const geometries = [];
                for (let i = 0; i < features.length; i++) {
                    geometries.push(features[i].getGeometry());
                }
                geometry = new ol.geom.GeometryCollection(geometries);
            } else {
                if (features[0]) {
                    geometry = features[0].getGeometry().clone();
                    for (let j = 1; j < features.length; j++) {
                        switch (geometry.getType()) {
                        case "MultiPoint":
                            geometry.appendPoint(features[j].getGeometry().getPoint(0));
                            break;
                        case "MultiLineString":
                            geometry.appendLineString(features[j].getGeometry().getLineString(0));
                            break;
                        case "MultiPolygon":
                            geometry.appendPolygon(features[j].getGeometry().getPolygon(0));
                        }
                    }
                }
            }
        } else {
            if (features[0]) {
                geometry = features[0].getGeometry();
            }
        }
        var prefix = "SRID=" + this.options.map_srid + ";";
        document.getElementById(this.options.id).value = (geometry) ? prefix + wktFormat.writeGeometry(geometry) : '';
    };

    window.MapWidget = MapWidget;
}
