#!/bin/bash

echo "Running Tests..."

python $(which pytest) --cov=hdltools/
mv .coverage{,.tests}

echo "Running usage examples / other..."

test_count=0
for file in ./usage/*.py; do
    echo "$file"
    if ! python $(which coverage) run  $file > /dev/null; then
        exit 1 # error
    fi
    ((test_count ++))
    mv .coverage .coverage.usage$test_count
done

# do other tests manually
python $(which coverage) run --source=hdltools ./tools/axi_slave_builder assets/tests/videochk.mmap > /dev/null
mv .coverage .coverage.axislave
python $(which coverage) run --source=hdltools ./tools/mmap_docgen assets/tests/videochk.mmap > /dev/null
mv .coverage .coverage.docgen

virtualenv_root=$(poetry env info -p)
coverage_report_options='-i --omit=usage/*,tests/*,venv/*,tools/*'",${virtualenv_root}"'/*'
coverage combine
coverage html $coverage_report_options
coverage report $coverage_report_options
