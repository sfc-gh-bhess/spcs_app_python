#!/bin/bash

# Prompt user for input
read -p "What is the image repository URL (SHOW IMAGE REPOSITORIES IN SCHEMA)? " repository_url
read -p "What warehouse can the data API backend use? " warehouse

# Paths to the files
makefile="./Makefile"
spcs_yaml="./fullstack.yaml"

# Copy files
cp $makefile.template $makefile
cp $spcs_yaml.template $spcs_yaml

# Replace placeholders in Makefile file using | as delimiter
sed -i "" "s|<<REPOSITORY>>|$repository_url|g" $makefile

# Replace placeholders in SPCS YAML file using | as delimiter
sed -i "" "s|<<REPOSITORY>>|$repository_url|g" $spcs_yaml
sed -i "" "s|<<WAREHOUSE>>|$warehouse|g" $spcs_yaml

echo "Placeholder values have been replaced!"
echo "Run 'make help' to view the targets."
