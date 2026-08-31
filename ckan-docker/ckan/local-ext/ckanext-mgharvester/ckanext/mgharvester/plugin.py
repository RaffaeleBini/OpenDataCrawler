# -*- coding: utf-8 -*-
"""
Harvester a medida para a API JSON de MeteoGalicia (rede de estacións
meteorolóxicas).

MeteoGalicia non ofrece catálogo CKAN nin DCAT, senón varios servizos JSON
públicos e sen autenticación en servizos.meteogalicia.gal/mgrss/. Este
harvester usa o servizo de datos diarios:

    https://servizos.meteogalicia.gal/mgrss/observacion/datosDiariosEstacionsMeteo.action

que, sen parámetros, devolve o día en curso; admite datIni/dataFin
(dd/MM/yyyy) para un intervalo.

A resposta é unha lista de días, cada un cunha lista de estacións, cada
unha cunha lista de medidas (un valor por parámetro meteorolóxico). Igual
que coa OMS, ademais do recurso JSON orixinal, este harvester aplana esa
estrutura aniñada nunha fila por (día, estación, parámetro) e sobe un CSV
xerado, para que sexa cargable no DataStore e visualizable no cadro de
mando.

**Series temporais sen límite de 7 días**: cada execución pide unha
fiestra dos últimos 30 días (marxe de sobra fronte a execucións manuais
espazadas no tempo, xa que esta fonte non ten frecuencia automática) e
**fusiona** eses datos cos xa acumulados en execucións anteriores — lidos
de volta do propio DataStore ANTES de tocar o dataset —, en vez de
substituílos. O histórico total medra así a cada execución, sen límite
fixo: un día que xa se importou nunca desaparece por quedar fóra da
fiestra dunha execución posterior. Cando unha fiestra volve traer un día
xa gardado (por exemplo, porque MeteoGalicia acaba de validar un dato que
antes viña marcado como sospeitoso), a versión nova substitúe á antiga
dese día/estación/parámetro concreto; o resto do histórico non se toca.

**Detalle importante de orde**: `HarvesterBase._create_or_update_package`
(o método base de ckanext-harvest que crea/actualiza o dataset) chama a
`package_update` cun `package_dict` que declara os recursos — e
`package_update` non fai un "parche", senón que SUBSTITÚE por completo a
lista de recursos do dataset pola que se lle pase: calquera recurso xa
existente que non apareza nesa lista (identificado pola súa `id`) queda
BORRADO nese mesmo paso. Por iso:

1. A lectura do acumulado e a fusión teñen que facerse ANTES de chamar a
   `_create_or_update_package`, non despois: se se fixese despois (como
   na primeira versión deste harvester), o recurso CSV xa estaría
   borrado e `_fetch_existing_rows` sempre atoparía unha lista baleira,
   perdendo en silencio todo o histórico anterior á fiestra da execución
   en curso.
2. O `package_dict` ten que incluír a `id` dos recursos xa existentes
   (JSON e CSV) cando os hai, para que `package_update` os actualice en
   vez de borralos e crear uns novos. Non facelo así (como tamén pasaba
   na primeira versión) fai que cada execución xere un recurso CSV novo
   con outra `id` — e, máis grave aínda, o borrado interno que fai
   `package_update` non dispara a limpeza da táboa do DataStore
   asociada (é un gotcha coñecido de CKAN: iso só pasa co borrado
   explícito dun recurso vía a acción `resource_delete`), así que cada
   execución deixaba ademais unha táboa orfa acumulando espazo en
   Postgres e ruído en Metabase. Mantendo a mesma `id` de recurso entre
   execucións, a táboa do DataStore tamén se mantén: nunca se borra nin
   se recrea, só se actualiza o seu contido.
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
                "Importa os datos diarios da rede de estacións "
                "meteorolóxicas de MeteoGalicia como un dataset de CKAN "
                "que acumula historial sen límite fixo (cada execución "
                "fusiona unha fiestra dos últimos 30 días coa acumulada en "
                "execucións anteriores), cun recurso JSON (a fonte máis "
                "recente) e un CSV acumulado xerado a partir deses datos."
            ),
            "form_config_interface": "Text",
        }

    def _date_window_url(self, base_url):
        today = datetime.date.today()
        start = today - datetime.timedelta(days=29)
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

    def _resolve_package_id(self, harvest_object):
        previous = (
            model.Session.query(HarvestObject)
            .filter(HarvestObject.guid == harvest_object.guid)
            .filter(HarvestObject.current == True)  # noqa: E712
            .filter(HarvestObject.id != harvest_object.id)
            .first()
        )
        return previous.package_id if previous and previous.package_id else str(uuid.uuid4())

    def _package_dict(self, harvest_object, rows, all_rows, source, owner_org,
                       package_id, existing_json_resource, existing_csv_resource):
        json_url = self._date_window_url(harvest_object.guid)
        title = source.title or "MeteoGalicia — Datos diarios de estacións meteorolóxicas"
        n_estacions = len({r["idEstacion"] for r in all_rows})
        datas = sorted({str(r["data"])[:10] for r in all_rows})
        notes = (
            "Datos diarios da rede de estacións meteorolóxicas de "
            "MeteoGalicia, importados automaticamente do seu servizo JSON "
            "público. Cada execución pide unha fiestra dos últimos 30 días "
            "(esta vez trouxo %d filas) e fusiona eses datos cos xa "
            "acumulados en execucións anteriores: o histórico total do "
            "recurso CSV medra a cada execución, sen límite fixo. Estado "
            "actual do acumulado: %d filas, %d estacións, do %s ao %s.\n\n"
            "Cada fila é un valor dun parámetro meteorolóxico (temperatura, "
            "choiva, vento, humidade...) nunha estación e día concretos. "
            "Descrición completa dos códigos de parámetro: "
            "https://www.meteogalicia.gal/web/observacion/parametros\n\n"
            "Fonte orixinal (última fiestra descargada): %s"
        ) % (
            len(rows), len(all_rows), n_estacions,
            datas[0] if datas else "?", datas[-1] if datas else "?",
            json_url,
        )

        # Reenviar a `id` dun recurso xa existente (cando o hai) fai que
        # package_update o actualice no seu sitio en vez de borralo e crear
        # un novo — ver a nota de "Detalle importante de orde" arriba.
        json_resource = {
            "url": json_url, "format": "JSON", "name": "Datos (JSON, fonte orixinal)",
        }
        if existing_json_resource:
            json_resource["id"] = existing_json_resource["id"]
        resources = [json_resource]

        if existing_csv_resource:
            # O contido real (xa fusionado co histórico) súbese despois, á
            # parte, en _upsert_csv_resource — aquí só se reenvía tal cual
            # para que non se borre ao substituír a lista de recursos.
            resources.append({
                "id": existing_csv_resource["id"],
                "url": existing_csv_resource.get("url"),
                "format": existing_csv_resource.get("format") or "CSV",
                "name": existing_csv_resource.get("name") or "Datos (CSV)",
            })

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
        package_id = self._resolve_package_id(harvest_object)

        context = {
            "model": model,
            "session": model.Session,
            "user": self._get_user_name(),
            "ignore_auth": True,
        }

        # A fusión co acumulado ten que facerse XA, antes de tocar o
        # dataset: _create_or_update_package (máis abaixo) substitúe por
        # completo a lista de recursos polo que se lle pase, así que
        # calquera recurso xa existente que non se reenvíe (coa súa id)
        # queda borrado nese mesmo paso. Lelo despois xa sería tarde de máis.
        existing_json_resource, existing_csv_resource = self._fetch_existing_resources(
            context, package_id
        )
        existing_rows = self._fetch_existing_rows(context, existing_csv_resource)
        all_rows = self._merge_rows(existing_rows, rows)
        log.debug(
            "MGHarvester: %d filas xa acumuladas + %d desta fiestra = %d "
            "filas totais tras a fusión",
            len(existing_rows), len(rows), len(all_rows),
        )

        # Mesmo patrón xa probado coa OMS: primeiro créase/actualízase o
        # dataset só co recurso JSON, e só despois, como paso aparte e
        # illado, súbese o CSV xerado — mesturalo no mesmo package_dict que
        # xestiona _create_or_update_package rompe (FileStorage non é
        # serializable) e pode deixar a sesión de base de datos a medias.
        package_dict = self._package_dict(
            harvest_object, rows, all_rows, source, owner_org, package_id,
            existing_json_resource, existing_csv_resource,
        )
        result = self._create_or_update_package(
            package_dict, harvest_object, package_dict_form="package_show"
        )
        if not result:
            return result

        try:
            self._upsert_csv_resource(context, package_dict["id"], all_rows)
        except Exception as exc:  # noqa: BLE001 - o CSV é un extra, non crítico
            log.warning(
                "O dataset creouse correctamente, pero non se puido engadir "
                "o recurso CSV acumulado: %s",
                exc,
            )

        return result

    def _row_key(self, row):
        def norm_id(value):
            try:
                return str(int(float(value)))
            except (TypeError, ValueError):
                return str(value)

        fecha = str(row.get("data") or "")[:10]
        return (fecha, norm_id(row.get("idEstacion")), str(row.get("codigoParametro")))

    def _fetch_existing_resources(self, context, package_id):
        """Devolve (recurso_json, recurso_csv) xa existentes para este
        dataset — cada un None se aínda non existe (dataset novo, ou aínda
        sen ese recurso concreto). Pasarllos de volta a
        `_create_or_update_package` coa súa `id` é o que evita que os borre
        ao substituír a lista de recursos — ver a nota do docstring do
        módulo."""
        try:
            pkg = toolkit.get_action("package_show")(dict(context), {"id": package_id})
        except Exception:
            return None, None
        resources = pkg.get("resources", [])
        json_resource = next(
            (r for r in resources if r.get("name") == "Datos (JSON, fonte orixinal)"),
            None,
        )
        csv_resource = next(
            (r for r in resources if r.get("name") == "Datos (CSV)"),
            None,
        )
        return json_resource, csv_resource

    def _fetch_existing_rows(self, context, existing_resource):
        """Le do DataStore as filas xa acumuladas en execucións anteriores,
        para fusionalas coas novas en vez de substituílas. Devolve sempre
        unha lista (baleira se aínda non hai recurso, se aínda non está
        cargado no DataStore, ou se algo falla ao lelo) — nunca lanza
        excepción, para que un fallo aquí non impida gardar polo menos a
        fiestra recén descargada."""
        if not existing_resource or not existing_resource.get("datastore_active"):
            return []

        fields = [
            "data", "idEstacion", "estacion", "concello", "provincia",
            "utmx", "utmy", "codigoParametro", "nomeParametro", "unidade",
            "valor", "lnCodigoValidacion",
        ]
        rows = []
        offset = 0
        page_size = 20000
        while True:
            try:
                result = toolkit.get_action("datastore_search")(
                    dict(context),
                    {
                        "resource_id": existing_resource["id"],
                        "fields": fields,
                        "limit": page_size,
                        "offset": offset,
                    },
                )
            except Exception as exc:  # noqa: BLE001 - mellor perder o acumulado que romper o harvest
                log.warning(
                    "Non se puideron ler os datos xa acumulados do "
                    "DataStore (recurso %s) para fusionalos cos novos: %s",
                    existing_resource["id"], exc,
                )
                return rows
            records = result.get("records", [])
            rows.extend(records)
            if len(records) < page_size:
                break
            offset += page_size
        return rows

    def _merge_rows(self, existing_rows, new_rows):
        """Combina o acumulado xa existente cos datos recén descargados,
        indexando por (día, estación, parámetro). Os novos gañan cando
        coinciden — o caso típico é que MeteoGalicia acabe de validar un
        dato que antes viña marcado como sospeitoso — pero o resto do
        histórico existente non se toca nin se perde."""
        merged = {self._row_key(r): r for r in existing_rows}
        merged.update({self._row_key(r): r for r in new_rows})
        return sorted(merged.values(), key=self._row_key)

    def _upsert_csv_resource(self, context, package_id, rows):
        """Sobe `rows` (xa fusionado co histórico previo por quen chama) como
        o recurso "Datos (CSV)". Como `_create_or_update_package` (chamado
        xusto antes) xa reenviou a `id` do recurso CSV existente cando a
        había, este segue existindo e o camiño normal é `resource_update`
        (mesma id, mesma táboa do DataStore); só entra por
        `resource_create` na primeira execución dun dataset novo."""
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
