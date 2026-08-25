# Personalización del portal

Extensión: `ckan-docker/ckan/local-ext/ckanext-datalifetheme` (plugin `datalifetheme`).

## 1. Añadir fuentes de datos manualmente (formulario)

CKAN, a través de `ckanext-harvest`, ya trae de serie un formulario web para dar de alta una fuente de recolección: **`/harvest/new`**. No hemos tenido que construir nada nuevo para el formulario en sí: el equipo técnico entra ahí, pega la URL de la API o del catálogo, elige el tipo de fuente (`ckan`, `dcat_rdf`, `dcat_json`, `ige` o `ine`), la cadena de valor (organización) y la frecuencia, y al guardar queda creada una fuente de harvesting real, exactamente igual que las que hemos ido creando por API en las sesiones anteriores.

Lo que sí hemos añadido:

- **Restricción a personas administradoras del sistema**: por defecto, `ckanext-harvest` permite crear una fuente a cualquier persona con permiso de edición en alguna organización (mismo permiso que crear un dataset normal). Se ha restringido para que solo sysadmins puedan hacerlo.
  - **Detalle técnico**: la acción `harvest_source_create` no comprueba permisos por sí misma — delega directamente en `package_create` (fija `data_dict['type'] = 'harvest'` y llama a esa acción). Por eso la función de autorización que hay que interceptar es `package_create`, no `harvest_source_create` como cabría esperar a primera vista; interceptar esta última no tiene ningún efecto porque nunca llega a invocarse. La restricción solo actúa cuando `data_dict.get('type') == 'harvest'`; para cualquier otro dataset se delega en el comportamiento normal de CKAN, así que no afecta a la creación de datasets corrientes por parte de las personas editoras de cada organización.
  - Verificado con una persona editora de prueba (sin ser sysadmin): se le bloquea la creación de una fuente de harvesting con el mensaje "Solo las personas administradoras del sistema pueden añadir fuentes de datos", pero puede seguir creando datasets normales sin problema. Un sysadmin sigue pudiendo crear fuentes sin restricción.
- **Enlace directo "Fuentes de datos"** en el menú de cuenta, junto a "Admin", visible solo para sysadmins (comprobado también con una persona no-sysadmin: no le aparece el enlace).

## 2. Logo e identidad de marca de DATAlife

*(Nota: el logo se probó y se revirtió en una sesión anterior, al saberse que DATAlife ya contaba con otra herramienta de este tipo. Esa decisión queda superada: se continúa este desarrollo con la marca de DATAlife aplicada de forma definitiva, junto con la paleta de color oficial.)*

El portal usa el logo oficial de DIH DATALIFE y su paleta de color, sin necesidad de tocar plantillas ni reconstruir la imagen `ckan` para los cambios de color:

- **Logo** (`ckanext/datalifetheme/public/datalife-logo.svg`, logotipo completo) enganchado vía la configuración estándar de CKAN `ckan.site_logo`, aplicada en caliente con la acción de API `config_option_update` (sysadmin).
- **Favicon**: recorte del icono sin el texto "DATAlife" (`ckanext/datalifetheme/public/datalife-icon.svg`, mismo `<defs>`/degradados del logo original, solo los paths del icono), configurado vía `ckan.favicon`. A diferencia del logo, este ajuste **no** es editable en caliente por la API (no está marcado `editable` en la configuración de CKAN); se fija con la variable de entorno `CKAN___CKAN__FAVICON` en `ckan-docker/.env`, que requiere reiniciar el contenedor `ckan` (no reconstruir la imagen) para aplicarse.
- **Colores**: paleta oficial (Teal Green `#00a79d`, Cyan Blue `#00aeef`, Dark Charcoal `#414042`, Off White `#f1f2f2`) aplicada como CSS mediante la configuración `ckan.site_custom_css` (mecanismo nativo de CKAN para CSS a medida, sin necesidad de un pipeline de `webassets` propio): gradiente Teal→Cyan en la cabecera, enlaces y botones primarios en Cyan Blue con estado `hover` en Teal Green, etiquetas en Teal Green, fondo general en Off White.
- **Título del sitio**: `ckan.site_title` actualizado a "DATAlife - Plataforma de Datos Abiertos" (antes, el valor por defecto "CKAN").
- Metabase (el cuadro de mando) mantiene solo el nombre de sitio ya configurado ("Cuadro de mando DATAlife"); el "white-labeling" completo (logo propio, retirar la marca Metabase) es una función de pago no disponible en la edición gratuita desplegada.

## 3. Sectores ampliados (14 organizaciones, no solo las 4 de DATAlife)

Además de Agro-Mar-Alimentación, Forestal-Madera, Salud-Cuidados y Biotecnología, se crearon 10 organizaciones nuevas en CKAN para cubrir cualquier sector: Medio Ambiente y Clima, Energía, Transporte y Movilidad, Ciencia/Tecnología e I+D, Economía y Finanzas Públicas, Educación, Cultura y Turismo, Vivienda y Urbanismo, Gobierno y Sector Público, y Demografía y Sociedad (detalle en [docs/taxonomia.md](taxonomia.md)). La lista completa vive en un único sitio del código (`SECTOR_LABELS` en `plugin.py`), para que el desplegable de sector de la portada y de `/explorar-catalogos` se alimenten siempre de la misma fuente sin duplicar la lista.

## 4. Explorador de catálogos por país y sector

Página nueva, **`/explorar-catalogos`** (solo administradores), pensada para cuando el proyecto amplió su alcance de "Galicia y 4 sectores" a cualquier país y sector. Es un directorio curado de catálogos de datos abiertos, cada uno verificado a mano con una petición real (no un buscador automático), con una máscara de filtrado por país/región y por sector.

- Cada entrada indica: nombre, país/región, sector(es), tecnología (`ckan`, `dcat_rdf`, `dcat_json`, `ige`, `ine` o `custom` si haría falta un conector nuevo), la URL de referencia, notas, y si ya está conectado al catálogo o no.
- El directorio vive en un fichero de datos dentro de la extensión (`ckanext/datalifetheme/data/catalog_directory.json`): para añadir una fuente nueva al explorador basta con añadir una entrada ahí, sin tocar la plantilla ni el código Python.
- La página no conecta nada por sí misma: para cada catálogo listado, indica qué URL y qué tipo de fuente usar en el formulario de "Fuentes de datos" (punto 1).
- El formulario de filtrado (país/región + sector) se muestra también en la **portada**, en el hueco donde antes estaba el cuadro "Search data" de CKAN; al enviarlo, lleva a `/explorar-catalogos` con esos filtros ya aplicados.
- Enlace "Explorar catálogos" en el menú superior, visible para cualquier persona (es una página pública, de solo lectura). "Fuentes de datos" sigue solo en el menú de cuenta, visible únicamente para sysadmins.

## Cómo se implementó

Al ser cambios de plantilla e interfaz (no solo de configuración), no bastaba con una opción de `ckan.ini`: se creó una extensión mínima propia que:

1. Registra una carpeta pública (`public/`) y una de plantillas (`templates/`) que sobrescribe el bloque `header_account_logged` de la cabecera de CKAN mediante `{% ckan_extends %}` (la forma estándar de CKAN de extender una plantilla ya existente sin copiarla entera).
2. Registra una función de autorización encadenada (`chained_auth_function`) sobre `package_create`, siguiendo el patrón que usa el propio CKAN para permitir que varias extensiones cooperen sobre la misma acción sin pisarse.
3. Registra un blueprint de Flask (interfaz `IBlueprint`) con la ruta `/explorar-catalogos`, que lee el directorio JSON y renderiza una plantilla propia con el formulario de filtrado y los resultados.
4. Registra tres funciones auxiliares de plantilla (interfaz `ITemplateHelpers`: `datalife_directory_paises`, `datalife_directory_sectores` y `datalife_sector_labels`) para poder rellenar los desplegables de país y sector, y sus etiquetas legibles, tanto en `/explorar-catalogos` como en la portada, sin duplicar la lista de sectores.
5. Sobrescribe también `home/index.html` (bloque `search`) y el bloque `header_site_navigation_tabs` de la cabecera, para mostrar el formulario en la portada y el enlace "Explorar catálogos" en el menú público.
