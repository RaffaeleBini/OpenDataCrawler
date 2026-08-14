#!/bin/bash

if [[ $CKAN__PLUGINS == *"harvest"* ]]; then
   echo "Applying ckanext-harvest database migrations"
   ckan -c $CKAN_INI db upgrade -p harvest
else
   echo "Not configuring ckanext-harvest (plugin not enabled)"
fi
