#!/usr/bin/env bash

usage() {
cat << EOF
usage: $0 options
OPTIONS:
  -e, --environment       Environment
  -h,  --help             Show this message
EOF
}

error() {
  echo "[31m$1[0m"
}

warn() {
  echo "[33m$1[0m"
}

info() {
  echo "[32m$1[0m"
}

debug() {
  echo "[36m$1[0m"
}

# Run command and if an error occured, print stderr via the 'error' function (i.e.: color code stderr)
run_cmd() {
    eval "$1" 2>/tmp/log.err
    ret=$?
    if [ $ret -ne 0 ]; then
        error "$(cat /tmp/log.err)"
    fi

    return $ret
}


main() {
    if [ "$DOCKER" == true ]; then
        run_cmd "docker-compose -f ./tests/docker-compose.yml -p test build"
        run_cmd "NO_CACHE=true docker-compose -f ./tests/docker-compose.yml -p test up --exit-code-from test_runner"
        ret=$?
        if [ $ret -ne 0 ]; then
            exit $ret
        fi
        info "Completed with 'NO_CACHE=true'"
        # run_cmd "NO_CACHE=false docker-compose -f ./tests/docker-compose.yml -p test up --exit-code-from test_runner"
        # info "Completed with 'NO_CACHE=false'"
    else
        env
        if [ "$ALL" == true ] || [ "$LINT" == true ]; then
            run_cmd "flake8"
            ret=$?
            if [ $ret -ne 0 ]; then
                exit $ret
            fi
        fi
        if [ "$ALL" == true ] || [ "$UNITTEST" == true ]; then
            run_tests "tests/unittests"
            ret=$?
            if [ $ret -ne 0 ]; then
                exit $ret
            fi
        fi
        if [ "$ALL" == true ] || [ "$INTEGRATION" == true ]; then
            run_tests "tests/integration_tests"
            ret=$?
            if [ $ret -ne 0 ]; then
                exit $ret
            fi
        fi
        if [ "$ALL" == true ] || [ "$E2E" == true ]; then
            run_tests "--tavern-beta-new-traceback tests/e2e_tests"
            ret=$?

            if [ $ret -ne 0 ]; then
                exit $ret
            fi
        fi
    fi
}

run_tests() {
    CMD="pytest -x --cache-clear -W ignore"
    if [ "$NO_CAPTURE" == true ]; then
        CMD="$CMD --show-capture=no"
    fi
    if [ "$VERBOSE" == true ]; then
        CMD="$CMD -vv"
    fi
    CMD="$CMD $1"

    run_cmd "$CMD"
}


#############################################
# Parse Arguments
#############################################
while (("$#")); do
  case "$1" in
    -a|--all)
      ALL=true
      shift
      ;;
    -i|--integration)
      INTEGRATION=true
      shift
      ;;
    -e|--end-to-end)
      E2E=true
      shift
      ;;
    -u|--unittest)
      UNITTEST=true
      shift
      ;;
    -l|--lint)
      LINT=true
      shift
      ;;
    -n|--no-capture)
      NO_CAPTURE=true
      shift
      ;;
    -d|--docker)
      DOCKER=true
      shift
      ;;
    -v|--verbose)
      VERBOSE=true
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    --) # end argument parsing
      shift
      break
      ;;
    *)
      usage
      exit 1
      ;;
  esac
done

# Execute main function
main
