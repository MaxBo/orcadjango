import { AfterViewInit, Component, Input, OnInit } from '@angular/core';
import { BaseInjectableComponent } from "../injectable.component";
import { Feature, Map, View } from 'ol';
import { GeoJSON, WKT } from "ol/format";
import { Geometry } from "ol/geom";
import { v4 as uuid } from 'uuid';
import TileLayer from "ol/layer/Tile";
import { OSM } from "ol/source";
import { fromLonLat } from "ol/proj";
import VectorLayer from "ol/layer/Vector";
import { Fill, Stroke, Style } from "ol/style";
import VectorSource from "ol/source/Vector";
import { Vector } from "ol/layer";
import { Draw } from "ol/interaction";

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
  srid = 3857;
  geom?: Geometry;
  featureLayer?: Vector<any>;
  mapId = `map-${uuid()}`;
  map?: Map;
  view?: View;

  ngOnInit() {
    if (!this.height)
      this.height = this.edit? '500px': '200px';
  }

  ngAfterViewInit() {
    const format = new WKT();
    const feature = format.readFeature(this.wkt);
    this.geom = feature.getGeometry();
    this.geom?.transform('EPSG:4326', `EPSG:${this.srid}`);
    this.initMap();
    if (!this.edit)
      this.initPreview();
    else
      this.initEdit();
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
    if (this.geom)
      source.addFeature(new Feature(this.geom));
    this.map?.addLayer(this.featureLayer);
    this.map?.getView().fit(source.getExtent());
  }

  initEdit() {
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
    if (this.geom)
      source.addFeature(new Feature(this.geom));

    const draw = new Draw({
      source: source,
      type: 'Polygon',
    }); // global so we can remove it later
    this.map?.addInteraction(draw);

    this.map?.addLayer(this.featureLayer);
    this.map?.getView().fit(source.getExtent());
  }
}
