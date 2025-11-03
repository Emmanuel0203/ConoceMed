import os
import requests
from functools import lru_cache

GOOGLE_KEY = os.environ.get('GOOGLE_GEOCODING_API_KEY')
SKIP_SERVER_GEOCODE = os.environ.get('SKIP_SERVER_GEOCODE', '').lower() in ('1', 'true', 'yes')


@lru_cache(maxsize=1024)
def _google_geocode(address, region='CO', components: str = None):
    if not GOOGLE_KEY:
        return {'ok': False, 'error': 'No API key configured for Google Geocoding'}

    url = 'https://maps.googleapis.com/maps/api/geocode/json'
    params = {'key': GOOGLE_KEY, 'region': region}
    if address:
        params['address'] = address
    if components:
        params['components'] = components
    try:
        resp = requests.get(url, params=params, timeout=5)
    except requests.RequestException as e:
        return {'ok': False, 'error': str(e)}

    if resp.status_code != 200:
        return {'ok': False, 'error': f'HTTP {resp.status_code}'}

    data = resp.json()
    status = data.get('status')
    if status != 'OK':
        return {'ok': False, 'error': f'Google status: {status}', 'raw': data}

    results = data.get('results', [])
    if not results:
        return {'ok': False, 'error': 'No results', 'raw': data}

    # pick best result (first)
    best = results[0]
    loc = best.get('geometry', {}).get('location', {})

    # simple confidence heuristic
    types = best.get('types', [])
    confidence = 0.5
    if 'street_address' in types or 'premise' in types:
        confidence = 0.95
    elif 'route' in types:
        confidence = 0.7
    elif 'locality' in types:
        confidence = 0.6

    return {
        'ok': True,
        'lat': loc.get('lat'),
        'lng': loc.get('lng'),
        'formatted_address': best.get('formatted_address'),
        'types': types,
        'confidence': confidence,
        'raw': best,
    }


@lru_cache(maxsize=512)
def geocode(address, region='CO'):
    """Try Google Geocoding first. Returns structured dict with ok flag."""
    if SKIP_SERVER_GEOCODE:
        # Explicit skip requested by environment: return non-fatal result indicating skip
        return {'ok': False, 'error': 'Server geocoding skipped by SKIP_SERVER_GEOCODE'}
    return _google_geocode(address, region=region)


def normalize_address(address: str) -> str:
    """Lightweight normalization for common Colombian address abbreviations.
    This helps Google Geocoding match free-text admin input.
    """
    if not address:
        return ''
    a = str(address).strip()
    # Simple replacements (keep it deterministic and safe)
    replacements = [
        ('Cra.', 'Carrera'),
        ('Cra', 'Carrera'),
        ('Cr', 'Carrera'),
        ('Crr', 'Carrera'),
        ('Cl', 'Calle'),
        ('#', '#'),
        (',,', ','),
    ]
    for old, new in replacements:
        a = a.replace(old, new)
    # collapse multiple spaces
    while '  ' in a:
        a = a.replace('  ', ' ')
    return a


def geocode_with_variants(address: str, fkidLocalidad: str = None, api_client_factory=None, region: str = 'CO'):
    """Try multiple address variants to improve geocoding match rate.

    Returns a tuple: (geo_result_or_none, used_variant_string_or_none)
    geo_result_or_none follows the same shape as `geocode` (dict with 'ok').
    """
    address = (address or '').strip()
    if not address:
        return None, None

    # 1) raw
    geo = geocode(address, region=region)
    if geo and geo.get('ok'):
        return geo, address

    # 2) normalized
    norm = normalize_address(address)
    if norm and norm != address:
        geo = geocode(norm, region=region)
        if geo and geo.get('ok'):
            return geo, norm

    # 2b) If no locality provided, try biasing the search to a default locality
    # This helps avoid matches in other cities when user is operating in a known city (e.g., Medellín)
    try:
        from flask import current_app
        default_locality = current_app.config.get('DEFAULT_LOCALITY_NAME') if hasattr(current_app, 'config') else None
    except Exception:
        default_locality = None
    if not fkidLocalidad and default_locality:
        try:
            components = f"locality:{default_locality}|country:{region}"
            geo = _google_geocode(address, region=region, components=components)
            if geo and geo.get('ok'):
                return geo, f"{address} + components:{components}"
            if norm and norm != address:
                geo = _google_geocode(norm, region=region, components=components)
                if geo and geo.get('ok'):
                    return geo, f"{norm} + components:{components}"
        except Exception:
            pass

    # 3) prefer using components for locality if available via API client factory
    if fkidLocalidad and api_client_factory:
        try:
            api_loc = api_client_factory('Localidad')
            loc_resp = api_loc.get_data_by_key('idLocalidad', fkidLocalidad)
            if loc_resp and isinstance(loc_resp, dict):
                datos = loc_resp.get('datos', [])
                if datos:
                    loc_name = datos[0].get('nombre')
                    # Build components string that biases Google search to the locality
                    if loc_name:
                        # Example: components=locality:El Poblado|administrative_area:Antioquia|country:CO
                        components = f"locality:{loc_name}|administrative_area:Antioquia|country:CO"
                        # Try using components-only search first (no free-text ambiguity)
                        geo = geocode('', region=region) if SKIP_SERVER_GEOCODE else _google_geocode('', region=region, components=components)
                        if geo and geo.get('ok'):
                            return geo, f"components:{components}"

                        # Then try address with components
                        try:
                            geo = _google_geocode(address, region=region, components=components)
                            if geo and geo.get('ok'):
                                return geo, f"{address} + components:{components}"
                        except Exception:
                            pass

                        # Also try normalized address with components
                        try:
                            geo = _google_geocode(norm, region=region, components=components)
                            if geo and geo.get('ok'):
                                return geo, f"{norm} + components:{components}"
                        except Exception:
                            pass
        except Exception:
            # ignore locality fetch errors; fall back to other variants
            pass

    # 4) last resort: append city/state
    combo = f"{address}, Medellín, Antioquia"
    geo = geocode(combo, region=region)
    if geo and geo.get('ok'):
        return geo, combo

    # 5) Fallback to Nominatim (OpenStreetMap) if Google failed or not available
    try:
        nom = _nominatim_geocode(address)
        if nom and nom.get('ok'):
            return nom, 'nominatim'
        # try normalized address
        if norm and norm != address:
            nom = _nominatim_geocode(norm)
            if nom and nom.get('ok'):
                return nom, 'nominatim-normalized'
        # try combo
        nom = _nominatim_geocode(combo)
        if nom and nom.get('ok'):
            return nom, 'nominatim-combo'
    except Exception:
        # ignore nominatim errors; final return below will propagate last google result or None
        pass

    return geo, None


def _nominatim_geocode(address: str, timeout: int = 5):
    """Query Nominatim (OpenStreetMap) as a fallback geocoder.

    Note: Nominatim public instance has usage policies and rate limits. Use responsibly.
    """
    if not address:
        return {'ok': False, 'error': 'No address provided for nominatim'}
    url = 'https://nominatim.openstreetmap.org/search'
    params = {'q': address, 'format': 'json', 'limit': 1}
    headers = {'User-Agent': current_app_user_agent()}
    try:
        resp = requests.get(url, params=params, headers=headers, timeout=timeout)
        if resp.status_code != 200:
            return {'ok': False, 'error': f'Nominatim HTTP {resp.status_code}', 'raw': None}
        data = resp.json()
        if not data:
            return {'ok': False, 'error': 'Nominatim: no results', 'raw': data}
        item = data[0]
        return {'ok': True, 'lat': float(item.get('lat')), 'lng': float(item.get('lon')), 'formatted_address': item.get('display_name'), 'raw': item, 'confidence': 0.6}
    except requests.RequestException as e:
        return {'ok': False, 'error': str(e), 'raw': None}


_nominatim_geocode = lru_cache(maxsize=1024)(_nominatim_geocode)


def current_app_user_agent():
    """Return a sensible User-Agent string for geocode requests.

    Avoid importing Flask's current_app here to keep function usable in tests; derive from env if available.
    """
    try:
        from flask import current_app
        app_name = getattr(current_app, 'name', 'ConoceMed')
    except Exception:
        app_name = 'ConoceMed'
    return f"{app_name}/1.0 (+https://example.com)"


def extract_locality_from_google(raw: dict) -> str:
    """Try to extract locality/city from Google Geocoding result 'raw' (first result)."""
    try:
        components = raw.get('address_components', [])
        for comp in components:
            types = comp.get('types', [])
            if 'locality' in types or 'administrative_area_level_2' in types:
                return comp.get('long_name')
        # fallback to administrative_area_level_1
        for comp in components:
            types = comp.get('types', [])
            if 'administrative_area_level_1' in types:
                return comp.get('long_name')
    except Exception:
        pass
    return ''


def extract_locality_from_nominatim(raw: dict) -> str:
    """Try to extract locality from Nominatim 'raw' (item)."""
    try:
        if isinstance(raw, dict):
            # Nominatim may include an 'address' dict with 'city' or 'town' or 'county'
            addr = raw.get('address') or {}
            for key in ('city', 'town', 'village', 'hamlet', 'county'):
                if addr.get(key):
                    return addr.get(key)
            # fallback to display_name parsing
            display = raw.get('display_name', '')
            if display:
                # take first locality-like token
                parts = [p.strip() for p in display.split(',')]
                if parts:
                    return parts[-3] if len(parts) >= 3 else parts[-2] if len(parts) >= 2 else parts[0]
    except Exception:
        pass
    return ''
