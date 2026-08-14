# Taxonomía del catálogo

El catálogo organiza los datasets con 4 organizaciones de primer nivel, una por cada cadena de valor de DIH DATALIFE (Hub de Innovación Digital Europeo, EDIH por sus siglas en inglés):

| Slug (CKAN) | Título | Descripción |
|---|---|---|
| `agro-mar-alimentacion` | Agro-Mar-Alimentación | Agricultura, ganadería, pesca, acuicultura e industria alimentaria en Galicia |
| `forestal-madera` | Forestal-Madera | Monte, gestión forestal e industria de la madera en Galicia |
| `salud-cuidados` | Salud-Cuidados | Salud, demografía, envejecimiento y servicios de cuidados en Galicia |
| `biotecnologia` | Biotecnología | Biotecnología, I+D+i, patentes y publicaciones científicas en Galicia |

Estas 4 organizaciones ya están creadas en la instancia CKAN del proyecto (`ckan-docker/`). Cada dataset se debe asignar a la organización de la cadena de valor a la que pertenezca; si aplica a varias, se usan además los grupos temáticos (`groups` en CKAN) como etiqueta transversal (pendiente de definir en Fase 1 en función de los datasets reales que se incorporen).

## Próximos pasos de taxonomía (Fase 1)

- Definir subtemas/grupos dentro de cada cadena de valor conforme se incorporen datasets reales.
- Definir vocabulario de etiquetas (tags) común, evitando duplicados por sinónimos.
- Revisar si conviene una organización adicional "Transversal" para fuentes que no encajan en una sola cadena de valor (p. ej. IGE demografía general).
