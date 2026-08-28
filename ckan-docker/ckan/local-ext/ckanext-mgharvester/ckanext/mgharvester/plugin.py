# -*- coding: utf-8 -*-
"""
Harvester a medida para a API JSON de MeteoGalicia (rede de estacións
meteorolóxicas).

MeteoGalicia non ofrece catálogo CKAN nin DCAT, senón varios servizos JSON
públicos e sen autenticación en servizos.meteogalicia.gal/mgrss/. Este
harvester usa o servizo de datos diarios:

    https://servizos.meteogalicia.gal/mgrss/observacion/datosDiariosEstacionsMeteo.action

que, sen parámetros, devolve o día en curso; admite datIni/dataFin
(dd/MM/yyyy) para un intervalo. Como o obxectivo é un dataset con algo de
profundidade histórica (non só unha foto do momento), este harvester pide
sempre unha fiestra móbil dos últimos 7 días, calculada en cada execución.

A resposta é unha lista de días, cada un cunha lista de estacións, cada
unha cunha lista de medidas (un valor por parámetro meteorolóxico). Igual
que coa OMS, ademais do recurso JSON orixinal, este harvester aplana esa
estrutura aniñada nunha fila por (día, estación, parámetro) e sobe un CSV
xerado, para que sexa cargable no DataStore e visualizable no cadro de
mando.
"""

from __future__ import absolute_import

import csv
import datetime
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


class MGHarvester(HarvesterBase):
    """Harvester para os datos diarios da rede de estacións de MeteoGalicia."""

    def info(self):
        return {
            "name": "mg",
            "title": "MeteoGalicia",
            "description": (
                "Importa os datos diarios dos últimos 7 días da rede de "
                "estacións meteorolóxicas de MeteoGalicia como un dataset "
                "de CKAN, cun recurso JSON (a fonte orixinal) e un CSV "
                "xerado a partir deses mesmos datos."
            ),
            "form_config_interface": "Text",
        }

    def _date_window_url(self, base_url):
        today = datetime.date.today()
        start = today - datetime.timedelta(days=6)
        return "%s?dataIni=%s&dataFin=%s" % (
            base_url,
            start.strftime("%d/%m/%Y"),
            today.strftime("%d/%m/%Y"),
        )

    def gather_stage(self, harvest_job):
        log.debug("MGHarvester gather_stage for job: %r", harvest_job.id)
        source_url = harvest_job.source.url.strip()

        obj = HarvestObject(guid=source_url, job=harvest_job)
        obj.save()
        return [obj.id]

    def fetch_stage(self, harvest_object):
        log.debug("MGHarvester fetch_stage for object: %r", harvest_object.id)
        url = self._date_window_url(harvest_object.guid)
        try:
            response = requests.get(url, timeout=60)
            response.raise_for_status()
        except requests.RequestException as e:
            self._save_object_error(
                "Erro accedendo a %s: %s" % (url, e), harvest_object, "Fetch"
            )
            return False

        harvest_object.content = response.text
        harvest_object.save()
        return True

    def _flatten_rows(self, payload):
        rows = []
        for day in payload.get("listDatosDiarios", []) or []:
            fecha = day.get("data")
            for estacion in day.get("listaEstacions", []) or []:
                base = {
                    "data": fecha,
                    "idEstacion": estacion.get("idEstacion"),
                    "estacion": estacion.get("estacion"),
                    "concello": estacion.get("concello"),
                    "provincia": estacion.get("provincia"),
                    "utmx": estacion.get("utmx"),
                    "utmy": estacion.get("utmy"),
                }
                for medida in estacion.get("listaMedidas", []) or []:
                    row = dict(base)
                    row["codigoParametro"] = medida.get("codigoParametro")
                    row["nomeParametro"] = medida.get("nomeParametro")
                    row["unidade"] = medida.get("unidade")
                    row["valor"] = medida.get("valor")
                    row["lnCodigoValidacion"] = medida.get("lnCodigoValidacion")
                    rows.append(row)
        return rows

    def _build_csv_bytes(self, rows):
        buffer = io.StringIO()
        fieldnames = list(rows[0].keys())
        writer = csv.DictWriter(buffer, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
        return buffer.getvalue().encode("utf-8")

    def _package_dict(self, harvest_object, rows, source, owner_org):
        json_url = self._date_window_url(harvest_object.guid)
        title = source.title or "MeteoGalicia — Datos diarios de estacións meteorolóxicas"
        n_estacions = len({r["idEstacion"] for r in rows})
        n_dias = len({r["data"] for r in rows})
        notes = (
            "Datos diarios da rede de estacións meteorolóxicas de "
            "MeteoGalicia, importados automaticamente do seu servizo JSON "
            "público. Fiestra móbil dos últimos %d días (%d estacións, %d "
            "filas en total): cada execución do harvester actualiza este "
            "dataset cos días máis recentes dispoñibles, non acumula "
            "historial máis alá desa fiestra.\n\n"
            "Cada fila é un valor dun parámetro meteorolóxico (temperatura, "
            "choiva, vento, humidade...) nunha estación e día concretos. "
            "Descrición completa dos códigos de parámetro: "
            "https://www.meteogalicia.gal/web/observacion/parametros\n\n"
            "Fonte orixinal: %s"
        ) % (n_dias, n_estacions, len(rows), json_url)

        resources = [
            {"url": json_url, "format": "JSON", "name": "Datos (JSON, fonte orixinal)"},
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
                {"key": "fonte", "value": "MeteoGalicia"},
                {"key": "harvest_source_title", "value": source.title},
            ],
        }

    def import_stage(self, harvest_object):
        log.debug("MGHarvester import_stage for object: %r", harvest_object.id)
        if not harvest_object.content:
            self._save_object_error(
                "Sen contido para procesar", harvest_object, "Import"
            )
            return False

        try:
            payload = json.loads(harvest_object.content)
        except ValueError as e:
            self._save_object_error(
                "JSON non válido: %s" % e, harvest_object, "Import"
            )
            return False

        rows = self._flatten_rows(payload) if isinstance(payload, dict) else []
        if not rows:
            self._save_object_error(
                "Formato de resposta inesperado (agardaba un obxecto con "
                "'listDatosDiarios' non baleiro)",
                harvest_object,
                "Import",
            )
            return False

        source = harvest_object.source
        # HarvestSource non ten un atributo owner_org propio: cada fonte de
        # harvesting é en realidade un Package de tipo "harvest" co mesmo id.
        owner_org = model.Package.get(source.id).owner_org

        # Mesmo patrón xa probado coa OMS: primeiro créase/actualízase o
        # dataset só co recurso JSON, e só despois, como paso aparte e
        # illado, súbese o CSV xerado — mesturalo no mesmo package_dict que
        # xestiona _create_or_update_package rompe (FileStorage non é
        # serializable) e pode deixar a sesión de base de datos a medias.
        package_dict = self._package_dict(harvest_object, rows, source, owner_org)
        result = self._create_or_update_package(
            package_dict, harvest_object, package_dict_form="package_show"
        )
        if not result:
            return result

        try:
            self._upsert_csv_resource(package_dict["id"], rows)
        except Exception as exc:  # noqa: BLE001 - o CSV é un extra, non crítico
            log.warning(
                "O dataset creouse correctamente, pero non se puido engadir "
                "o recurso CSV xerado: %s",
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
