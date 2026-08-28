FROM ckan/ckan-base:2.11

# Install any extensions needed by your CKAN instance
# See Dockerfile.dev for more details and examples

# ckan-base runs as the non-root 'ckan' user by default, which cannot write
# to /srv/app; switch to root to install extensions, matching the pattern CKAN
# itself uses later in this file before switching back to 'ckan' for patches.
USER root

### Harvester (DATAlife: agregar/recolectar catalogos externos) ###
# Modern ckanext-harvest declares its dependencies via pyproject.toml/setup.py,
# no separate requirements.txt to install.
RUN pip3 install -e 'git+https://github.com/ckan/ckanext-harvest.git@master#egg=ckanext-harvest'

### DCAT (DATAlife: harvester DCAT RDF/JSON, p.ej. datos.gob.es, data.europa.eu) ###
RUN pip3 install -e 'git+https://github.com/ckan/ckanext-dcat.git@master#egg=ckanext-dcat' && \
    pip3 install -r ${APP_DIR}/src/ckanext-dcat/requirements.txt

### IGE (DATAlife: harvester a medida para la API REST del Instituto Galego
### de Estatistica, que no expone catalogo CKAN ni DCAT) ###
COPY --chown=ckan-sys:ckan-sys local-ext/ckanext-igeharvester ${APP_DIR}/src/ckanext-igeharvester
RUN pip3 install -e ${APP_DIR}/src/ckanext-igeharvester

### INE (DATAlife: harvester a medida para la API Tempus3 del Instituto
### Nacional de Estadistica, que tampoco expone catalogo CKAN ni DCAT) ###
COPY --chown=ckan-sys:ckan-sys local-ext/ckanext-ineharvester ${APP_DIR}/src/ckanext-ineharvester
RUN pip3 install -e ${APP_DIR}/src/ckanext-ineharvester

### OMS/GHO (DATAlife: harvester a medida para la API OData del Global
### Health Observatory, que tampoco expone catalogo CKAN ni DCAT) ###
COPY --chown=ckan-sys:ckan-sys local-ext/ckanext-ghoharvester ${APP_DIR}/src/ckanext-ghoharvester
RUN pip3 install -e ${APP_DIR}/src/ckanext-ghoharvester

### Francia/data.gouv.fr (DATAlife: harvester a medida para la API JSON de
### la plataforma udata, que tampoco expone catalogo CKAN ni DCAT) ###
COPY --chown=ckan-sys:ckan-sys local-ext/ckanext-dgfharvester ${APP_DIR}/src/ckanext-dgfharvester
RUN pip3 install -e ${APP_DIR}/src/ckanext-dgfharvester

### MeteoGalicia (DATAlife: harvester a medida para los servicios JSON de
### la red de estaciones meteorologicas, que tampoco expone catalogo CKAN
### ni DCAT) ###
COPY --chown=ckan-sys:ckan-sys local-ext/ckanext-mgharvester ${APP_DIR}/src/ckanext-mgharvester
RUN pip3 install -e ${APP_DIR}/src/ckanext-mgharvester

### Tema DATAlife (logo propio, "powered by CKAN", formulario de fuentes
### de datos restringido a sysadmins) ###
COPY --chown=ckan-sys:ckan-sys local-ext/ckanext-datalifetheme ${APP_DIR}/src/ckanext-datalifetheme
RUN pip3 install -e ${APP_DIR}/src/ckanext-datalifetheme

# Copy custom initialization scripts
COPY --chown=ckan-sys:ckan-sys docker-entrypoint.d/* /docker-entrypoint.d/

# Entrypoint used by auxiliary services (harvest gather/fetch consumers,
# harvest scheduler) that need the same init as start_ckan.sh but run a
# CKAN CLI command instead of the web server.
COPY --chown=ckan-sys:ckan-sys docker-entrypoint-worker.sh ${APP_DIR}/docker-entrypoint-worker.sh
RUN chmod +x ${APP_DIR}/docker-entrypoint-worker.sh

# Apply any patches needed to CKAN core or any of the built extensions (not the
# runtime mounted ones)
COPY --chown=ckan-sys:ckan-sys patches ${APP_DIR}/patches

USER ckan

RUN for d in $APP_DIR/patches/*; do \
        if [ -d $d ]; then \
            for f in `ls $d/*.patch | sort -g`; do \
                cd $SRC_DIR/`basename "$d"` && echo "$0: Applying patch $f to $SRC_DIR/`basename $d`"; patch -p1 < "$f" ; \
            done ; \
        fi ; \
    done
