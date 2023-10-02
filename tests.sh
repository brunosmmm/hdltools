#!/bin/bash

if [[ $VIRTUAL_ENV == "" ]]; then
    source `poetry env info --path`/bin/activate
fi

echo "INFO: running Tests..."

python $(which pytest) --cov=hdltools/
mv .coverage{,.tests}

echo "INFO: running usage examples / other..."

test_count=0
for file in ./usage/*.py; do
    echo "$file"
    if ! python $(which coverage) run  $file > /dev/null 2> /dev/null; then
        echo "ERROR: usage example $file failed"
    fi
    ((test_count ++))
    mv .coverage .coverage.usage$test_count
done

# do other tests manually
echo "INFO: test AXI MM-slave builder"
python $(which coverage) run --source=hdltools $(which axi_slave_builder) assets/tests/videochk.mmap > /dev/null 2> /dev/null
mv .coverage .coverage.axislave
python $(which coverage) run --source=hdltools $(which mmap_docgen) assets/tests/videochk.mmap > /dev/null
mv .coverage .coverage.docgen

# test input generator
echo "INFO: test input generator scripts"
mkdir -p tmp
python $(which coverage) run --source=hdltools $(which vgc) assets/tests/input1.vg --output tmp/input.json
mv .coverage .coverage.vgc
python $(which coverage) run --source=hdltools $(which inputgen) tmp/input.json --output tmp/input.txt
mv .coverage .coverage.inputgen

rm -rf tmp

virtualenv_root=$(poetry env info -p)
coverage_report_options='-i --omit=usage/*,tests/*,venv/*,tools/*'",${virtualenv_root}"'/*'
coverage combine
coverage html $coverage_report_options
coverage report $coverage_report_options

echo "INFO: done"
