import { AfterViewInit, Component, ElementRef, Input, OnInit, ViewChild } from '@angular/core';
import { BaseInjectableComponent } from "../injectable.component";
import { Feature, Map, View } from 'ol';
import { GeoJSON, WKT } from "ol/format";
import { Geometry, MultiPolygon } from "ol/geom";
import { v4 as uuid } from 'uuid';
import TileLayer from "ol/layer/Tile";
import { OSM } from "ol/source";
import { fromLonLat } from "ol/proj";
import VectorLayer from "ol/layer/Vector";
import { Fill, Stroke, Style } from "ol/style";
import VectorSource from "ol/source/Vector";
import { Vector } from "ol/layer";
import { Draw, Select, Snap, DragPan, defaults as interactionDefaults } from "ol/interaction";
import { click, always } from 'ol/events/condition';
import { FullScreen } from "ol/control";
import { FeatureLike } from "ol/Feature";
import { register } from 'ol/proj/proj4'
import proj4 from 'proj4';
import { createBox } from "ol/interaction/Draw";

proj4.defs("EPSG:25832", "+proj=utm +zone=32 +ellps=GRS80 +units=m +no_defs");
proj4.defs("EPSG:3044", "+proj=utm +zone=32 +ellps=GRS80 +towgs84=565.04,49.91,465.84,1.9848,-1.7439,9.0587,4.0772 +units=m +no_defs +type=crs");
register(proj4);

@Component({
  selector: 'inj-geometry',
  templateUrl: './geometry.component.html',
  styleUrls: ['./geometry.component.scss', '../../../../../node_modules/ol/ol.css'],
  inputs: ['edit'],
  outputs: ['valueChanged']
})
export class GeometryComponent extends BaseInjectableComponent implements AfterViewInit, OnInit {
  @Input() wkt!: string;
  @Input() height?: string;
  @Input() srid = 4326;
  protected wktSrid = 4326;
  protected wktInput: string = '';
  protected mapSrid = 3857;
  protected geom?: Geometry;
  protected featureLayer?: Vector<any>;
  protected mapId = `map-${uuid()}`;
  protected map?: Map;
  protected view?: View;
  protected editMode: 'select' | 'draw' | 'freehand' | 'none' | 'square' | 'circle' = 'select';
  protected featuresSelected = false;

  ngOnInit() {
    this.wktInput = this.wkt;
    if (!this.height)
      this.height = this.edit? '400px': '160px';
  }

  ngAfterViewInit() {
    this.wktSrid = this.srid;
    const format = new WKT();
    this.geom = this.wkt? format.readGeometry(this.wkt): new MultiPolygon([]);
    this.initMap();
    if (!this.edit)
      this.initPreview();
    else
      this.initEdit();
    this.onModeChanged();
    // disable right click context menu on map (right mouse is used to move)
    // ViewChild is not working here (no idea why)
    document.getElementById(this.mapId)?.addEventListener('contextmenu', (e: any) => {
      e.preventDefault();
    });
  }

  initMap() {
    this.map = new Map({
      target: this.mapId,
      layers: [
        new TileLayer({
          className: 'bw',
          source: new OSM({ attributions: [] }),
        }),
      ],
      view: new View({
        center: fromLonLat([13.3392,52.5192]),
        zoom: 7,
        projection: `EPSG:${this.mapSrid}`
      }),
      controls: this.edit? undefined: [],
      interactions: interactionDefaults({dragPan: false}).extend([
        new DragPan({
          condition: function (mapBrowserEvent) {
            // drag map on left, middle and right click
            return (
              mapBrowserEvent.originalEvent.isPrimary &&
              mapBrowserEvent.originalEvent.button < 3
            );
          },
        }),
      ]),
    });
  }

  initPreview() {
    const style = new Style({
      stroke: new Stroke({
        color: 'yellow',
        width: 2
      }),
      fill: new Fill({
        color: 'rgba(255, 242, 0, 0.3)'
      })
    });
    const source = new VectorSource({ format: new GeoJSON()});
    this.featureLayer = new VectorLayer<any>({
      source: source,
      style: style
    });
    if (this.geom) {
      const geom = this.geom.clone();
      geom.transform('EPSG:4326', `EPSG:${this.mapSrid}`);
      source.addFeature(new Feature(geom));
    }
    this.map?.addLayer(this.featureLayer);
    this.zoomToExtent();
  }

  zoomToExtent() {
    if (!this.map) return;
    const extent = this.featureLayer?.getSource().getExtent();
    try {
      this.map.getView().fit(extent);
    }
    catch {
      return;
    }
    this.map.getView().setZoom(this.map.getView().getZoom()! - 0.5);
  }

  initEdit() {
    if (!this.map) return;
    const style = new Style({
      stroke: new Stroke({
        color: 'yellow',
        width: 2
      }),
      fill: new Fill({
        color: 'rgba(255, 242, 0, 0.3)'
      })
    });
    const source = new VectorSource({ format: new GeoJSON()});
    this.featureLayer = new VectorLayer<any>({
      source: source,
      style: style
    });
    if (this.geom) {
      const geom = this.geom.clone();
      geom.transform('EPSG:4326', `EPSG:${this.mapSrid}`);
      source.addFeature(new Feature(geom));
    }
    source.on('addfeature', event => this.onFeatureChange());

    const draw = new Draw({
      source: source,
      type: 'Polygon',
    });
    this.featureLayer.set('draw', draw);
    this.map.addInteraction(draw);

    const freehand = new Draw({
      source: source,
      type: 'Polygon',
      freehand: true
    });
    this.featureLayer.set('freehand', freehand);
    this.map.addInteraction(freehand);

    const snap = new Snap({
      source: source,
    });
    this.map.addInteraction(snap);

    // WKT does not support circle geoms, ToDo: transform circle into poly and update on map
/*    const circle = new Draw({
      source: source,
      type: 'Circle'
    });
    this.featureLayer.set('circle', circle);
    this.map.addInteraction(circle);*/

    const square = new Draw({
      source: source,
      type: 'Circle',
      geometryFunction: createBox()
    });
    this.featureLayer.set('square', square);
    this.map.addInteraction(square);

    const selected = new Style({
      fill: new Fill({
        color: 'rgba(16, 74, 229, 0.3)',
      }),
      stroke: new Stroke({
        color: 'rgba(16, 74, 229,)',
        width: 2,
      }),
    });
    const select = new Select({
      condition: click,
      layers: [this.featureLayer],
      style: selected,
      toggleCondition: always,
      multi: true
    });
    select.on('select', event => {
       this.featuresSelected = select.getFeatures().getLength() > 0;
    })
    this.featureLayer.set('select', select);
    this.map.addInteraction(select);

    this.map.addControl(new FullScreen());

    this.map.on('pointermove', event => {
      const div = this.map?.getTargetElement();
      if (!div) return;
      if (select.getActive()) {
        this.featureLayer?.getFeatures(event.pixel).then((features: FeatureLike[]) => {
          div.style.cursor = features.length > 0 ? 'pointer' : 'default';
        })
      }
      else
        div.style.cursor = 'default';
    });
    this.map.addLayer(this.featureLayer);
    this.zoomToExtent();
  }

  onModeChanged() {
    const draw = this.featureLayer?.get('draw');
    draw?.setActive(this.editMode === 'draw');

    const freehand = this.featureLayer?.get('freehand');
    freehand?.setActive(this.editMode === 'freehand');
    const circle = this.featureLayer?.get('circle');
    circle?.setActive(this.editMode === 'circle');
    const square = this.featureLayer?.get('square');
    square?.setActive(this.editMode === 'square');

    const select = this.featureLayer?.get('select');
    select?.setActive(this.editMode === 'select');
    if (this.editMode !== 'select') {
      select?.getFeatures().clear();
    }
  }

  deleteSelected() {
    const select = this.featureLayer?.get('select');
    const features = select.getFeatures();
    if (features.getLength() > 0) {
      features.forEach((feature: Feature<any>) => this.featureLayer?.getSource().removeFeature(feature));
      this.onFeatureChange();
    }
  }

  deleteAll() {
    this.featureLayer?.getSource().clear();
    this.onFeatureChange();
  }

  onFeatureChange() {
    if (!this.featureLayer) return;
    const features = this.featureLayer.getSource().getFeatures();
    if (features.length === 0) {
      this.geom = undefined;
      this.wktInput = '';
      this.emitChange();
      return;
    }
    const format = new WKT();
    let fs = features[0].getGeometry().clone();
    if (features.length > 1) {
      if (!(fs instanceof MultiPolygon)) {
        fs = new MultiPolygon([fs.getCoordinates()]);
      }
      features.forEach((feature: Feature<any>, i: number) => {
        if (i > 0) fs.appendPolygon(feature.getGeometry());
      });
    }
    const out = fs.clone();
    this.geom = fs.clone();
    this.geom?.transform(this.map?.getView().getProjection().getCode(), `EPSG:${this.srid}`);
    out.transform(this.map?.getView().getProjection().getCode(), `EPSG:${this.wktSrid}`);
    this.wktInput = format.writeGeometry(out);

    this.emitChange();
  }

  changeSrid(srid: number) {
    const geom = this.geom?.clone();
    geom?.transform(`EPSG:${this.srid}`, `EPSG:${srid}`);
    this.wktInput = geom? (new WKT()).writeGeometry(geom): '';
    this.wktSrid = srid;
  }

  applyWkt() {
    const format = new WKT();
    const geom = format.readGeometry(this.wktInput);
    this.geom = geom? geom.clone(): undefined;
    geom?.transform(`EPSG:${this.wktSrid}`, `EPSG:${this.mapSrid}`);
    this.geom?.transform(`EPSG:${this.wktSrid}`, `EPSG:${this.srid}`);
    const source = this.featureLayer?.getSource();
    source?.clear();
    if (geom) {
      source.addFeature(new Feature(geom));
      this.zoomToExtent();
    }
    this.emitChange();
  }

  private emitChange() {
    const format = new WKT();
    const wkt = this.geom? format.writeGeometry(this.geom): '';
    this.valueChanged.emit(wkt);
  }
}
