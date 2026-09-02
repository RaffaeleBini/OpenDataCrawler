# Plataforma de Datos Abiertos (DATAlife)

Catálogo/agregador de datos abiertos. Nació centrado en Galicia y en las cuatro cadenas de valor del Hub de Innovación Digital Europeo (EDIH, por sus siglas en inglés) DIH DATALIFE (Agro-Mar-Alimentación, Forestal-Madera, Salud-Cuidados y Biotecnología), y ahora amplía su alcance a cualquier país y sector: esas cuatro cadenas de valor siguen existiendo como una opción más, junto a un directorio creciente de catálogos internacionales.

El plan completo (contexto, decisiones, fases) está en `C:\Users\Raffaele-DIHDatalife\.claude\plans\quiero-crear-una-plataforma-ancient-creek.md`.

## Estado actual (Fase 1 — MVP en marcha)

- Motor de catálogo: [CKAN](https://ckan.org) 2.11, desplegado con Docker Compose a partir del repositorio oficial [ckan/ckan-docker](https://github.com/ckan/ckan-docker) (carpeta [ckan-docker/](ckan-docker/)).
- Extensiones de harvesting instaladas: [ckanext-harvest](https://github.com/ckan/ckanext-harvest) (harvester tipo `ckan`, para recolectar de otros CKAN), [ckanext-dcat](https://github.com/ckan/ckanext-dcat) (harvesters tipo `dcat_rdf` para catálogos DCAT/RDF como abertos.xunta.gal o datos.gob.es, y `dcat_json` para el formato DCAT-US JSON de portales ArcGIS Hub como opendata.esri.es) y cinco harvesters propios para APIs que no exponen ni CKAN ni DCAT: `ckan-docker/ckan/local-ext/ckanext-igeharvester` (tipo `ige`, para el Instituto Galego de Estatística), `ckan-docker/ckan/local-ext/ckanext-ineharvester` (tipo `ine`, para el Instituto Nacional de Estadística), `ckan-docker/ckan/local-ext/ckanext-ghoharvester` (tipo `gho`, para el Global Health Observatory de la OMS), `ckan-docker/ckan/local-ext/ckanext-dgfharvester` (tipo `dgf`, para data.gouv.fr en Francia) y `ckan-docker/ckan/local-ext/ckanext-mgharvester` (tipo `mg`, para MeteoGalicia). Además, algunos datasets se conectan sin ninguna fuente de harvesting (`package_create` directo), cuando el origen solo ofrece descargas ZIP sueltas sin API ni catálogo — ver el centro de descargas de la Xunta en docs/fuentes.md.
- Taxonomía: 14 organizaciones creadas en CKAN — las 4 cadenas de valor originales de DATAlife más 10 sectores nuevos (Medio Ambiente y Clima, Energía, Transporte y Movilidad, Ciencia/Tecnología e I+D, Economía y Finanzas Públicas, Educación, Cultura y Turismo, Vivienda y Urbanismo, Gobierno y Sector Público, Demografía y Sociedad) — para cubrir cualquier sector, no solo los de DATAlife (ver [docs/taxonomia.md](docs/taxonomia.md)).
- Inventario de fuentes candidatas por sector, con su estado de verificación técnica: [docs/fuentes.md](docs/fuentes.md).
- **30 datasets reales conectados** desde 13 fuentes distintas — 7 de España/Galicia (abertos.xunta.gal, datos.gob.es, IGE, INE, opendata.esri.es, MeteoGalicia, centro de descargas da Xunta) y 6 internacionales (data.gov.uk en Reino Unido, catálogo de la FAO y la OMS a nivel mundial, GovData en Alemania, data.gov.ie en Irlanda, data.gouv.fr en Francia) — usando 8 mecanismos de recolección (DCAT/RDF, DCAT JSON, cinco conectores a medida, y datasets enlazados a mano cuando la fuente no expone ni API ni catálogo), cubriendo las cuatro cadenas de valor (detalle, avisos de calidad de datos y decisiones técnicas en docs/fuentes.md).
- **Explorador de catálogos** (`/explorar-catalogos`, solo administradores): directorio curado de catálogos de datos abiertos por país/región y sector — incluye ya 15 catálogos investigados y verificados, de España y de fuera — con una máscara de filtrado para decidir qué conectar antes de darlo de alta en el formulario de fuentes.
- Personalización de marca e interfaz: formulario para añadir fuentes de datos manualmente (`/harvest/new`, ya incluido en CKAN) restringido a personas administradoras del sistema, con enlaces directos "Explorar catálogos" y "Fuentes de datos" en su menú de cuenta (extensión `ckan-docker/ckan/local-ext/ckanext-datalifetheme`; detalle en docs/personalizacion.md).
- **Cuadro de mando** (`http://localhost:3000`, enlazado desde la cabecera del portal): [Metabase](https://www.metabase.com/) conectado en modo lectura al DataStore de CKAN, para construir gráficos, mapas y tablas dinámicas sobre los datasets ya cargados en el catálogo, sin salir de la plataforma. Detalle de qué datasets son visualizables hoy y cómo añadir nuevas visualizaciones en [docs/cuadro-de-mando.md](docs/cuadro-de-mando.md).
- **Tutorial para el equipo**: guía paso a paso, sin conocimientos técnicos previos, para buscar datasets en el catálogo y crear gráficos, indicadores, tablas dinámicas, mapas y paneles en Metabase — [docs/tutorial-equipo.md](docs/tutorial-equipo.md).

## Cómo levantar el entorno local

1. Asegúrate de que Docker Desktop está en marcha.
2. Abre una terminal en la carpeta del proyecto y entra en `ckan-docker`:
   ```bash
   cd ckan-docker
   ```
3. Levanta todo el stack:
   ```bash
   docker compose up -d
   ```
4. Espera a que los contenedores estén sanos (`docker compose ps`, especialmente `ckan` y `metabase` en estado `healthy`; `ckan` puede tardar un minuto en el primer arranque).
5. Accede:
   - **Catálogo (CKAN)**: `https://localhost:8443` (certificado autofirmado de desarrollo, hay que aceptar la advertencia del navegador). Credenciales de administrador: usuario `CKAN_SYSADMIN_NAME` y contraseña `CKAN_SYSADMIN_PASSWORD` en `ckan-docker/.env` (no versionado), también recogidas en `ckan-docker/.secrets_generated.txt`.
   - **Cuadro de mando (Metabase)**: `http://localhost:3000`, o desde el enlace "Cuadro de mando" en la cabecera del portal. Correo `raffaele@dihdatalife.com`, contraseña en `ckan-docker/.metabase_password.txt` (no versionado).

Para parar todo: `docker compose down` (los datos persisten en los volúmenes Docker; no borra nada).

Servicios del stack (ver `ckan-docker/docker-compose.yml`):

| Servicio | Función |
|---|---|
| `nginx` | Proxy HTTPS de entrada |
| `ckan` | Aplicación CKAN (catálogo, API, interfaz web) |
| `db` | PostgreSQL |
| `solr` | Índice de búsqueda |
| `redis` | Cola de mensajes para harvesting y jobs |
| `datapusher` | Volcado de recursos tabulares al Datastore |
| `harvest-gather` / `harvest-fetch` | Procesos consumidores de las colas de recolección (`ckan harvester gather-consumer` / `fetch-consumer`) |
| `harvest-scheduler` | Lanza `ckan harvester run` cada 5 minutos para procesar los harvest jobs pendientes |
| `metabase` | Cuadro de mando (BI, Business Intelligence): gráficos, mapas y tablas dinámicas sobre el DataStore |

## Próximos pasos

Ver el estado técnico completo en [docs/fuentes.md](docs/fuentes.md). En resumen: abertos.xunta.gal, datos.gob.es, opendata.esri.es, data.gov.uk, GovData (Alemania), data.gov.ie (Irlanda) y el catálogo de la FAO ya se recolectan vía DCAT (RDF o JSON según el caso), y el IGE, el INE, la OMS (GHO), Francia (data.gouv.fr) y MeteoGalicia ya tienen su propio conector a medida (MeteoGalicia ya con frecuencia automática diaria, sin depender de ejecuciones manuales). data.europa.eu se investigó a fondo y se usa como directorio de descubrimiento (así se encontró Irlanda), no como fuente de harvesting directa — su API de búsqueda no expone RDF ni enlaces de descarga fiables. data.gov (Estados Unidos) se reverificó y sigue bloqueado. El centro de descargas de información xeográfica da Xunta de Galicia se investigó y conectó por completo: 11 datasets (usos do solo, Rede Natura 2000, Rede Galega de Espazos Protexidos, Outros Espazos Protexidos, Reservas da Biosfera, ríos, encoros, Camiño de Santiago, aeródromos, ferrocarril y rede viaria — las capas de la familia "Base Topográfica de Galicia" no traen licencia documentada en la fuente, marcadas como tal). No quedan capas identificadas sin conectar de este centro de descargas. La organización `sandbox-pruebas` ya se retiró.
