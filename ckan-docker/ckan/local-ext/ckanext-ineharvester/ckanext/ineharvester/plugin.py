# -*- coding: utf-8 -*-
"""
Harvester a medida para la API JSON del INE (Instituto Nacional de
Estadistica), conocida como Tempus3.

El INE no ofrece catalogo CKAN ni DCAT, sino una API REST propia
(servicios.ine.es/wstempus) que devuelve cada tabla como una lista de
series JSON, por ejemplo:

    https://servicios.ine.es/wstempus/js/ES/DATOS_TABLA/33387?nult=10

La URL de la fuente de harvesting (harvest_source.url) debe ser esa URL
completa de una tabla concreta. A diferencia de la API del IGE, el INE
declara correctamente UTF-8 y no ofrece una variante CSV real para esta
funcion (el parametro "formato=csv" se ignora en la practica), asi que
este harvester crea un dataset con un unico recurso JSON.
"""

from __future__ import absolute_import

import json
import logging
import uuid

import requests

from ckan import model

from ckanext.harvest.model import HarvestObject
from ckanext.harvest.harvesters.base import HarvesterBase

log = logging.getLogger(__name__)


class INEHarvester(HarvesterBase):
    """Harvester para tablas individuais da API Tempus3 do INE."""

    def info(self):
        return {
            "name": "ine",
            "title": "INE (Instituto Nacional de Estadística)",
            "description": (
                "Importa unha táboa da API Tempus3 do INE (formato JSON) "
                "como un dataset de CKAN."
            ),
            "form_config_interface": "Text",
        }

    def gather_stage(self, harvest_job):
        log.debug("INEHarvester gather_stage for job: %r", harvest_job.id)
        source_url = harvest_job.source.url.strip()

        obj = HarvestObject(guid=source_url, job=harvest_job)
        obj.save()
        return [obj.id]

    def fetch_stage(self, harvest_object):
        log.debug("INEHarvester fetch_stage for object: %r", harvest_object.id)
        url = harvest_object.guid
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
        except requests.RequestException as e:
            self._save_object_error(
                "Erro accedendo a %s: %s" % (url, e), harvest_object, "Fetch"
            )
            return False

        # O INE declara UTF-8 correctamente na cabeceira, a diferenza do IGE.
        harvest_object.content = response.text
        harvest_object.save()
        return True

    def import_stage(self, harvest_object):
        log.debug("INEHarvester import_stage for object: %r", harvest_object.id)
        if not harvest_object.content:
            self._save_object_error(
                "Sen contido para procesar", harvest_object, "Import"
            )
            return False

        try:
            series = json.loads(harvest_object.content)
        except ValueError as e:
            self._save_object_error(
                "JSON non válido: %s" % e, harvest_object, "Import"
            )
            return False

        if not isinstance(series, list):
            self._save_object_error(
                "Formato de resposta inesperado (agardaba unha lista de series)",
                harvest_object,
                "Import",
            )
            return False

        series_names = [s.get("Nombre", "").strip() for s in series if s.get("Nombre")]
        json_url = harvest_object.guid

        source = harvest_object.source
        title = source.title or "Táboa do INE"
        notes = (
            "Táboa importada automaticamente da API Tempus3 do Instituto "
            "Nacional de Estadística (INE).\n\n"
            "Número de series incluídas: %d\n"
            "Primeiras series: %s\n\n"
            "Fonte orixinal: %s"
        ) % (
            len(series),
            ", ".join(series_names[:8]) + ("…" if len(series_names) > 8 else ""),
            json_url,
        )

        # Reutiliza o id de paquete dun harvest anterior co mesmo guid, se
        # existe, para actualizar en vez de duplicar; se non, xera un novo.
        previous = (
            model.Session.query(HarvestObject)
            .filter(HarvestObject.guid == harvest_object.guid)
            .filter(HarvestObject.current == True)  # noqa: E712
            .filter(HarvestObject.id != harvest_object.id)
            .first()
        )
        package_id = previous.package_id if previous and previous.package_id else str(uuid.uuid4())

        # HarvestSource non ten un atributo owner_org propio: cada fonte de
        # harvesting é en realidade un Package de tipo "harvest" co mesmo id.
        source_package = model.Package.get(source.id)

        package_dict = {
            "id": package_id,
            "name": self._gen_new_name(title),
            "title": title,
            "notes": notes,
            "owner_org": source_package.owner_org,
            "resources": [
                {"url": json_url, "format": "JSON", "name": "Datos (JSON)"},
            ],
            "extras": [
                {"key": "fonte", "value": "Instituto Nacional de Estadística (INE)"},
                {"key": "harvest_source_title", "value": source.title},
            ],
        }

        return self._create_or_update_package(
            package_dict, harvest_object, package_dict_form="package_show"
        )
