# -*- coding: utf-8 -*-
"""
Harvester a medida para la API OData del Global Health Observatory (GHO) de
la Organizacion Mundial de la Salud (OMS).

La OMS no ofrece catalogo CKAN ni DCAT, sino una API OData publica y sin
autenticacion (ghoapi.azureedge.net) donde cada indicador es una tabla en
JSON, por ejemplo:

    https://ghoapi.azureedge.net/api/WHOSIS_000001

La URL de la fuente de harvesting (harvest_source.url) debe ser esa URL
completa de un indicador concreto. A diferencia del INE, esta API no ofrece
ninguna variante CSV real (el parametro "$format=csv" se ignora en la
practica y sigue devolviendo JSON), asi que este harvester genera el CSV el
mismo, a partir de la respuesta JSON, y lo sube como fichero propio a CKAN
para que sea cargable al DataStore (y por tanto visualizable en el cuadro de
mando). Si esa subida de fichero fallara, se cae de vuelta al patron simple
de IGE/INE: un unico recurso JSON con la URL real de la OMS.
"""

from __future__ import absolute_import

import csv
import io
import json
import logging
import uuid

import requests
from werkzeug.datastructures import FileStorage

from ckan import model
import ckan.plugins.toolkit as toolkit

from ckanext.harvest.model import HarvestObject
from ckanext.harvest.harvesters.base import HarvesterBase

log = logging.getLogger(__name__)


class GHOHarvester(HarvesterBase):
    """Harvester para indicadores individuales de la API OData de la OMS (GHO)."""

    def info(self):
        return {
            "name": "gho",
            "title": "OMS (Global Health Observatory)",
            "description": (
                "Importa un indicador de la API OData del Global Health "
                "Observatory de la OMS como un dataset de CKAN, con un "
                "recurso JSON (la fuente original) y un CSV generado a "
                "partir de esos mismos datos."
            ),
            "form_config_interface": "Text",
        }

    def gather_stage(self, harvest_job):
        log.debug("GHOHarvester gather_stage for job: %r", harvest_job.id)
        source_url = harvest_job.source.url.strip()

        obj = HarvestObject(guid=source_url, job=harvest_job)
        obj.save()
        return [obj.id]

    def fetch_stage(self, harvest_object):
        log.debug("GHOHarvester fetch_stage for object: %r", harvest_object.id)
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

    def _build_csv_bytes(self, rows):
        buffer = io.StringIO()
        fieldnames = list(rows[0].keys())
        writer = csv.DictWriter(buffer, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
        return buffer.getvalue().encode("utf-8")

    def _package_dict(self, harvest_object, rows, source, owner_org):
        json_url = harvest_object.guid
        title = source.title or "Indicador de la OMS"
        notes = (
            "Indicador importado automáticamente de la API OData del "
            "Global Health Observatory (GHO) de la Organización Mundial de "
            "la Salud (OMS).\n\n"
            "Número de filas incluidas: %d (todos los países y años "
            "disponibles). No hay desglose por Galicia en esta fuente: "
            "los datos son a nivel de país.\n\n"
            "Fuente original: %s"
        ) % (len(rows), json_url)

        resources = [
            {"url": json_url, "format": "JSON", "name": "Datos (JSON, fuente original)"},
        ]

        previous = (
            model.Session.query(HarvestObject)
            .filter(HarvestObject.guid == harvest_object.guid)
            .filter(HarvestObject.current == True)  # noqa: E712
            .filter(HarvestObject.id != harvest_object.id)
            .first()
        )
        package_id = previous.package_id if previous and previous.package_id else str(uuid.uuid4())

        return {
            "id": package_id,
            "name": self._gen_new_name(title),
            "title": title,
            "notes": notes,
            "owner_org": owner_org,
            "resources": resources,
            "extras": [
                {"key": "fonte", "value": "OMS - Global Health Observatory"},
                {"key": "harvest_source_title", "value": source.title},
            ],
        }

    def import_stage(self, harvest_object):
        log.debug("GHOHarvester import_stage for object: %r", harvest_object.id)
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

        rows = payload.get("value") if isinstance(payload, dict) else None
        if not isinstance(rows, list) or not rows:
            self._save_object_error(
                "Formato de respuesta inesperado (esperaba un objeto con "
                "una lista 'value' no vacía)",
                harvest_object,
                "Import",
            )
            return False

        source = harvest_object.source
        # HarvestSource no tiene un atributo owner_org propio: cada fuente
        # de harvesting es en realidad un Package de tipo "harvest" con el
        # mismo id.
        owner_org = model.Package.get(source.id).owner_org

        # Primero se crea/actualiza el dataset solo con el recurso JSON (el
        # mismo patrón, ya probado, de IGE/INE). Intentar subir el CSV en el
        # mismo package_dict que gestiona _create_or_update_package no
        # funciona: esa función serializa el dict internamente (para
        # detectar cambios) y un objeto FileStorage no es serializable, lo
        # que además puede dejar la sesión de base de datos en un estado
        # inconsistente a media transacción. Por eso el CSV se sube después,
        # como un paso aparte y aislado, sobre un dataset ya guardado.
        package_dict = self._package_dict(harvest_object, rows, source, owner_org)
        result = self._create_or_update_package(
            package_dict, harvest_object, package_dict_form="package_show"
        )
        if not result:
            return result

        try:
            self._upsert_csv_resource(package_dict["id"], rows)
        except Exception as exc:  # noqa: BLE001 - el CSV es un extra, no crítico
            log.warning(
                "El dataset se creó correctamente, pero no se pudo añadir "
                "el recurso CSV generado: %s",
                exc,
            )

        return result

    def _upsert_csv_resource(self, package_id, rows):
        context = {
            "model": model,
            "session": model.Session,
            "user": self._get_user_name(),
            "ignore_auth": True,
        }
        pkg = toolkit.get_action("package_show")(dict(context), {"id": package_id})
        existing = next(
            (r for r in pkg.get("resources", []) if r.get("name") == "Datos (CSV)"),
            None,
        )

        csv_bytes = self._build_csv_bytes(rows)
        upload = FileStorage(
            stream=io.BytesIO(csv_bytes),
            filename="datos.csv",
            content_type="text/csv",
        )

        if existing:
            toolkit.get_action("resource_update")(
                dict(context),
                {"id": existing["id"], "upload": upload, "format": "CSV"},
            )
        else:
            toolkit.get_action("resource_create")(
                dict(context),
                {
                    "package_id": package_id,
                    "name": "Datos (CSV)",
                    "format": "CSV",
                    "upload": upload,
                },
            )
