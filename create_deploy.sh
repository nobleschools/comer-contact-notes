#! /bin/bash

mkdir dist
echo "Copying local files to dist/.."
cp -rf src data dist
echo "Copying dependencies to dist/.."
cp -rf ~/.envs/comer_contact_notes/lib/python3.6/site-packages/* dist 1> /dev/null
echo "Zipping to deployment.zip.."
cd dist/; zip -r deployment.zip . 1> /dev/null
cd ..
mv dist/deployment.zip .
echo "Removing dist/.."
rm -rf dist/
