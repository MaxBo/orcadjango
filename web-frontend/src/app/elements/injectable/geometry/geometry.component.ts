import { AfterViewInit, Component, Input, OnInit } from '@angular/core';
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
import { Draw, Select } from "ol/interaction";
import { click, always } from 'ol/events/condition';
import { FullScreen } from "ol/control";
import { FeatureLike } from "ol/Feature";

@Component({
  selector: 'geometry',
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
  protected editMode: 'select' | 'draw' | 'freehand' | 'none' = 'select';
  protected featuresSelected = false;

  ngOnInit() {
    this.wktInput = this.wkt;
    if (!this.height)
      this.height = this.edit? '400px': '200px';
  }

  ngAfterViewInit() {
    this.wktSrid = this.srid;
    const format = new WKT();
    this.geom = format.readGeometry(this.wkt);
    this.initMap();
    if (!this.edit)
      this.initPreview();
    else
      this.initEdit();
    this.onModeChanged();
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
    this.map.getView().fit(this.featureLayer?.getSource().getExtent());
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
      fs = new MultiPolygon([]);
      features.forEach((feature: Feature<any>) => fs.appendPolygon(feature.getGeometry()));
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
