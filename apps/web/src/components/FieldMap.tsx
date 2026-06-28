"use client";

import { useEffect, useRef } from "react";
import maplibregl from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";

// Estilo raster OpenStreetMap (gratuito, sem chave de API).
const OSM_STYLE: maplibregl.StyleSpecification = {
  version: 8,
  sources: {
    osm: {
      type: "raster",
      tiles: ["https://tile.openstreetmap.org/{z}/{x}/{y}.png"],
      tileSize: 256,
      attribution: "© OpenStreetMap",
    },
  },
  layers: [{ id: "osm", type: "raster", source: "osm" }],
};

interface Props {
  lat: number;
  lon: number;
  onPick?: (lat: number, lon: number) => void;
}

export function FieldMap({ lat, lon, onPick }: Props) {
  const ref = useRef<HTMLDivElement>(null);
  const mapRef = useRef<maplibregl.Map | null>(null);
  const markerRef = useRef<maplibregl.Marker | null>(null);

  useEffect(() => {
    if (!ref.current || mapRef.current) return;
    const map = new maplibregl.Map({
      container: ref.current,
      style: OSM_STYLE,
      center: [lon, lat],
      zoom: 12,
    });
    map.addControl(new maplibregl.NavigationControl(), "top-right");
    markerRef.current = new maplibregl.Marker({ color: "#1b5e20" })
      .setLngLat([lon, lat])
      .addTo(map);
    map.on("click", (e) => {
      markerRef.current?.setLngLat(e.lngLat);
      onPick?.(e.lngLat.lat, e.lngLat.lng);
    });
    mapRef.current = map;
    return () => {
      map.remove();
      mapRef.current = null;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    markerRef.current?.setLngLat([lon, lat]);
    mapRef.current?.easeTo({ center: [lon, lat] });
  }, [lat, lon]);

  return (
    <div className="overflow-hidden rounded-xl border border-stone-200">
      <div ref={ref} className="h-[260px] w-full" />
      <p className="bg-stone-100 px-3 py-1 text-[11px] text-stone-500">
        Clique no mapa para posicionar o talhão. (Desenho de polígono e import de CAR/shapefile: próxima fase.)
      </p>
    </div>
  );
}
