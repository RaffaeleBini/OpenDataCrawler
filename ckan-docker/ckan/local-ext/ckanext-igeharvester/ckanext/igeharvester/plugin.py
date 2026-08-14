# -*- coding: utf-8 -*-
"""
Harvester a medida para o Instituto Galego de Estatistica (IGE).

O IGE non ofrece un catalogo CKAN nin DCAT, senon unha API REST propia que
devolve cada taboa como JSON (ou CSV) nun URL fixo, por exemplo:

    https://www.ige.gal/igebdt/igeapi/json/datos/1552/1:0,9912:12,0:1981:1991:2001:2011

A URL da fonte de harvesting (harvest_source.url) debe ser esa URL completa
en formato JSON dunha taboa concreta. Este harvester crea un unico dataset
por fonte, cun recurso JSON e outro CSV (mesma taboa, cambiando o segmento
"json" por "csv" na URL).

Nota de calidade de datos: a API do IGE declara "charset=UTF-8" na cabeceira
Content-Type pero en realidade devolve os bytes en ISO-8859-1; decodificamos
explicitamente en ISO-8859-1 para evitar caracteres corrompidos (mojibake).
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


class IGEHarvester(HarvesterBase):
    """Harvester para taboas individuais da API REST do IGE."""

    def info(self):
        return {
            "name": "ige",
            "title": "IGE (Instituto Galego de Estatística)",
            "description": (
                "Importa unha táboa da API REST do IGE (formato JSON) "
                "como un dataset de CKAN, cos datos dispoñibles tamén en CSV."
            ),
            "form_config_interface": "Text",
        }

    def gather_stage(self, harvest_job):
        log.debug("IGEHarvester gather_stage for job: %r", harvest_job.id)
        source_url = harvest_job.source.url.strip()

        obj = HarvestObject(guid=source_url, job=harvest_job)
        obj.save()
        return [obj.id]

    def fetch_stage(self, harvest_object):
        log.debug("IGEHarvester fetch_stage for object: %r", harvest_object.id)
        url = harvest_object.guid
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
        except requests.RequestException as e:
            self._save_object_error(
                "Erro accedendo a %s: %s" % (url, e), harvest_object, "Fetch"
            )
            return False

        # A API do IGE declara UTF-8 na cabeceira pero devolve ISO-8859-1.
        harvest_object.content = response.content.decode("iso-8859-1")
        harvest_object.save()
        return True

    def import_stage(self, harvest_object):
        log.debug("IGEHarvester import_stage for object: %r", harvest_object.id)
        if not harvest_object.content:
            self._save_object_error(
                "Sen contido para procesar", harvest_object, "Import"
            )
            return False

        try:
            data = json.loads(harvest_object.content)
        except ValueError as e:
            self._save_object_error(
                "JSON non válido: %s" % e, harvest_object, "Import"
            )
            return False

        variables = data.get("variables", [])
        rows = data.get("datos", [])
        json_url = harvest_object.guid
        csv_url = json_url.replace("/igeapi/json/", "/igeapi/csv/")

        source = harvest_object.source
        # HarvestSource non ten un atributo owner_org propio: cada fonte de
        # harvesting é en realidade un Package de tipo "harvest" co mesmo id,
        # e o owner_org vive nese Package.
        source_package = model.Package.get(source.id)
        title = source.title or "Táboa do IGE"
        notes = (
            "Táboa importada automaticamente da API do Instituto Galego de "
            "Estatística (IGE).\n\n"
            "Columnas: %s\n"
            "Número de filas: %d\n\n"
            "Fonte orixinal: %s"
        ) % (", ".join(variables), len(rows), json_url)

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

        package_dict = {
            "id": package_id,
            "name": self._gen_new_name(title),
            "title": title,
            "notes": notes,
            "owner_org": source_package.owner_org,
            "resources": [
                {"url": json_url, "format": "JSON", "name": "Datos (JSON)"},
                {"url": csv_url, "format": "CSV", "name": "Datos (CSV)"},
            ],
            "extras": [
                {"key": "fonte", "value": "Instituto Galego de Estatística (IGE)"},
                {"key": "harvest_source_title", "value": source.title},
            ],
        }

        return self._create_or_update_package(
            package_dict, harvest_object, package_dict_form="package_show"
        )
