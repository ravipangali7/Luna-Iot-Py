"""
Geofence boundary import service.
Parses KMZ, KML, or shapefile (zip) and returns GeoJSON Polygon or MultiPolygon in WGS84 [lng, lat].
"""
import io
import os
import tempfile
import zipfile
import xml.etree.ElementTree as ET

# KML namespace
KML_NS = {'kml': 'http://www.opengis.net/kml/2.2'}


def _parse_kml_coordinates(text: str) -> list[list[float]]:
    """Parse KML <coordinates> string (lon,lat[,alt] per point) into list of [lng, lat]."""
    if not text or not text.strip():
        return []
    points = []
    for part in text.strip().replace('\n', ' ').split():
        part = part.strip().rstrip(',')
        if not part:
            continue
        tokens = part.split(',')
        if len(tokens) >= 2:
            try:
                lng = float(tokens[0])
                lat = float(tokens[1])
                points.append([lng, lat])
            except ValueError:
                continue
    return points


def _close_ring(ring: list[list[float]]) -> list[list[float]]:
    """Ensure ring is closed (first point equals last point)."""
    if len(ring) < 2:
        return ring
    first = ring[0]
    last = ring[-1]
    if first[0] != last[0] or first[1] != last[1]:
        return ring + [first]
    return ring


def _kml_placemarks_to_geojson(root: ET.Element) -> dict | None:
    """Extract polygon(s) from KML root and return GeoJSON Polygon or MultiPolygon."""
    polygons = []

    def find_polygons(elem: ET.Element) -> None:
        # Handle both namespaced and non-namespaced tags
        tag = elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag
        if tag == 'Polygon':
            for coord_elem in elem.iter():
                ctag = coord_elem.tag.split('}')[-1] if '}' in coord_elem.tag else coord_elem.tag
                if ctag == 'coordinates' and coord_elem.text:
                    ring = _parse_kml_coordinates(coord_elem.text)
                    if len(ring) >= 3:
                        polygons.append([_close_ring(ring)])
                    break
        elif tag == 'MultiGeometry':
            for child in elem:
                find_polygons(child)
        elif tag in ('Placemark', 'Document', 'Folder', 'kml'):
            for child in elem:
                find_polygons(child)

    find_polygons(root)

    if not polygons:
        return None
    if len(polygons) == 1:
        return {'type': 'Polygon', 'coordinates': polygons[0]}
    # MultiPolygon: each polygon is one element with one exterior ring
    return {'type': 'MultiPolygon', 'coordinates': polygons}


def parse_kml(content: bytes) -> dict | None:
    """Parse KML bytes and return GeoJSON boundary or None."""
    try:
        root = ET.fromstring(content)
        return _kml_placemarks_to_geojson(root)
    except ET.ParseError:
        return None


def parse_kmz(content: bytes) -> dict | None:
    """Parse KMZ (zip with KML inside) and return GeoJSON boundary or None."""
    try:
        with zipfile.ZipFile(io.BytesIO(content), 'r') as zf:
            for name in zf.namelist():
                if name.lower().endswith('.kml'):
                    with zf.open(name) as f:
                        return parse_kml(f.read())
    except (zipfile.BadZipFile, KeyError, OSError):
        pass
    return None


def parse_shapefile_zip(content: bytes) -> dict | None:
    """Parse zip containing .shp + .prj (+ .shx, .dbf), reproject to WGS84, return GeoJSON."""
    try:
        import shapefile
        from pyproj import Transformer
    except ImportError:
        return None

    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            with zipfile.ZipFile(io.BytesIO(content), 'r') as zf:
                zf.extractall(tmpdir)

            shp_path = None
            prj_path = None
            for name in os.listdir(tmpdir):
                lower = name.lower()
                if lower.endswith('.shp'):
                    shp_path = os.path.join(tmpdir, name)
                elif lower.endswith('.prj'):
                    prj_path = os.path.join(tmpdir, name)

            if not shp_path:
                return None

            reader = shapefile.Reader(shp_path)
            shapes = reader.shapes()

            if not shapes:
                return None

            # Get source CRS from .prj if present
            transformer = None
            if prj_path and os.path.isfile(prj_path):
                with open(prj_path, 'r') as f:
                    prj_wkt = f.read()
                try:
                    from pyproj import CRS
                    src_crs = CRS.from_wkt(prj_wkt)
                    dst_crs = CRS.from_epsg(4326)
                    transformer = Transformer.from_crs(src_crs, dst_crs, always_xy=True)
                except Exception:
                    pass

            def transform(x: float, y: float) -> list[float]:
                if transformer:
                    lon, lat = transformer.transform(x, y)
                    return [lon, lat]
                return [float(x), float(y)]

            polygons = []
            for shape in shapes:
                if shape.shapeType not in (5, 15):  # POLYGON, POLYGONZ
                    continue
                parts = list(shape.parts) + [len(shape.points)]
                for i in range(len(parts) - 1):
                    ring = [
                        transform(shape.points[j][0], shape.points[j][1])
                        for j in range(parts[i], parts[i + 1])
                    ]
                    if len(ring) >= 3:
                        polygons.append([_close_ring(ring)])

            if not polygons:
                return None
            if len(polygons) == 1:
                return {'type': 'Polygon', 'coordinates': polygons[0]}
            return {'type': 'MultiPolygon', 'coordinates': polygons}
    except Exception:
        return None


def file_to_geojson_boundary(file) -> dict:
    """
    Convert uploaded file to GeoJSON boundary (Polygon or MultiPolygon, WGS84 [lng, lat]).
    file: Django UploadedFile or file-like with .name and .read().
    Raises ValueError on invalid/unsupported file or parse failure.
    """
    name = getattr(file, 'name', '') or ''
    content = file.read() if hasattr(file, 'read') else file

    if not content:
        raise ValueError('File is empty')

    max_size = 10 * 1024 * 1024  # 10 MB
    if len(content) > max_size:
        raise ValueError('File too large (max 10 MB)')

    ext = os.path.splitext(name)[1].lower()
    geojson = None

    if ext == '.kmz':
        geojson = parse_kmz(content)
    elif ext == '.kml':
        geojson = parse_kml(content)
    elif ext == '.zip':
        geojson = parse_shapefile_zip(content)
    else:
        raise ValueError('Unsupported file type. Use .kmz, .kml, or .zip (shapefile).')

    if not geojson:
        raise ValueError('No polygon boundary found in file or failed to parse.')
    return geojson
