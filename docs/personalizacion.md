# Personalización del portal

Extensión: `ckan-docker/ckan/local-ext/ckanext-datalifetheme` (plugin `datalifetheme`).

## 1. Añadir fuentes de datos manualmente (formulario)

CKAN, a través de `ckanext-harvest`, ya trae de serie un formulario web para dar de alta una fuente de recolección: **`/harvest/new`**. No hemos tenido que construir nada nuevo para el formulario en sí: el equipo técnico entra ahí, pega la URL de la API o del catálogo, elige el tipo de fuente (`ckan`, `dcat_rdf`, `dcat_json`, `ige` o `ine`), la cadena de valor (organización) y la frecuencia, y al guardar queda creada una fuente de harvesting real, exactamente igual que las que hemos ido creando por API en las sesiones anteriores.

Lo que sí hemos añadido:

- **Restricción a personas administradoras del sistema**: por defecto, `ckanext-harvest` permite crear una fuente a cualquier persona con permiso de edición en alguna organización (mismo permiso que crear un dataset normal). Se ha restringido para que solo sysadmins puedan hacerlo.
  - **Detalle técnico**: la acción `harvest_source_create` no comprueba permisos por sí misma — delega directamente en `package_create` (fija `data_dict['type'] = 'harvest'` y llama a esa acción). Por eso la función de autorización que hay que interceptar es `package_create`, no `harvest_source_create` como cabría esperar a primera vista; interceptar esta última no tiene ningún efecto porque nunca llega a invocarse. La restricción solo actúa cuando `data_dict.get('type') == 'harvest'`; para cualquier otro dataset se delega en el comportamiento normal de CKAN, así que no afecta a la creación de datasets corrientes por parte de las personas editoras de cada organización.
  - Verificado con una persona editora de prueba (sin ser sysadmin): se le bloquea la creación de una fuente de harvesting con el mensaje "Solo las personas administradoras del sistema pueden añadir fuentes de datos", pero puede seguir creando datasets normales sin problema. Un sysadmin sigue pudiendo crear fuentes sin restricción.
- **Enlace directo "Fuentes de datos"** en el menú de cuenta, junto a "Admin", visible solo para sysadmins (comprobado también con una persona no-sysadmin: no le aparece el enlace).

## 2. Logo de DATAlife y "Powered by CKAN"

- El logo de la esquina superior izquierda (antes el de CKAN) se sustituyó por el logo de DATAlife (`DiH_Logo-Pos-H.svg`, aportado por el equipo), servido como recurso estático de la extensión.
- Como el logo es una versión "positiva" (pensada para fondo claro) y la cabecera de CKAN es azul oscuro, se le añadió un fondo blanco discreto para que se lea bien.
- Debajo del logo, en texto pequeño, aparece "Powered by CKAN".
- Si en el futuro llega una versión del logo pensada para fondo oscuro, basta con sustituir el fichero `ckanext/datalifetheme/public/datalife-logo.svg` dentro de la extensión (no hace falta tocar código) y reconstruir la imagen de Docker.

## Cómo se implementó

Al ser cambios de plantilla e interfaz (no solo de configuración), no bastaba con una opción de `ckan.ini`: se creó una extensión mínima propia que:

1. Registra una carpeta pública (`public/`) con el logo, y una carpeta de plantillas (`templates/`) que sobrescribe el bloque `header_logo` y `header_account_logged` de la cabecera de CKAN mediante `{% ckan_extends %}` (la forma estándar de CKAN de extender una plantilla ya existente sin copiarla entera).
2. Registra una función de autorización encadenada (`chained_auth_function`) sobre `package_create`, siguiendo el patrón que usa el propio CKAN para permitir que varias extensiones cooperen sobre la misma acción sin pisarse.
