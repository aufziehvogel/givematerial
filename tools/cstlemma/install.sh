#!/usr/bin/env bash

git clone https://github.com/kuhumcst/hashmap.git
git clone https://github.com/kuhumcst/letterfunc.git
git clone https://github.com/kuhumcst/parsesgml.git
git clone https://github.com/kuhumcst/cstlemma.git

mkdir -p models/croatian
wget https://cst.dk/download/cstlemma/croatian/1/flexrules -O models/croatian/flexrules
wget https://cst.dk/download/cstlemma/croatian/dict -O models/croatian/dict

pushd cstlemma/src
make all
popd
