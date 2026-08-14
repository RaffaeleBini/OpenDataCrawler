# Taxonomía del catálogo

El catálogo empezó con 4 organizaciones de primer nivel, una por cada cadena de valor de DIH DATALIFE (Hub de Innovación Digital Europeo, EDIH por sus siglas en inglés), y se ha ampliado con 10 sectores más para cubrir cualquier ámbito, no solo los de DATAlife. En total hay 14 organizaciones en CKAN (más `sandbox-pruebas`, de uso técnico).

## Cadenas de valor originales de DATAlife

| Slug (CKAN) | Título | Descripción |
|---|---|---|
| `agro-mar-alimentacion` | Agro-Mar-Alimentación | Agricultura, ganadería, pesca, acuicultura e industria alimentaria en Galicia |
| `forestal-madera` | Forestal-Madera | Monte, gestión forestal e industria de la madera en Galicia |
| `salud-cuidados` | Salud-Cuidados | Salud, demografía, envejecimiento y servicios de cuidados en Galicia |
| `biotecnologia` | Biotecnología | Biotecnología, I+D+i, patentes y publicaciones científicas en Galicia |

## Ampliación a cualquier sector

| Slug (CKAN) | Título | Descripción |
|---|---|---|
| `medio-ambiente-clima` | Medio Ambiente y Clima | Biodiversidad, agua, calidad del aire, contaminación y cambio climático |
| `energia` | Energía | Producción, consumo y redes energéticas, incluidas las renovables |
| `transporte-movilidad` | Transporte y Movilidad | Transporte público, tráfico e infraestructuras de movilidad |
| `ciencia-tecnologia-id` | Ciencia, Tecnología e I+D | Investigación, patentes y financiación de la ciencia y la tecnología |
| `economia-finanzas` | Economía y Finanzas Públicas | Presupuestos, subvenciones, comercio e industria |
| `educacion` | Educación | Centros educativos, matriculación y resultados académicos |
| `cultura-turismo` | Cultura y Turismo | Patrimonio cultural, oferta turística y actividades culturales |
| `vivienda-urbanismo` | Vivienda y Urbanismo | Planificación urbana, vivienda e infraestructuras urbanas |
| `gobierno-sector-publico` | Gobierno y Sector Público | Transparencia, contratación pública y rendición de cuentas |
| `demografia-sociedad` | Demografía y Sociedad | Población, envejecimiento y bienestar social |

Además existe `general`, no como organización sino como etiqueta del directorio de catálogos (`/explorar-catalogos`) para fuentes que cubren todos los sectores a la vez (agregadores nacionales como datos.gob.es).

## Dónde vive esta taxonomía

La lista completa de sectores (con sus etiquetas legibles) está centralizada en un único sitio del código, para no tener que mantenerla duplicada: `ckan-docker/ckan/local-ext/ckanext-datalifetheme/ckanext/datalifetheme/plugin.py`, constante `SECTOR_LABELS`. De ahí se alimentan tanto el desplegable de sector de la portada como el de `/explorar-catalogos`.

Cada dataset se asigna a la organización de la cadena de valor a la que pertenezca; si aplica a varias, se usan además los grupos temáticos (`groups` en CKAN) como etiqueta transversal (pendiente de definir en función de los datasets reales que se incorporen).

## Próximos pasos de taxonomía

- Definir subtemas/grupos dentro de cada cadena de valor conforme se incorporen datasets reales.
- Definir vocabulario de etiquetas (tags) común, evitando duplicados por sinónimos.
- Los 10 sectores nuevos son organizaciones reales pero, a fecha de esta actualización, todavía sin ningún dataset conectado — están listos para recibir el primero.
