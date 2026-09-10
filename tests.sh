#!/bin/bash
set -euo pipefail

if [[ ${VIRTUAL_ENV:-} == "" ]]; then
    # shellcheck disable=SC1091
    source "$(poetry env info --path)/bin/activate"
fi

fail=0

echo "INFO: running Tests..."

python "$(which pytest)" --cov=hdltools/
mv .coverage .coverage.tests

echo "INFO: running usage examples / other..."

test_count=0
shopt -s nullglob
for file in ./usage/*.py; do
    echo "$file"
    if ! python "$(which coverage)" run "$file" > /dev/null; then
        echo "ERROR: usage example $file failed"
        fail=1
    fi
    test_count=$((test_count + 1))
    mv .coverage ".coverage.usage$test_count"
done

# do other tests manually — exit codes must fail the job (HDLTOOLS-0001 / A2)
echo "INFO: test AXI MM-slave builder"
if ! python "$(which coverage)" run --source=hdltools "$(which axi_slave_builder)" assets/tests/videochk.mmap > /dev/null; then
    echo "ERROR: axi_slave_builder failed on assets/tests/videochk.mmap"
    fail=1
fi
mv .coverage .coverage.axislave

if ! python "$(which coverage)" run --source=hdltools "$(which mmap_docgen)" assets/tests/videochk.mmap > /dev/null; then
    echo "ERROR: mmap_docgen failed on assets/tests/videochk.mmap"
    fail=1
fi
mv .coverage .coverage.docgen

# test input generator
echo "INFO: test input generator scripts"
mkdir -p tmp
if ! python "$(which coverage)" run --source=hdltools "$(which vgc)" assets/tests/input1.vg --output tmp/input.json; then
    echo "ERROR: vgc failed on assets/tests/input1.vg"
    fail=1
fi
mv .coverage .coverage.vgc

if ! python "$(which coverage)" run --source=hdltools "$(which inputgen)" tmp/input.json --output tmp/input.txt; then
    echo "ERROR: inputgen failed on tmp/input.json"
    fail=1
fi
mv .coverage .coverage.inputgen

rm -rf tmp

virtualenv_root=$(poetry env info -p)
coverage_report_options="-i --omit=usage/*,tests/*,venv/*,tools/*,${virtualenv_root}/*"
coverage combine
coverage html $coverage_report_options
coverage report $coverage_report_options

if [[ "$fail" -ne 0 ]]; then
    echo "ERROR: one or more smoke steps failed"
    exit 1
fi

echo "INFO: done"
