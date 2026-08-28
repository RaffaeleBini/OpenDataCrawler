# -*- coding: utf-8 -*-
"""
Harvester a medida para la API JSON de data.gouv.fr (plataforma "udata",
Francia).

data.gouv.fr no es CKAN ni expone DCAT/RDF por dataset (comprobado: tanto
`{slug}.rdf` como `/api/1/datasets/{id}.rdf` devuelven 404 tras redirigir),
pero sí una API REST propia con una URL por dataset, por ejemplo:

    https://www.data.gouv.fr/api/1/datasets/{id}/

La URL de la fuente de harvesting (harvest_source.url) debe ser esa URL
completa de un dataset concreto. A diferencia de la OMS, esta API ya trae
URLs de descarga reales con su formato correcto en el campo "resources", así
que no hace falta generar ni subir ningún fichero: se mapean tal cual.
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


class DGFHarvester(HarvesterBase):
    """Harvester para datasets individuales de la API de data.gouv.fr (udata)."""

    def info(self):
        return {
            "name": "dgf",
            "title": "data.gouv.fr (Francia)",
            "description": (
                "Importa un dataset de la API de data.gouv.fr (plataforma "
                "udata) como un dataset de CKAN, reutilizando tal cual sus "
                "recursos de descarga (URL y formato ya vienen dados por "
                "la fuente)."
            ),
            "form_config_interface": "Text",
        }

    def gather_stage(self, harvest_job):
        log.debug("DGFHarvester gather_stage for job: %r", harvest_job.id)
        source_url = harvest_job.source.url.strip()

        obj = HarvestObject(guid=source_url, job=harvest_job)
        obj.save()
        return [obj.id]

    def fetch_stage(self, harvest_object):
        log.debug("DGFHarvester fetch_stage for object: %r", harvest_object.id)
        url = harvest_object.guid
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
        except requests.RequestException as e:
            self._save_object_error(
                "Error accediendo a %s: %s" % (url, e), harvest_object, "Fetch"
            )
            return False

        harvest_object.content = response.text
        harvest_object.save()
        return True

    def import_stage(self, harvest_object):
        log.debug("DGFHarvester import_stage for object: %r", harvest_object.id)
        if not harvest_object.content:
            self._save_object_error(
                "Sin contenido para procesar", harvest_object, "Import"
            )
            return False

        try:
            payload = json.loads(harvest_object.content)
        except ValueError as e:
            self._save_object_error(
                "JSON no válido: %s" % e, harvest_object, "Import"
            )
            return False

        raw_resources = payload.get("resources")
        if not isinstance(raw_resources, list) or not raw_resources:
            self._save_object_error(
                "Formato de respuesta inesperado (esperaba un objeto con "
                "una lista 'resources' no vacía)",
                harvest_object,
                "Import",
            )
            return False

        source = harvest_object.source
        title = source.title or payload.get("title") or "Dataset de data.gouv.fr"
        origin_url = payload.get("page") or harvest_object.guid
        notes = (
            "Dataset importado automáticamente de la API de data.gouv.fr "
            "(plataforma udata, Francia).\n\n%s\n\nFuente original: %s"
        ) % (payload.get("description") or "", origin_url)

        resources = []
        for r in raw_resources:
            url = r.get("url")
            if not url:
                continue
            fmt = (r.get("format") or "").upper()
            resources.append({
                "url": url,
                "format": fmt,
                "name": r.get("title") or fmt or "Datos",
            })

        # HarvestSource no tiene un atributo owner_org propio: cada fuente
        # de harvesting es en realidad un Package de tipo "harvest" con el
        # mismo id.
        owner_org = model.Package.get(source.id).owner_org

        previous = (
            model.Session.query(HarvestObject)
            .filter(HarvestObject.guid == harvest_object.guid)
            .filter(HarvestObject.current == True)  # noqa: E712
            .filter(HarvestObject.id != harvest_object.id)
            .first()
        )
        package_id = previous.package_id if previous and previous.package_id else str(uuid.uuid4())

        package_dict = {
            "id": package_id,
            "name": self._gen_new_name(title),
            "title": title,
            "notes": notes,
            "owner_org": owner_org,
            "resources": resources,
            "extras": [
                {"key": "fonte", "value": "data.gouv.fr (Francia)"},
                {"key": "harvest_source_title", "value": source.title},
            ],
        }

        return self._create_or_update_package(
            package_dict, harvest_object, package_dict_form="package_show"
        )
