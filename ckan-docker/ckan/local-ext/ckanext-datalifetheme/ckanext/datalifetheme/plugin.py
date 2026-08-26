# -*- coding: utf-8 -*-
"""
Personalizacion DATAlife para el portal:

1. Logo de DATAlife en la cabecera (en vez del logo de CKAN), con un aviso
   "Powered by CKAN" debajo, y un enlace directo para el equipo tecnico a
   "Anadir fuente de datos" (el formulario ya existente de ckanext-harvest
   en /harvest/new).
2. El formulario para anadir una fuente de datos (harvest_source_create)
   queda restringido a sysadmins, en vez de a cualquier persona con permiso
   de crear datasets en alguna organizacion (que es el comportamiento por
   defecto de ckanext-harvest).
3. Un directorio curado de catalogos de datos abiertos (mundial, por pais
   y sector) con una mascara de filtrado, para decidir que fuentes conectar
   antes de darlas de alta con el formulario del punto 2.
"""

from __future__ import absolute_import

import json
import logging
import os
from urllib.parse import urlparse

import requests
from flask import Blueprint, redirect, request

import ckan.lib.helpers as h
import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
from ckanext.harvest.logic.auth import user_is_sysadmin

log = logging.getLogger(__name__)


_DIRECTORY_PATH = os.path.join(
    os.path.dirname(__file__), "data", "catalog_directory.json"
)

# El backend de CKAN llama a Metabase por la red interna de Docker (comparten
# la red "dbnet"), no por el puerto publicado al host.
_METABASE_INTERNAL_URL = os.environ.get("METABASE_INTERNAL_URL", "http://metabase:3000")
_METABASE_API_KEY = os.environ.get("METABASE_API_KEY")
_METABASE_DATASTORE_DB_NAME = "Catálogo DATAlife (DataStore CKAN)"

# Taxonomía completa de sectores/cadenas de valor. Es la fuente única para
# el desplegable de sector (portada y /explorar-catalogos) y para las
# etiquetas legibles: así no hace falta duplicar esta lista en cada
# plantilla ni esperar a que un catálogo la use para que aparezca como
# opción de filtro.
SECTOR_LABELS = {
    "general": "General / todos los sectores",
    # Cadenas de valor originales de DATAlife
    "agro-mar-alimentacion": "Agro-Mar-Alimentación",
    "forestal-madera": "Forestal-Madera",
    "salud-cuidados": "Salud-Cuidados",
    "biotecnologia": "Biotecnología",
    # Ampliación a cualquier sector
    "medio-ambiente-clima": "Medio Ambiente y Clima",
    "energia": "Energía",
    "transporte-movilidad": "Transporte y Movilidad",
    "ciencia-tecnologia-id": "Ciencia, Tecnología e I+D",
    "economia-finanzas": "Economía y Finanzas Públicas",
    "educacion": "Educación",
    "cultura-turismo": "Cultura y Turismo",
    "vivienda-urbanismo": "Vivienda y Urbanismo",
    "gobierno-sector-publico": "Gobierno y Sector Público",
    "demografia-sociedad": "Demografía y Sociedad",
}


def _load_directory():
    with open(_DIRECTORY_PATH, encoding="utf-8") as f:
        return json.load(f)


def get_directory_paises():
    directorio = _load_directory()
    return sorted({d["pais"] for d in directorio})


def get_directory_sectores():
    # "general" siempre primero; el resto, alfabético por etiqueta legible.
    keys = [k for k in SECTOR_LABELS if k != "general"]
    keys.sort(key=lambda k: SECTOR_LABELS[k])
    return ["general"] + keys


def get_sector_labels():
    return SECTOR_LABELS


def _url_host(url):
    """Dominio de una URL, sin 'www.' y en minúsculas (cadena vacía si no hay)."""
    try:
        host = (urlparse(url).hostname or "").lower()
    except ValueError:
        return ""
    return host[4:] if host.startswith("www.") else host


def _hosts_match(host_a, host_b):
    if not host_a or not host_b:
        return False
    return (
        host_a == host_b
        or host_a.endswith("." + host_b)
        or host_b.endswith("." + host_a)
    )


def _find_harvest_sources_for_host(host):
    """Fuentes de harvesting (ckanext-harvest) cuya URL apunta al mismo dominio."""
    sources = toolkit.get_action("harvest_source_list")(
        {"ignore_auth": True}, {}
    )
    return [s for s in sources if _hosts_match(_url_host(s.get("url", "")), host)]


def _packages_for_harvest_source(source_id):
    """Datasets ya recolectados por una fuente de harvesting concreta."""
    result = toolkit.get_action("package_search")(
        {"ignore_auth": True},
        {
            "fq": "harvest_source_id:{}".format(source_id),
            "rows": 1000,
            "include_private": True,
        },
    )
    return result.get("results", [])


def _resource_is_datapusher_eligible(resource):
    """Mismo criterio que usa CKAN al disparar la carga automática al DataStore.

    Nota: algunas fuentes DCAT-AP (p. ej. GovData/Alemania) no guardan el
    formato como "csv" o "xls", sino como la URI completa del vocabulario
    europeo de tipos de fichero (p. ej. "http://publications.europa.eu/
    resource/authority/file-type/XLS"). Se probó a normalizar esa URI antes
    de comparar, pero el propio `datapusher` usa el campo `format` tal cual
    para detectar el tipo de fichero (vía `messytables`) y falla igual al
    procesar el recurso aunque se le envíe — así que aquí se compara el
    valor exacto, igual que CKAN, y esos recursos se marcan como "no
    soportado" en vez de encolar un envío que sabemos que va a fallar.
    """
    fmt = (resource.get("format") or "").strip().lower()
    if not fmt:
        return False
    supported = [
        f.lower() for f in toolkit.aslist(toolkit.config.get("ckan.datapusher.formats", []))
    ]
    return fmt in supported


def _metabase_sync_datastore():
    """Sincroniza en caliente la base del DataStore dentro de Metabase.

    Devuelve (ok, mensaje_de_aviso). mensaje_de_aviso es None si todo fue bien.
    """
    if not _METABASE_API_KEY:
        return False, toolkit._(
            "No hay una clave de API de Metabase configurada; las tablas "
            "nuevas tardarán en aparecer hasta la siguiente sincronización "
            "automática de Metabase."
        )
    headers = {"x-api-key": _METABASE_API_KEY}
    try:
        resp = requests.get(
            _METABASE_INTERNAL_URL + "/api/database", headers=headers, timeout=10
        )
        resp.raise_for_status()
        payload = resp.json()
        databases = payload.get("data", payload) if isinstance(payload, dict) else payload
        db_id = next(
            (db.get("id") for db in databases if db.get("name") == _METABASE_DATASTORE_DB_NAME),
            None,
        )
        if db_id is None:
            return False, toolkit._(
                "No se encontró en Metabase la base de datos conectada al "
                "DataStore; sincronízala manualmente desde Metabase."
            )
        sync_resp = requests.post(
            "{}/api/database/{}/sync_schema".format(_METABASE_INTERNAL_URL, db_id),
            headers=headers,
            timeout=15,
        )
        sync_resp.raise_for_status()
        return True, None
    except requests.RequestException as exc:
        log.warning("No se pudo sincronizar Metabase: %s", exc)
        return False, toolkit._(
            "Los recursos se enviaron igualmente, pero no se pudo contactar "
            "con Metabase para sincronizar (comprueba que el contenedor esté "
            "arrancado)."
        )


def _send_entry_to_metabase(entry):
    """Carga al DataStore los recursos aptos de una fuente ya conectada, y
    sincroniza Metabase. Devuelve (contadores, mensaje_de_aviso_o_None)."""
    counts = {"enviados": 0, "ya_cargados": 0, "no_soportados": 0, "errores": 0}

    host = _url_host(entry.get("url_catalogo", ""))
    if not host:
        return counts, toolkit._("No se pudo determinar el dominio de esta fuente.")

    sources = _find_harvest_sources_for_host(host)
    if not sources:
        return counts, toolkit._(
            "No se encontró ninguna fuente de harvesting conectada para este dominio."
        )

    context = {"user": toolkit.g.user}
    seen_resources = set()
    for source in sources:
        for pkg in _packages_for_harvest_source(source["id"]):
            for res in pkg.get("resources", []):
                res_id = res.get("id")
                if not res_id or res_id in seen_resources:
                    continue
                seen_resources.add(res_id)

                if res.get("datastore_active"):
                    counts["ya_cargados"] += 1
                    continue
                if not _resource_is_datapusher_eligible(res):
                    counts["no_soportados"] += 1
                    continue
                try:
                    toolkit.get_action("datapusher_submit")(
                        dict(context), {"resource_id": res_id}
                    )
                    counts["enviados"] += 1
                except Exception as exc:  # noqa: BLE001 - se informa, no se interrumpe el resto
                    log.warning("No se pudo enviar el recurso %s a datapusher: %s", res_id, exc)
                    counts["errores"] += 1

    warning = None
    if counts["enviados"]:
        _, warning = _metabase_sync_datastore()
    return counts, warning


datalife_explorer = Blueprint("datalife_explorer", __name__)


@datalife_explorer.route("/explorar-catalogos")
def explorar_catalogos():
    directorio = _load_directory()

    pais_sel = request.args.get("pais", "").strip()
    sector_sel = request.args.get("sector", "").strip()

    paises = get_directory_paises()
    sectores = get_directory_sectores()

    resultados = directorio
    if pais_sel:
        resultados = [d for d in resultados if d["pais"] == pais_sel]
    if sector_sel:
        resultados = [d for d in resultados if sector_sel in d["sectores"]]

    return toolkit.render(
        "explorar_catalogos.html",
        extra_vars={
            "directorio": resultados,
            "paises": paises,
            "sectores": sectores,
            "pais_sel": pais_sel,
            "sector_sel": sector_sel,
            "total": len(directorio),
            "total_filtrado": len(resultados),
        },
    )


@datalife_explorer.route("/explorar-catalogos/enviar-a-metabase", methods=["POST"])
def enviar_a_metabase():
    if not getattr(toolkit.g, "userobj", None) or not toolkit.g.userobj.sysadmin:
        toolkit.abort(
            403,
            toolkit._(
                "Solo las personas administradoras del sistema pueden hacer esto."
            ),
        )

    nombre = request.form.get("nombre", "")
    entry = next((d for d in _load_directory() if d["nombre"] == nombre), None)

    if not entry:
        h.flash_error(toolkit._("No se encontró esa fuente en el directorio."))
    elif not entry.get("ya_conectado"):
        h.flash_error(toolkit._("Esta fuente todavía no está conectada al catálogo."))
    else:
        counts, warning = _send_entry_to_metabase(entry)
        resumen = toolkit._(
            "{enviados} recurso(s) enviado(s) a Metabase; {ya_cargados} ya "
            "estaban cargados; {no_soportados} con formato no soportado, "
            "omitido(s)."
        ).format(**counts)
        if counts["errores"]:
            resumen += " " + toolkit._("{errores} fallaron al enviarse.").format(**counts)
        h.flash_success(resumen)
        if warning:
            h.flash_notice(warning)

    return redirect(
        request.referrer or toolkit.url_for("datalife_explorer.explorar_catalogos")
    )


@toolkit.chained_auth_function
def _restrict_harvest_source_create_to_sysadmin(next_auth, context, data_dict=None):
    # La acción harvest_source_create no comprueba permisos por sí misma:
    # delega por completo en package_create (fija data_dict['type'] a
    # "harvest" y llama a package_create), tal y como indica su propio
    # docstring. Por eso hay que interceptar package_create aquí, no
    # harvest_source_create (esa función de auth existe pero nunca llega a
    # invocarse en la práctica). Solo actuamos cuando el tipo es "harvest";
    # para cualquier otro dataset, delegamos en el comportamiento normal.
    if data_dict and data_dict.get("type") == "harvest":
        if user_is_sysadmin(context):
            return {"success": True}
        return {
            "success": False,
            "msg": toolkit._(
                "Solo las personas administradoras del sistema pueden "
                "añadir fuentes de datos."
            ),
        }
    return next_auth(context, data_dict)


class DatalifeThemePlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IAuthFunctions)
    plugins.implements(plugins.IBlueprint)
    plugins.implements(plugins.ITemplateHelpers)

    # IConfigurer

    def update_config(self, config_):
        toolkit.add_template_directory(config_, "templates")
        toolkit.add_public_directory(config_, "public")

    # IAuthFunctions

    def get_auth_functions(self):
        return {
            "package_create": _restrict_harvest_source_create_to_sysadmin,
        }

    # IBlueprint

    def get_blueprint(self):
        return datalife_explorer

    # ITemplateHelpers

    def get_helpers(self):
        return {
            "datalife_directory_paises": get_directory_paises,
            "datalife_directory_sectores": get_directory_sectores,
            "datalife_sector_labels": get_sector_labels,
        }
