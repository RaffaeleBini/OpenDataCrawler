# Inventario de fuentes de datos abiertos

Este documento recoge las fuentes candidatas a integrar en el catálogo. Empezó centrado en Galicia y en las cuatro cadenas de valor de DATAlife (secciones de abajo), y ahora se amplía a cualquier país y sector: la sección "Internacional" recoge catálogos de otros países y de alcance mundial. El directorio completo, con máscara de filtrado por país y sector, está disponible dentro del propio portal en `/explorar-catalogos` (solo administradores) — este documento es su respaldo en texto, con más detalle sobre cada decisión técnica.

Acrónimos usados: Instituto Galego de Estatística (IGE), Instituto Nacional de Estadística (INE), Oficina Española de Patentes y Marcas (OEPM), Oficina Europea de Patentes (EPO, por sus siglas en inglés), Sistema de Información Xeográfica de Parcelas Agrícolas (SIGPAC), European Forest Fire Information System (EFFIS), Application Programming Interface (API), Data Catalog Vocabulary (DCAT), Resource Description Framework (RDF), Web Feature Service/Web Map Service (WFS/WMS), Organización de las Naciones Unidas para la Alimentación y la Agricultura (FAO), Organización Mundial de la Salud (OMS), Global Health Observatory (GHO), Department for Environment, Food and Rural Affairs (DEFRA).

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
| data.europa.eu | Unión Europea | **Confirmado**: agrega los portales nacionales (incluye datos.gob.es, GovData...) vía una API REST de búsqueda propia (`data.europa.eu/api/hub/search/search?q=…`) y un endpoint SPARQL (`data.europa.eu/sparql`), no un feed DCAT plano | Ni CKAN ni DCAT RDF/JSON tal cual: necesitaría un conector a medida |
| abertos.xunta.gal | Xunta de Galicia | **Confirmado**: catálogo DCAT/RDF completo en `abertos.xunta.gal/busca-de-datos.rdf` (564 datasets) y también por dataset individual, p. ej. `.../dataset/0147/incendios-forestais.rdf` | Ya conectado un dataset real (ver estado técnico) |

## Internacional (fuera de España)

Este apartado nació para ampliar el alcance del catálogo a cualquier país y sector, no solo Galicia y las 4 cadenas de valor de DATAlife (que se mantienen como una opción más). Cada fuente se ha verificado con una petición real, igual que las de España.

| Fuente | País / alcance | Formato/acceso confirmado | Notas |
|---|---|---|---|
| data.gov.uk | Reino Unido | **Confirmado y ya conectado un dataset real** ("Sustainable fisheries", DEFRA): es CKAN nativo (más de 59.000 datasets), pero el endpoint `status_show` está bloqueado; `package_search` y el RDF por dataset individual (`.../dataset/{nombre}.rdf`) sí funcionan | Mismo patrón que datos.gob.es: un endpoint bloqueado no significa que toda la API lo esté |
| FAO catalog (`data.apps.fao.org`) | Global | **Confirmado y ya conectado un dataset real** ("Forest cover"): catálogo CKAN de la Organización de las Naciones Unidas para la Alimentación y la Agricultura (FAO), cerca de 12.000 datasets sobre suelo, agua, pesca, silvicultura y clima | Relevante para Agro-Mar-Alimentación y Forestal-Madera a escala mundial |
| GHO — Global Health Observatory (OMS) | Global | **Confirmado**: API OData pública en `ghoapi.azureedge.net/api/Indicator`, sin autenticación | Formato distinto a todo lo anterior; necesitaría un conector a medida, igual que el IGE o el INE |
| data.gouv.fr | Francia | **Confirmado**: API JSON propia (plataforma "udata", no CKAN) en `data.gouv.fr/api/1/datasets/`, más de 73.000 datasets | Necesitaría un conector a medida |
| GovData (`ckan.govdata.de`) | Alemania | **Confirmado y ya conectado un dataset real** ("Krankenhaus" — hospitales, clínicas de rehabilitación y de día en Dortmund, agregado desde el portal regional Open.NRW): CKAN nativo, con `ckanext-dcat` activado en su lado igual que abertos.xunta.gal/data.gov.uk/FAO, así que expone RDF por dataset individual (`ckan.govdata.de/dataset/{id}.rdf`) | Conectado en `salud-cuidados`, vía el mismo harvester `dcat_rdf` que ya teníamos, sin código nuevo. Incluye coordenadas geográficas reales por centro (ver estado técnico y `docs/cuadro-de-mando.md` para el mapa piloto construido con este dataset) |
| data.gov (`catalog.data.gov`) | Estados Unidos | **Reverificado, sigue bloqueado**: `status_show`, `package_search` y `data.json` devuelven HTTP 404 con un cuerpo `{"detail":{},"message":"Not Found"}` que no tiene forma de error de CKAN — parece un gateway/proxy delante de la API, no la ausencia del dominio (la web en sí responde HTTP 200) | Sigue pendiente; haría falta investigar si la API requiere una ruta distinta o una clave, no reintentar sin más |

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
- **Ampliación a alcance internacional**: se añadieron tres datasets reales fuera de España, usando el mismo harvester `dcat_rdf` de siempre: "Sustainable fisheries" del Reino Unido (`data.gov.uk`, publicado por DEFRA) en `agro-mar-alimentacion`, "Forest cover" de la FAO (alcance mundial) en `forestal-madera`, y "Krankenhaus" de Alemania (`ckan.govdata.de`, agregado desde el portal regional Open.NRW) en `salud-cuidados`. En los tres casos, igual que con la Xunta, el remoto es CKAN pero con `ckanext-dcat` activado en su lado, lo que expone un RDF por dataset individual (`/dataset/{nombre-o-id}.rdf`) — la misma vía que ya usábamos, sin necesidad de código nuevo. Se investigaron y verificaron otras cinco fuentes (Unión Europea, Reino Unido/FAO/Alemania ya conectadas, OMS, Francia, Estados Unidos); las que no usan CKAN ni DCAT (Unión Europea, OMS, Francia) quedan en el directorio pendientes de un conector a medida, y Estados Unidos se reverificó y sigue bloqueado.
- **El dataset alemán "Krankenhaus" resultó tener coordenadas geográficas reales**: cada centro trae una columna `Geografische Koordinate` con "latitud, longitud" combinadas en un solo campo de texto (convención habitual en catálogos alemanes). CKAN/DataStore lo carga tal cual (no separa el campo); la separación en dos columnas numéricas se hizo con una consulta SQL nativa dentro de Metabase (`split_part`), no modificando el dato de origen — ver `docs/cuadro-de-mando.md`. Es el primer dataset del catálogo con coordenadas de punto reales, usado para el mapa piloto del cuadro de mando.
- **Directorio de catálogos con máscara de filtrado**: nueva página `/explorar-catalogos` (solo administradores) dentro del propio portal, con un directorio de los 12 catálogos investigados hasta ahora (5 de España, 7 internacionales) y un filtro por país/región y sector para decidir qué conectar a continuación. El directorio vive en `ckan-docker/ckan/local-ext/ckanext-datalifetheme/ckanext/datalifetheme/data/catalog_directory.json`; se amplía añadiendo entradas ahí, sin tocar código.
- **Sin filtro nativo por tema o cantidad**: el harvester `dcat_rdf` recolecta todos los `dcat:Dataset` que encuentre en la URL indicada y sigue automáticamente la paginación si la hay; no tiene una opción de configuración para limitar cuántos importa. Para catálogos grandes (los 564 de abertos.xunta.gal, o el catálogo completo de datos.gob.es), la forma de acotar es apuntar a una URL ya filtrada por la propia fuente (por editor o por dataset individual — abertos.xunta.gal no filtra por categoría a nivel de URL, pero datos.gob.es sí por editor, ver más abajo), no a un límite dentro de CKAN.
- **Sandbox de pruebas técnicas retirado**: la organización `sandbox-pruebas`, su fuente `test-demo-ckan-org` (contra demo.ckan.org) y los 2 datasets de ejemplo que había recolectado (`my-sample-dataset-001`, `my-org-pcns`, ambos datos de muestra del propio demo.ckan.org, sin relación con DATAlife) se purgaron por completo, confirmado con el usuario. El catálogo queda con 14 organizaciones y 15 datasets reales.
