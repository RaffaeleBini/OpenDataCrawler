# Tutorial para el equipo: usar el catálogo y crear visualizaciones

Esta guía te explica, paso a paso, cómo usar la plataforma de datos abiertos de DATAlife: cómo buscar y descargar datasets desde el catálogo, y cómo crear gráficos, indicadores, tablas dinámicas, mapas y paneles en Metabase, la herramienta de análisis de datos conectada al catálogo. No necesitas conocimientos técnicos previos para seguirla.

**Antes de empezar**: este documento no cubre cómo instalar la plataforma ni cómo acceder a ella (URL, usuario, contraseña) — pide esa información a la persona responsable del catálogo en tu equipo. Aquí partimos de que ya tienes esos datos y estás dentro de las dos herramientas.

## Acrónimos usados en este documento

- **EDIH**: Hub de Innovación Digital Europeo (European Digital Innovation Hub, por sus siglas en inglés)
- **BI**: Business Intelligence (análisis de datos empresarial)
- **CSV**: Comma-Separated Values (valores separados por comas), un formato de fichero de datos en tabla
- **XLS/XLSX**: formato de hoja de cálculo de Microsoft Excel
- **JSON**: JavaScript Object Notation, un formato de intercambio de datos
- **KPI**: Key Performance Indicator (indicador clave de rendimiento)
- **SQL**: Structured Query Language (lenguaje de consulta estructurado), el lenguaje con el que se hacen preguntas avanzadas a una base de datos
- **UUID**: Universally Unique Identifier (identificador único universal), una cadena de caracteres que identifica algo de forma unívoca

## Qué es esta herramienta

Es el catálogo de datos abiertos de DIH DATALIFE: un punto único donde encontrar, explorar y descargar datasets ya publicados por administraciones públicas y organismos internacionales, organizados por país, sector y cadena de valor (Agro-Mar-Alimentación, Forestal-Madera, Salud-Cuidados y Biotecnología, entre otros sectores). El catálogo no genera datos propios: reúne y ordena datos que ya son abiertos, para que no tengas que buscar fuente por fuente.

Junto al catálogo hay un cuadro de mando (Metabase) conectado a esos mismos datos, para que puedas construir gráficos, mapas y tablas dinámicas sin descargar nada ni usar otra herramienta.

---

## Parte 1 — Usar el catálogo de datos

### Buscar un dataset

En la portada del catálogo tienes un buscador de texto libre: escribe una palabra clave (por ejemplo, "pesca" o "hospitales") y pulsa a buscar. Los resultados muestran el título, el organismo que publica cada dataset y la cadena de valor o sector al que pertenece.

### Filtrar por país y sector

Justo en la portada, junto al buscador, hay un filtro por país/región y por sector. Úsalo cuando quieras explorar qué hay disponible de un país concreto (por ejemplo, Francia o Alemania) o de un sector concreto (por ejemplo, Medio Ambiente y Clima), en vez de buscar por una palabra exacta. Al enviarlo, la página te lleva a los resultados filtrados.

También puedes navegar directamente por organización: cada cadena de valor y cada sector de DATAlife es una organización dentro del catálogo, con su propia página de listado.

### Abrir la ficha de un dataset y descargar un recurso

Al abrir un dataset, encontrarás:

- Un título y una descripción (notas) que explican qué contiene y de dónde procede
- El organismo publicador y la organización/sector de DATAlife a la que se asignó
- La licencia bajo la que se publica
- Uno o varios recursos descargables (CSV, XLS, JSON, entre otros formatos)

Para descargar un recurso, pulsa sobre su nombre y después en el botón de descarga. Si el recurso es un enlace a la fuente original (no un fichero alojado en el propio catálogo), se abrirá esa página externa.

### Explorar catálogos: de dónde vienen los datos

En el menú superior encontrarás un enlace "Explorar catálogos". Esta página no lista datasets sueltos, sino los **catálogos de origen** que el equipo ha investigado (por ejemplo, abertos.xunta.gal, datos.gob.es o el Global Health Observatory de la Organización Mundial de la Salud), con su país, sector y si ya está conectado al catálogo o no. Te sirve como referencia para entender de dónde procede cada fuente de datos; conectar una fuente nueva es una tarea de la persona administradora del sistema, no algo que hagas desde aquí.

### Aviso sobre calidad de los datos de origen

Algunos recursos, tal y como los publica el organismo original, no son ficheros descargables directos: pueden redirigir a una página interactiva, o su enlace puede estar roto. Esto es un problema de la fuente original, no del catálogo. Si un recurso no se descarga como esperas, prueba con otro recurso del mismo dataset o consulta con la persona administradora del sistema.

---

## Parte 2 — Crear analíticas y visualizaciones en Metabase

Metabase es la herramienta de BI conectada al catálogo. Accede a ella desde el enlace "Cuadro de mando" en la cabecera del portal, o directamente con la URL que te haya facilitado tu equipo.

### Conceptos básicos

- **Pregunta** (Question): una visualización individual — un gráfico, un indicador, una tabla o un mapa — construida sobre una tabla de datos
- **Panel** (Dashboard): una colección de preguntas guardadas, organizadas juntas en una sola pantalla
- **Colección** (Collection): una carpeta para organizar preguntas y paneles

### Encontrar la tabla de un dataset

Cada dataset del catálogo que ya se ha cargado en Metabase aparece como una tabla, con el mismo título que tiene en el catálogo (por ejemplo, "Datos del subsector gandeiro bovino 2023"). Si en algún momento ves una tabla con un nombre críptico (una cadena larga de letras y números, un UUID), avisa a la persona administradora del sistema: significa que a esa tabla todavía no se le ha puesto el nombre legible.

### Crear un gráfico de barras o líneas

1. Pulsa en "Nueva pregunta"
2. Elige la tabla que quieras analizar
3. En el panel de resumen, elige qué quieres medir (por ejemplo, sumar o contar una columna) y, si quieres agrupar el resultado (por ejemplo, por concello o por año), añade un "Agrupar por"
4. Ejecuta la pregunta y elige el tipo de visualización de barras o de líneas en el panel de visualización
5. Pulsa "Guardar" y ponle un nombre descriptivo

### Crear un indicador (KPI)

Sigue los mismos pasos que para un gráfico, pero elige la visualización de tipo número ("Number"). Es la opción más clara cuando quieres mostrar un único valor destacado (un total, una media, un máximo) en vez de una serie de datos.

### Crear una tabla dinámica (Pivot Table)

Una tabla dinámica cruza dos dimensiones (por ejemplo, concello y año) con una métrica (por ejemplo, una suma), en una sola tabla. Ya hay un ejemplo real construido sobre el dataset del subsector gandeiro bovino, con todos los concellos y sus columnas de datos, que puedes usar como referencia.

Para construir una nueva:

1. Pulsa en "Nueva pregunta" y elige la tabla
2. En el resumen, añade la métrica y las dos dimensiones por las que quieras agrupar
3. En el panel de visualización, elige el tipo "Tabla dinámica" (Pivot Table)
4. Guarda la pregunta

### Crear un mapa de puntos

**Caso sencillo**: si el dataset ya trae la latitud y la longitud en dos columnas separadas, basta con crear una pregunta normal sobre esa tabla y elegir la visualización de tipo mapa de puntos (pin map); Metabase detecta las columnas de coordenadas automáticamente.

**Caso avanzado — coordenadas combinadas en un solo campo**: algunas fuentes (sobre todo de fuera de España) publican la coordenada como un único campo de texto, con el formato "latitud, longitud" en la misma celda. En ese caso hace falta una consulta en SQL nativo que separe ese campo en dos columnas numéricas antes de poder usar el mapa. Este es el ejemplo real ya usado con un dataset de centros sanitarios de Alemania, con la coordenada combinada en la columna "Geografische Koordinate":

```sql
SELECT "Objektname" AS "Nombre", "Objektart" AS "Tipo", "Ort" AS "Localidad",
       split_part("Geografische Koordinate", ',', 1)::float AS "Latitude",
       split_part("Geografische Koordinate", ',', 2)::float AS "Longitude"
FROM "nombre_de_la_tabla"
```

Puntos clave de esta receta:

- Se abre desde "Nueva pregunta" eligiendo la opción de consulta en SQL nativo, en vez de la pregunta visual normal
- Hay que llamar exactamente `Latitude` y `Longitude` a las dos columnas nuevas: Metabase las reconoce por ese nombre para dibujar el mapa de puntos
- La consulta no modifica el dato original en ningún momento — solo cambia cómo se presenta en esta pregunta concreta

Si tienes dudas para adaptar esta consulta a otro dataset, pide ayuda a la persona administradora del sistema.

### Mapas de región

Además de los mapas de país y de Estados Unidos que trae Metabase de serie, ya hay dos mapas de región propios de Galicia disponibles para usar directamente, sin ningún paso adicional:

- **Comarcas de Galicia**: para usarlo, la columna con el nombre de la comarca en tu pregunta tiene que coincidir exactamente con el nombre oficial (p. ej. "A Barcala", "Terra Chá").
- **Concellos de Galicia**: la columna con el nombre del concello tiene que estar en mayúsculas y con el artículo al principio (p. ej. "O GROVE", no "Grove, O").

Al construir una pregunta con visualización de mapa de región, estos dos aparecen junto a los mapas de país y de EE. UU. en el desplegable de "Región". Si tu tabla no trae el nombre exactamente en ese formato, puedes ajustarlo con una función de texto en la propia consulta (por ejemplo, poniéndolo en mayúsculas), sin modificar el dato original.

### Guardar preguntas y montar un panel (dashboard)

1. Guarda cada pregunta que quieras incluir (ver pasos anteriores)
2. Crea un panel nuevo desde el menú correspondiente, o abre uno ya existente
3. Añade las preguntas guardadas al panel y ordénalas como prefieras
4. Guarda el panel con un nombre descriptivo

Puedes volver a abrir un panel guardado en cualquier momento; las preguntas que contiene se actualizan solas si los datos de origen cambian.

### Buenas prácticas

- Si una columna tiene un nombre poco claro por un problema del fichero de origen, puedes renombrarla en Metabase para tu propia visualización, sin modificar el dato original
- Antes de construir una pregunta nueva desde cero, comprueba si ya existe una pregunta o un panel guardado que te sirva — evita duplicar trabajo
- Usa los filtros de la propia pregunta (por fecha, por categoría) en vez de crear una tabla distinta para cada corte de los mismos datos

---

## ¿Y si necesito una fuente de datos nueva?

Si echas en falta un dataset o una fuente de datos que no está en el catálogo, coméntaselo a la persona administradora del sistema: dar de alta una fuente nueva es una tarea de administración, no algo que puedas hacer desde tu cuenta. Puedes consultar antes "Explorar catálogos" para ver si esa fuente ya está identificada y pendiente de conectar.
