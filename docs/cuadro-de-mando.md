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

1. Cargar el recurso en el DataStore de CKAN (si no lo está ya): llamar a la acción `datapusher_submit` de la API de CKAN para ese recurso, o esperar a que `datapusher` lo procese si el recurso se conecta desde cero.
2. Metabase ya está conectado al DataStore completo (`Configuración > Administración > Bases de datos > Catálogo DATAlife (DataStore CKAN)`), así que cualquier recurso nuevo cargado en el DataStore aparece automáticamente como una tabla nueva tras la sincronización periódica de Metabase (o forzando una sincronización manual desde esa misma pantalla).
3. Desde "Nueva pregunta" en Metabase, elegir la tabla (el nombre de la tabla es el UUID del recurso en CKAN — se puede identificar copiando el UUID desde la URL del recurso en el catálogo) y construir el gráfico, mapa o tabla dinámica deseado.
4. Si el CSV origen tiene una cabecera mal alineada (como en el caso del subsector bovino), renombrar las columnas afectadas desde "Administración > Tablas > (tabla) > (columna) > Nombre visible" en Metabase, sin modificar el dato origen.

## Limitación conocida: mapas de región de Galicia

Metabase trae de serie mapas de región de países y de EE. UU., pero no de las provincias o comarcas gallegas. Para un mapa coroplético (mapa donde cada zona se colorea según un valor) de Galicia por concello o comarca haría falta subir un fichero GeoJSON propio en "Administración > Mapas". Se deja como mejora futura, no bloqueante: los mapas de puntos (latitud/longitud) sí funcionan de serie en cuanto haya un dataset cargado con coordenadas.
