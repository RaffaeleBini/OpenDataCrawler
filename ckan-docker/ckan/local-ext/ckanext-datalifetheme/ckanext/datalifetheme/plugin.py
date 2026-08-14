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
import os

from flask import Blueprint, request

import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
from ckanext.harvest.logic.auth import user_is_sysadmin


_DIRECTORY_PATH = os.path.join(
    os.path.dirname(__file__), "data", "catalog_directory.json"
)


def _load_directory():
    with open(_DIRECTORY_PATH, encoding="utf-8") as f:
        return json.load(f)


def get_directory_paises():
    directorio = _load_directory()
    return sorted({d["pais"] for d in directorio})


def get_directory_sectores():
    directorio = _load_directory()
    return sorted({s for d in directorio for s in d["sectores"]})


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
        }
