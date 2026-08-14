# Inventario de fuentes de datos abiertos

Este documento recoge las fuentes candidatas a integrar en el catálogo, organizadas por cadena de valor de DATAlife. Es un punto de partida (Fase 0): hay que validarlo y priorizarlo con las entidades socias.

Acrónimos usados: Instituto Galego de Estatística (IGE), Instituto Nacional de Estadística (INE), Oficina Española de Patentes y Marcas (OEPM), Oficina Europea de Patentes (EPO, por sus siglas en inglés), Sistema de Información Xeográfica de Parcelas Agrícolas (SIGPAC), European Forest Fire Information System (EFFIS), Application Programming Interface (API), Data Catalog Vocabulary (DCAT), Resource Description Framework (RDF), Web Feature Service/Web Map Service (WFS/WMS).

## Agro-Mar-Alimentación

| Fuente | Organismo | Formato/acceso conocido | Notas |
|---|---|---|---|
| IGE — agricultura, ganadería y pesca | Xunta de Galicia | **Confirmado**: API REST propia sin autenticación, documentada en `ige.gal/web/mostrar_paxina.jsp?idioma=es&paxina=004015` (`igebdt/igeapi/datos/{código}` y `.../datosindi/{código}`, en CSV/JSON/JSON-stat) | No es CKAN ni DCAT: necesitaría un conector a medida que traduzca JSON-stat a datasets CKAN |
| Consellería do Medio Rural | Xunta de Galicia | Web, SIGPAC | Datos de explotaciones y parcelas agrícolas |
| Consellería do Mar / Portos de Galicia | Xunta de Galicia | Web, estadísticas pesqueras | Trazabilidad y lonjas |
| MeteoGalicia | Xunta de Galicia | **Confirmado**: API REST propia MeteoSIX (`servizos.meteogalicia.gal/apiv4/`, requiere clave por solicitud) + servicios OGC abiertos sin clave: WMS/WCS (`meteogalicia.gal/geoserver/ows?SERVICE=WMS&REQUEST=GetCapabilities`) y THREDDS/OPeNDAP (`mandeo.meteogalicia.es/thredds`) | No es CKAN ni DCAT: necesitaría un conector a medida. La vía OGC (WMS/WCS) es la más automatizable sin gestionar una clave |
| INE — agricultura y pesca | Gobierno de España | **Confirmado**: API REST propia Tempus3 (`servicios.ine.es/wstempus/js/...`), sin autenticación, JSON con codificación UTF-8 correcta | Conector a medida ya construido (`ine_harvester`), ver estado técnico |
| opendata.esri.es — Comarcas Agrarias de España | MAPA, vía ArcGIS Hub de Esri España | **Confirmado y ya conectado**: feed DCAT-US 1.1 JSON, filtrable por id de dataset | En la organización `agro-mar-alimentacion`, con CSV/Shapefile/GeoJSON/KML de descarga directa confirmada |
| Eurostat — agri/fish | Unión Europea | API REST, bulk download | Cobertura europea/regional (NUTS2 Galicia) |
| Copernicus / Sentinel | Unión Europea | API, descarga masiva | Teledetección agraria y marina (mareas rojas, cultivos) |

## Forestal-Madera

| Fuente | Organismo | Formato/acceso conocido | Notas |
|---|---|---|---|
| abertos.xunta.gal — montes e incendios | Xunta de Galicia | **Confirmado: catálogo DCAT/RDF**, no CKAN | Dataset "Incendios forestales" ya conectado (ver estado técnico) |
| INE — extracción nacional de materiales | Gobierno de España | **Confirmado y ya conectado**: API REST Tempus3 (ver estado técnico) | Incluye madera y masa forestal en pie, entre otras categorías |
| Inventario Forestal (IFN/MFE) | Ministerio/Xunta | Descargas GIS | Formato shapefile/GeoJSON habitual |
| EFFIS (incendios) | Copernicus/UE | API, descarga | Riesgo y seguimiento de incendios |

## Salud-Cuidados

| Fuente | Organismo | Formato/acceso conocido | Notas |
|---|---|---|---|
| SERGAS | Xunta de Galicia | Por confirmar si publica datos abiertos | Pendiente de verificación |
| IGE — demografía/envejecimiento | Xunta de Galicia | **Confirmado y ya conectado**: API REST propia sin autenticación (ver estado técnico) | Conector a medida ya construido (`ige_harvester`) |
| opendata.esri.es — Servicio Sanitarios de Galicia | Contenidos Esri España | **Confirmado y ya conectado**: feed DCAT-US 1.1 JSON, filtrable por id de dataset | Farmacias, centros de salud, hospitales y centros de especialidades de Galicia; CSV/Shapefile/GeoJSON/KML de descarga directa confirmada |
| INE — salud | Gobierno de España | API JSON/CSV | Cobertura nacional |
| Eurostat — health | Unión Europea | API REST | Comparativa europea |

## Biotecnología

| Fuente | Organismo | Formato/acceso conocido | Notas |
|---|---|---|---|
| OEPM / EPO | España / UE | APIs de patentes | Vigilancia tecnológica |
| Repositorios USC/UDC/UVIGO/CSIC | Universidades | Variable (OAI-PMH en muchos repositorios institucionales) | A confirmar caso por caso |
| Eurostat — I+D+i | Unión Europea | API REST | Indicadores de innovación |

## Transversales (agregadores generales)

| Fuente | Organismo | Formato/acceso confirmado | Notas |
|---|---|---|---|
| datos.gob.es | Gobierno de España | **Confirmado y ya conectado un dataset real**: la API nativa de CKAN (`/api/3/action/...`) sigue bloqueada por firewall desde esta red (HTTP 403), pero su **API de datos enlazados** (`datos.gob.es/apidata/catalog/dataset.rdf`, formato DCAT/RDF, paginada) responde con normalidad (HTTP 200) desde el mismo sitio, con o sin cabecera de navegador. También hay un endpoint SPARQL público en `datos.gob.es/sparql`. Admite filtrar por editor (`.../apidata/catalog/dataset/publisher/{código}.rdf`) y por tema NTI-RISP (`.../apidata/catalog/dataset/theme/{tema}.rdf`, aunque solo algunos slugs de tema funcionan; confirmados `ciencia-tecnologia`, `economia`, `medio-ambiente`, `salud`, `demografia`, `sociedad-bienestar`), y por dataset individual (`.../apidata/catalog/dataset/{id}.rdf`) | El bloqueo era del endpoint CKAN concreto, no del dominio: usar el harvester `dcat_rdf` contra `/apidata/...` en vez del harvester `ckan` contra `/api/3/...` evita el problema por completo. **Importante**: filtrar por editor=Xunta de Galicia (código `A12002994`) solo duplica lo que ya tenemos de abertos.xunta.gal — el valor real de datos.gob.es para nosotros está en organismos *no* gallegos (OEPM, ministerios, otras comunidades) con datos relevantes para Galicia |
| data.europa.eu | Unión Europea | DCAT/SPARQL | Portal europeo, compatible con el harvester DCAT ya instalado |
| abertos.xunta.gal | Xunta de Galicia | **Confirmado**: catálogo DCAT/RDF completo en `abertos.xunta.gal/busca-de-datos.rdf` (564 datasets) y también por dataset individual, p. ej. `.../dataset/0147/incendios-forestais.rdf` | Ya conectado un dataset real (ver estado técnico) |

## Estado de verificación técnica (13/08/2026)

- **CKAN Harvester** (`ckan`) y **DCAT RDF Harvester** (`dcat_rdf`) quedan instalados y operativos en la plataforma (ver `ckan-docker/`), junto con los procesos `harvest-gather`, `harvest-fetch` y `harvest-scheduler` que procesan las colas de recolección. Los nombres técnicos exactos (`source_type`) son `ckan` y `dcat_rdf`, no los nombres de los paquetes Python.
- **Siete datasets reales conectados**, uno o dos por cada cadena de valor, todos desde `abertos.xunta.gal` vía el harvester `dcat_rdf` contra el endpoint RDF individual de cada dataset (no existe filtro por categoría a nivel de URL en este portal: se probaron `/catalogo/{categoría}.rdf` y parámetros `?tema=`/`?categoria=` sobre el volcado completo, y ninguno filtra; por eso la conexión es dataset a dataset):

  | Cadena de valor | Dataset | Recursos |
  |---|---|---|
  | Agro-Mar-Alimentación | Producción de leche, huevos, pollos, miel y cera 2020 | 1 (XLS/CSV) |
  | Agro-Mar-Alimentación | Datos del subsector ganadero bovino 2023 | 1 (XLS, descarga directa confirmada) |
  | Forestal-Madera | Incendios forestales | 2 (CSV) |
  | Forestal-Madera | Produción de madeira | 1 (redirige a selector IGE, no descarga directa) |
  | Salud-Cuidados | Proyecciones de población e indicadores de envejecimiento 2022-2037 | 1 (redirige a selector IGE, no descarga directa) |
  | Salud-Cuidados | Encuesta estructural a hogares: dependencia (2017) | 2 (una es un ZIP de microdatos, descarga directa confirmada) |
  | Biotecnología | Gastos y personal en I+D | 1 (redirige a selector IGE, no descarga directa) |

  **Aviso de calidad de datos, no es un fallo nuestro**: alrededor de la mitad de estos recursos son descargas directas (XLS, ZIP) y la otra mitad son enlaces que el propio catálogo de la Xunta etiqueta como "CSV" pero en realidad redirigen a un selector interactivo del IGE (Instituto Galego de Estatística), sin fichero descargable directo. Antes de mostrar un dataset como "descarga automática" en el portal, hay que comprobar a qué resuelve realmente cada recurso.
- **Primer dataset real conectado desde datos.gob.es**: probamos filtrar por editor=Xunta de Galicia y comprobamos que es exactamente el mismo catálogo que abertos.xunta.gal (mismos títulos, mismos datasets) — no aporta nada nuevo conectarlo así. En su lugar, buscamos por tema (`ciencia-tecnologia`) organismos *no* gallegos y conectamos el **Authority File de la Oficina Española de Patentes y Marcas (OEPM)**: inventario de patentes y modelos de utilidad publicados desde 1826, con tres recursos ZIP de descarga directa confirmada (sede.oepm.gob.es), en la organización `biotecnologia`. Pendiente menor: el título llegó en inglés porque el harvester tomó ese `dct:title` antes que el gallego/castellano disponible en la misma fuente; hay que revisar si se puede fijar el idioma preferido en la configuración del harvester para futuras conexiones.
- **Conector a medida construido para el IGE**: la API del IGE no expone catálogo CKAN ni DCAT, solo tablas individuales en JSON/CSV, así que en vez de forzar un harvester genérico, se escribió una extensión propia (`ckan-docker/ckan/local-ext/ckanext-igeharvester`, plugin `ige_harvester`, `source_type`: `ige`). La fuente de harvesting apunta directamente a la URL JSON de una tabla del IGE (p. ej. `igebdt/igeapi/json/datos/1552/...`, población de Galicia por censos) y el harvester crea un dataset con dos recursos: la misma tabla en JSON y en CSV. Ya conectada y funcionando en la organización `salud-cuidados`.

  **Aviso de calidad de datos del IGE, no es un fallo nuestro**: la API del IGE declara `charset=UTF-8` en la cabecera HTTP pero en realidad devuelve los bytes en ISO-8859-1; si no se decodifica explícitamente así, los acentos y las eñes se corrompen (mojibake). El harvester ya lo hace correctamente; cualquier otro consumidor de esta API tendría que hacer lo mismo.

  **Aprendizaje de la implementación**: los objetos `HarvestSource` no tienen un atributo `owner_org` propio — cada fuente de harvesting es en realidad un `Package` de tipo `harvest` con el mismo id, y el `owner_org` vive en ese `Package`. Hay que consultarlo con `model.Package.get(source.id).owner_org`, no con `source.owner_org` (esto rompió el primer intento con un `AttributeError` real, ya corregido).
- **Conector a medida construido para el INE**: igual que el IGE, la API Tempus3 del INE (`servicios.ine.es/wstempus/js/...`) no expone catálogo CKAN ni DCAT, solo tablas JSON. Se escribió otra extensión propia (`ckan-docker/ckan/local-ext/ckanext-ineharvester`, plugin `ine_harvester`, `source_type`: `ine`). A diferencia del IGE, el INE **sí declara la codificación correctamente** (UTF-8 real) y **no ofrece una variante CSV** real para esta función (el parámetro `formato=csv` se ignora), así que el dataset se crea con un único recurso JSON. Ya conectado: la tabla de Cuentas de Flujos de Materiales (extracción nacional por categoría, incluida madera y masa forestal en pie), en `forestal-madera`.
- **opendata.esri.es resultó ser un hallazgo importante**: no es un portal propio de Esri, sino un Hub genérico de ArcGIS que agrega datasets de decenas de administraciones españolas. Expone un feed DCAT-US 1.1 JSON (`opendata.esri.es/api/feed/dcat-us/1.1.json`, formato distinto del RDF/XML habitual: es JSON con esquema Project Open Data). Este formato usa un harvester diferente al que ya teníamos, `dcat_json` (plugin `dcat_json_harvester`), **incluido ya en el mismo paquete ckanext-dcat que instalamos** — no hizo falta código nuevo, solo activar el plugin. El feed completo tiene 1.440 datasets (10&nbsp;MB) de toda España, pero admite filtrar a un único dataset con `?id={identificador de ArcGIS}`, así que la conexión es dataset a dataset, igual que con abertos.xunta.gal. Se conectaron dos, ambos con CSV/Shapefile/GeoJSON/KML de descarga directa confirmada (la mejor calidad de recursos que hemos visto hasta ahora): "Servicio Sanitarios de Galicia" (`salud-cuidados`) y "Comarcas Agrarias de España" (`agro-mar-alimentacion`).
- **Sin filtro nativo por tema o cantidad**: el harvester `dcat_rdf` recolecta todos los `dcat:Dataset` que encuentre en la URL indicada y sigue automáticamente la paginación si la hay; no tiene una opción de configuración para limitar cuántos importa. Para catálogos grandes (los 564 de abertos.xunta.gal, o el catálogo completo de datos.gob.es), la forma de acotar es apuntar a una URL ya filtrada por la propia fuente (por editor o por dataset individual — abertos.xunta.gal no filtra por categoría a nivel de URL, pero datos.gob.es sí por editor, ver más abajo), no a un límite dentro de CKAN.
- **Sandbox de pruebas técnicas pendiente de retirar**: la organización `sandbox-pruebas` y la fuente `test-demo-ckan-org` (contra demo.ckan.org) siguen ahí, solo para validar el mecanismo; hay que borrarlas antes de producción.
