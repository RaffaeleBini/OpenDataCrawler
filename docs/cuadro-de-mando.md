# Cuadro de mando (visualización de datos)

## Qué es

Un cuadro de mando tipo BI (Business Intelligence, análisis de datos empresarial) para construir gráficos, mapas y tablas dinámicas a partir de los datasets que ya están en el catálogo, sin tener que descargarlos y abrirlos en otra herramienta. Es una funcionalidad de uso personal, igual que el resto de la plataforma.

## Cómo se construyó

Se usa [Metabase](https://www.metabase.com/), una herramienta de BI (Business Intelligence) de código abierto, desplegada como un servicio más de Docker (`metabase` en `ckan-docker/docker-compose.yml`), sin tocar la configuración de CKAN:

- Guarda su propia configuración y las visualizaciones creadas en un fichero H2 (formato de base de datos embebida) dentro de un volumen Docker con nombre (`metabase_data`), independiente del catálogo.
- Se conecta en modo solo lectura al **DataStore** de CKAN: la base de datos PostgreSQL donde `datapusher` vuelca automáticamente el contenido de los recursos tabulares (CSV/XLS) que se van conectando al catálogo. La conexión usa el usuario de solo lectura que CKAN ya trae preparado (`datastore_ro`, host `db`, puerto `5432`, base `datastore`).
- Es accesible en `http://localhost:3000`, con una única cuenta de administración (credenciales en `ckan-docker/.metabase_password.txt`, no versionado).
- Hay un enlace "Cuadro de mando" en la cabecera del portal que abre Metabase en una pestaña nueva.

## Qué datasets son visualizables hoy (y cuáles no)

Solo son visualizables desde Metabase los recursos que ya están cargados en el DataStore, es decir, ficheros CSV/XLS que `datapusher` haya procesado con éxito. **Importante**: en este despliegue, `datapusher` no se dispara automáticamente al recolectar (harvest) un recurso nuevo — hay que llamar manualmente a la acción `datapusher_submit` de la API de CKAN para cada recurso que se quiera cargar.

De los 15 datasets conectados al catálogo, se probaron 4 recursos como piloto:

| Dataset | Resultado | Nota |
|---|---|---|
| Datos del subsector gandeiro bovino (2023) | ✅ Cargado en el DataStore | La fila de cabecera del CSV origen está mal alineada: un nombre de concello (`Agolada`) quedó como nombre de columna, y las demás columnas quedaron con números como nombre en vez de una etiqueta real. Se renombraron en Metabase a `Concello` y `Dato 1`...`Dato 8` para que sean legibles, pero el significado exacto de cada `Dato N` se desconoce (problema del fichero origen, no de esta plataforma). Es el dataset usado en el cuadro de mando piloto de gráfico + tabla dinámica. |
| Krankenhaus — hospitales y clínicas de Dortmund (GovData, Alemania) | ✅ Cargado en el DataStore, y con coordenadas reales | El CSV está bien formado, sin problemas de cabecera. La columna de coordenadas viene como texto combinado (`"latitud, longitud"`); separarla en dos columnas numéricas para el mapa se hizo con una consulta SQL en Metabase, no modificando el dato de origen (detalle más abajo). Es el dataset usado en el mapa piloto. |
| Sustainable Fisheries (FAO) | ✅ Cargado en el DataStore, pero no es tabular | El CSV se parseó como una única columna de texto libre por fila, sin separación real en columnas — no permite gráficos ni tablas dinámicas útiles tal cual. |
| Produción de leite, ovos, polos, mel e cera (2020) | ❌ No se pudo cargar | El fichero real está detrás de un dominio (`mediorural.xunta.gal`) con un certificado SSL mal configurado; `datapusher` no puede descargarlo (`SSLCertVerificationError`). Es un problema de la fuente, no de esta plataforma. |

El resto de datasets del catálogo son mayoritariamente enlaces a páginas interactivas, Shapefile/GeoJSON o formatos que `datapusher` no vuelca al DataStore, así que hoy no son visualizables desde Metabase sin un paso adicional.

## Los cuadros de mando piloto

**"Piloto: Subsector gandeiro bovino 2023"**, con dos tarjetas sobre el dataset del subsector gandeiro bovino:

- Un **gráfico de barras** con los 15 concellos con el valor más alto de `Dato 7` (la columna numérica más grande de la tabla).
- Una **tabla dinámica** con todos los concellos y sus 8 columnas de datos.

**"Piloto: Hospitales de Dortmund - GovData Alemania (mapa)"**, con un **mapa de puntos** sobre el dataset "Krankenhaus" (hospitales, clínicas de rehabilitación y de día en Dortmund, Alemania, conectado vía GovData — ver `docs/fuentes.md`): 27 centros con coordenadas geográficas reales.

- Este dataset trae la coordenada como un único campo de texto (`Geografische Koordinate`, formato `"latitud, longitud"`), no como dos columnas numéricas separadas — convención habitual en catálogos alemanes. CKAN/DataStore carga el campo tal cual, sin separarlo.
- Para el mapa hizo falta una **consulta SQL nativa** dentro de Metabase (no una pregunta visual simple), usando `split_part()` de PostgreSQL para partir el campo en dos columnas (`Latitude`, `Longitude`) y convertirlas a número:
  ```sql
  SELECT "Objektname" AS "Nombre", "Objektart" AS "Tipo", "Ort" AS "Localidad",
         split_part("Geografische Koordinate", ',', 1)::float AS "Latitude",
         split_part("Geografische Koordinate", ',', 2)::float AS "Longitude"
  FROM "3fcc6519-855f-401a-bbf6-edddd158d8d7"
  ```
  Metabase reconoce automáticamente las columnas `Latitude`/`Longitude` (por ese nombre) para el mapa de puntos ("pin map"). El dato de origen no se modifica en ningún momento; la separación ocurre solo en la consulta de visualización.
- Es el primer dataset del catálogo con coordenadas de punto reales; sirve de plantilla para el siguiente dataset geolocalizado que se conecte (si ya trae latitud/longitud en columnas separadas, basta una pregunta visual normal, sin SQL).

## Cómo añadir una nueva conexión de datos en Metabase

### Automático: botón "Enviar a Metabase"

Cada fuente ya conectada en [Explorar catálogos](/explorar-catalogos) (`/explorar-catalogos`, solo administradores) tiene un botón **"Enviar a Metabase"** debajo de su etiqueta "Ya conectado". Al pulsarlo:

1. Se localizan todas las fuentes de harvesting conectadas para ese mismo dominio (p. ej. todas las de `abertos.xunta.gal`, aunque haya varias fuentes/datasets distintos del mismo origen).
2. De todos sus datasets, se cargan al DataStore (`datapusher_submit`) los recursos con un formato que `datapusher` sabe procesar (csv, xls, xlsx, tsv, ods) que todavía no estén cargados.
3. Se sincroniza en caliente la conexión de Metabase al DataStore, para que las tablas nuevas aparezcan sin esperar al ciclo periódico de Metabase.
4. Se renombran en Metabase todas las tablas del DataStore que todavía tengan el nombre por defecto (el UUID del recurso, poco legible — p. ej. "86524986 Bc95 47f2 A6b0..."), poniéndoles el título real del dataset de CKAN más su formato (p. ej. "Sustainable fisheries (CSV)"). Esto pasa cada vez que se pulsa el botón sobre una fuente con al menos un recurso cargado, no solo cuando hay recursos nuevos — así que también sirve para poner al día tablas que ya estaban cargadas pero sin nombre legible.
5. Se muestra un resumen ("N enviados; M ya estaban cargados; K con formato no soportado, omitidos").

**Límites a tener en cuenta**:
- Solo actúa sobre datasets **ya conectados** al catálogo — no crea datasets nuevos ni conecta fuentes nuevas.
- "Enviado" significa que se ha encolado la carga, no que haya terminado con éxito: si el fichero de origen tiene un problema real (cabecera mal formada, redirige a una página en vez de a un fichero, certificado SSL roto…), la carga puede fallar igualmente — el mismo tipo de aviso de calidad de datos ya documentado más arriba y en `docs/fuentes.md`.
- La sincronización con Metabase es inmediata solo si la carga termina en los pocos segundos posteriores al clic; para recursos grandes que tardan más, la tabla aparece en la siguiente sincronización periódica de Metabase (o volviendo a pulsar el botón más tarde).
- Algunas fuentes DCAT-AP europeas (comprobado con GovData/Alemania) guardan el formato del recurso como la URI completa del vocabulario europeo de tipos de fichero (p. ej. `http://publications.europa.eu/resource/authority/file-type/XLS`) en vez de simplemente `xls`. `datapusher` usa ese mismo valor para detectar el tipo de fichero y no lo reconoce, así que estos recursos se marcan como "formato no soportado" aunque el fichero real sí sea un XLS o CSV válido — es una limitación del propio `datapusher`, no de este botón.

### Manual

1. Cargar el recurso en el DataStore de CKAN (si no lo está ya): llamar a la acción `datapusher_submit` de la API de CKAN para ese recurso, o esperar a que `datapusher` lo procese si el recurso se conecta desde cero.
2. Metabase ya está conectado al DataStore completo (`Configuración > Administración > Bases de datos > Catálogo DATAlife (DataStore CKAN)`), así que cualquier recurso nuevo cargado en el DataStore aparece automáticamente como una tabla nueva tras la sincronización periódica de Metabase (o forzando una sincronización manual desde esa misma pantalla).
3. Desde "Nueva pregunta" en Metabase, elegir la tabla (el nombre de la tabla es el UUID del recurso en CKAN — se puede identificar copiando el UUID desde la URL del recurso en el catálogo) y construir el gráfico, mapa o tabla dinámica deseado.
4. Si el CSV origen tiene una cabecera mal alineada (como en el caso del subsector bovino), renombrar las columnas afectadas desde "Administración > Tablas > (tabla) > (columna) > Nombre visible" en Metabase, sin modificar el dato origen.

## Mapa de región de Galicia por comarca

Metabase trae de serie mapas de región de países y de EE. UU., pero no de las provincias o comarcas gallegas. El usuario aportó un GeoJSON propio (límites de las 53 comarcas de Galicia, en WGS84) y se registró como mapa personalizado en Metabase ("Comarcas de Galicia"), disponible para cualquier pregunta que agrupe datos por comarca.

- El fichero se sirve desde el propio portal (`ckanext-datalifetheme/ckanext/datalifetheme/public/comarcas-galicia.geojson`, accesible en `/comarcas-galicia.geojson`) y también vive en el repositorio de GitHub.
- La columna de datos que identifica cada comarca tiene que coincidir **exactamente** con el campo `Comarca` del GeoJSON (p. ej. "A Barcala", "Terra Chá"; hay también un campo `ComarcaMAY` en mayúsculas por si algún dataset usa esa convención).
- Piloto de verificación: dashboard "Piloto: Comarcas de Galicia (mapa de rexión)", con un mapa de las 53 comarcas coloreadas por su superficie en km² (dato tomado del propio GeoJSON, sin depender de ningún dataset del catálogo) — confirma que el mapa se registra y las 53 comarcas casan por nombre. Para un mapa con datos reales del catálogo haría falta un dataset con una columna de comarca (hoy los datasets gallegos vienen a nivel de concello, no de comarca; MeteoGalicia, por ejemplo, trae `concello` pero no `comarca`).

**Gotcha importante de seguridad, a tener en cuenta para cualquier mapa personalizado futuro**: Metabase bloquea por diseño cualquier URL de GeoJSON personalizado que resuelva a una dirección de red privada o interna (protección contra SSRF, ver [GHSA-w73v-6p7p-fpfr](https://github.com/metabase/metabase/security/advisories/GHSA-w73v-6p7p-fpfr)) — probado y confirmado que rechaza tanto el nombre de host interno de Docker (`ckan`) como la IP privada del contenedor, sin ninguna variable de entorno para permitirlo (solo existe `MB_CUSTOM_GEOJSON_ENABLED` para desactivar la función entera, no para relajar esta restricción). Por eso el GeoJSON no se sirve desde la red interna de Docker, sino desde una URL realmente pública: `https://raw.githubusercontent.com/RaffaeleBini/OpenDataCrawler/main/ckan-docker/ckan/local-ext/ckanext-datalifetheme/ckanext/datalifetheme/public/comarcas-galicia.geojson`.
