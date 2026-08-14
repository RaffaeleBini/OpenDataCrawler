# Plataforma de Datos Abiertos (DATAlife)

Catálogo/agregador de datos abiertos. Nació centrado en Galicia y en las cuatro cadenas de valor del Hub de Innovación Digital Europeo (EDIH, por sus siglas en inglés) DIH DATALIFE (Agro-Mar-Alimentación, Forestal-Madera, Salud-Cuidados y Biotecnología), y ahora amplía su alcance a cualquier país y sector: esas cuatro cadenas de valor siguen existiendo como una opción más, junto a un directorio creciente de catálogos internacionales.

El plan completo (contexto, decisiones, fases) está en `C:\Users\Raffaele-DIHDatalife\.claude\plans\quiero-crear-una-plataforma-ancient-creek.md`.

## Estado actual (Fase 1 — MVP en marcha)

- Motor de catálogo: [CKAN](https://ckan.org) 2.11, desplegado con Docker Compose a partir del repositorio oficial [ckan/ckan-docker](https://github.com/ckan/ckan-docker) (carpeta [ckan-docker/](ckan-docker/)).
- Extensiones de harvesting instaladas: [ckanext-harvest](https://github.com/ckan/ckanext-harvest) (harvester tipo `ckan`, para recolectar de otros CKAN), [ckanext-dcat](https://github.com/ckan/ckanext-dcat) (harvesters tipo `dcat_rdf` para catálogos DCAT/RDF como abertos.xunta.gal o datos.gob.es, y `dcat_json` para el formato DCAT-US JSON de portales ArcGIS Hub como opendata.esri.es) y dos harvesters propios para APIs que no exponen ni CKAN ni DCAT: `ckan-docker/ckan/local-ext/ckanext-igeharvester` (tipo `ige`, para el Instituto Galego de Estatística) y `ckan-docker/ckan/local-ext/ckanext-ineharvester` (tipo `ine`, para el Instituto Nacional de Estadística).
- Taxonomía: 14 organizaciones creadas en CKAN — las 4 cadenas de valor originales de DATAlife más 10 sectores nuevos (Medio Ambiente y Clima, Energía, Transporte y Movilidad, Ciencia/Tecnología e I+D, Economía y Finanzas Públicas, Educación, Cultura y Turismo, Vivienda y Urbanismo, Gobierno y Sector Público, Demografía y Sociedad) — para cubrir cualquier sector, no solo los de DATAlife (ver [docs/taxonomia.md](docs/taxonomia.md)).
- Inventario de fuentes candidatas por sector, con su estado de verificación técnica: [docs/fuentes.md](docs/fuentes.md).
- **14 datasets reales conectados** desde 7 fuentes distintas — 5 de España/Galicia (abertos.xunta.gal, datos.gob.es, IGE, INE, opendata.esri.es) y 2 internacionales (data.gov.uk en Reino Unido, catálogo de la FAO a nivel mundial) — usando 4 mecanismos de recolección (DCAT/RDF, DCAT JSON, y dos conectores a medida), cubriendo las cuatro cadenas de valor (detalle, avisos de calidad de datos y decisiones técnicas en docs/fuentes.md).
- **Explorador de catálogos** (`/explorar-catalogos`, solo administradores): directorio curado de catálogos de datos abiertos por país/región y sector — incluye ya 12 catálogos investigados y verificados, de España y de fuera — con una máscara de filtrado para decidir qué conectar antes de darlo de alta en el formulario de fuentes.
- Personalización de marca e interfaz: formulario para añadir fuentes de datos manualmente (`/harvest/new`, ya incluido en CKAN) restringido a personas administradoras del sistema, con enlaces directos "Explorar catálogos" y "Fuentes de datos" en su menú de cuenta (extensión `ckan-docker/ckan/local-ext/ckanext-datalifetheme`; detalle en docs/personalizacion.md).

## Cómo levantar el entorno local

```bash
cd ckan-docker
docker compose up -d
```

CKAN queda accesible en `https://localhost:8443` (certificado autofirmado de desarrollo, hay que aceptar la advertencia del navegador). Las credenciales de administrador están en `ckan-docker/.env` (no versionado) y en `ckan-docker/.secrets_generated.txt`.

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

## Próximos pasos

Ver el estado técnico completo en [docs/fuentes.md](docs/fuentes.md). En resumen: abertos.xunta.gal, datos.gob.es, opendata.esri.es, data.gov.uk y el catálogo de la FAO ya se recolectan vía DCAT (RDF o JSON según el caso), y el IGE y el INE ya tienen su propio conector a medida. Quedan en el directorio, investigados pero sin conector todavía: data.europa.eu, la OMS (GHO), Francia (data.gouv.fr) y Alemania (GovData) — y MeteoGalicia, de las fuentes gallegas. data.gov (Estados Unidos) quedó pendiente de reverificar. Queda decidir cómo seguir escalando por país/sector, y retirar la organización `sandbox-pruebas` antes de producción.
