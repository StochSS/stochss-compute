#!bash
if [[ $1 == all ]]; then
  coverage run --source=../stochss_compute run_unit_tests.py
  coverage run --source=../stochss_compute run_integration_tests.py
  coverage html
fi
if [[ $1 == unit ]]; then
  if [ -z "$2" ]; then
  coverage run --source=../stochss_compute run_unit_tests.py
  else
  coverage run --source=../stochss_compute run_unit_tests.py -c $2
  fi
  coverage html
fi
