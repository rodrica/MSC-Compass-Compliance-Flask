#!/usr/bin/env bash

usage() {
cat << EOF
usage: $0 options
OPTIONS:
  -e, --environment       Environment
  -h,  --help             Show this message
EOF
}

# Enable or disable colored logs
COLOR_LOG=true

## Color coded logging - https://misc.flogisoft.com/bash/tip_colors_and_formatting
error() {
  if [ $COLOR_LOG = true ]; then
    echo "[31m$1[0m"  # Red FG
  else
    echo "$1"
  fi
}

warn() {
  if [ $COLOR_LOG = true ]; then
    echo "[33m$1[0m"  # Yellow FG
  else
    echo "$1"
  fi
}

info() {
  if [ $COLOR_LOG = true ]; then
    echo "[32m$1[0m"  # Green FG
  else
    echo "$1"
  fi
}

debug() {
  if [ $COLOR_LOG = true ]; then
    echo "[36m$1[0m"  # Cyan FG
  else
    echo "$1"
  fi
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
        info "Shutting down existing test deployment"
        run_cmd "docker-compose -f ./tests/docker-compose.yml -p test down"
        test_exit_code=$?
        if [ $test_exit_code -ne 0 ]; then
            error "Failed to tear existing test deployment!"
            exit $test_exit_code
        fi

        info "Building test images"
        run_cmd "docker-compose -f ./tests/docker-compose.yml -p test build"
        test_exit_code=$?
        if [ $test_exit_code -ne 0 ]; then
            error "Failed to build test deployment!"
            exit $test_exit_code
        fi

        info "Running tests"
        run_cmd "docker-compose -f ./tests/docker-compose.yml -p test run test_runner ${NON_DOCKER_ARGS[*]}"
        test_exit_code=$?

        if [ ! "$KEEP_ALIVE" == true ]; then
          info "Shutting down test deployment"
          run_cmd "docker-compose -f ./tests/docker-compose.yml -p test down"
        fi
        if [ $test_exit_code -ne 0 ]; then
            error "Test failed!"
            exit $test_exit_code
        fi
        info "Completed"
    else
        # Print environment variables if verbose
        if [ "$VERBOSE" == true ]; then
          env
        fi

        if [ "$INIT" == true ]; then
            info "Initializing"
            run_cmd "flask db upgrade"
            run_cmd "python /app/tests/e2e_tests/conftest.py"
            ret=$?
            if [ $ret -ne 0 ]; then
                exit $ret
            fi
        fi

        if [ "$ALL" == true ] || [ "$LINT" == true ]; then
            info "Running Lint Tests"
            run_cmd "flake8"
            ret=$?
            if [ $ret -ne 0 ]; then
                exit $ret
            fi
        fi
        if [ "$ALL" == true ] || [ "$UNITTEST" == true ]; then
            info "Running Unit Tests"
            run_cmd "pyclean ."
            run_tests "tests/unittests"
            ret=$?
            if [ $ret -ne 0 ]; then
                exit $ret
            fi
        fi
        # if [ "$ALL" == true ] || [ "$INTEGRATION" == true ]; then
        #     info "Running Integration Tests"
        #     run_tests "tests/integration_tests"
        #     ret=$?
        #     if [ $ret -ne 0 ]; then
        #         exit $ret
        #     fi
        # fi
        if [ "$ALL" == true ] || [ "$E2E" == true ]; then
            info "Running E2E Tests"
            # sleep for 10 seconds to allow services to start before we start testing
            run_cmd "sleep 10 && flask db upgrade"
            run_tests "--tavern-beta-new-traceback tests/e2e_tests"
            ret=$?

            if [ $ret -ne 0 ]; then
                exit $ret
            fi
        fi
    fi
}

run_tests() {
    CMD="pytest -x --cache-clear -W ignore -r s"
    if [ "$NO_CAPTURE" == true ]; then
        CMD="$CMD --capture=no"
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
NON_DOCKER_ARGS=()
while (("$#")); do
  # Get list of aruments that are not docker
  case "$1" in
    -d|--docker|-k|--keep-alive)
      # Do nothing
      ;;
    *)
      NON_DOCKER_ARGS+=("$1")
      ;;
  esac

  case "$1" in
    -a|--all)
      ALL=true
      shift
      ;;
    --init)
      INIT=true
      shift
      ;;
    # -i|--integration)
    #   INTEGRATION=true
    #   shift
    #   ;;
    -e|--end-to-end)
      E2E=true
      shift
      ;;
    -u|--unittest)
      UNITTEST=true
      shift
      ;;
    -k|--keep-alive)
      KEEP_ALIVE=true
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
