#!/bin/bash

export PYENV_ROOT="$HOME/.pyenv"
command -v pyenv >/dev/null || export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init -)"

pyenv shell nxs-parser

cd /Users/domna/fairmat/nomad-parser-nexus/nexusutils/definitions/contributed_definitions/nyaml
for file in NXdispersion*yml
do
nyaml2nxdl --input-file $file
done

nyaml2nxdl --input-file NXdispersive_material.yml

cp /Users/domna/fairmat/nomad-parser-nexus/nexusutils/definitions/contributed_definitions/nyaml/NXdispersion*.nxdl.xml \
/Users/domna/fairmat/nomad-parser-nexus/nexusutils/definitions/contributed_definitions/

cp /Users/domna/fairmat/nomad-parser-nexus/nexusutils/definitions/contributed_definitions/nyaml/NXdispersive_material.nxdl.xml \
/Users/domna/fairmat/nomad-parser-nexus/nexusutils/definitions/contributed_definitions/