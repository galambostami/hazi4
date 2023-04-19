import json
import subprocess
import urllib
from io import StringIO
import os
import urllib.request
from typing import get_type_hints

from call_function_with_timeout import SetTimeoutDecorator

MASTER_URL = r"https://raw.githubusercontent.com/INBGM0212-2023/exercises/main/week-08/P1081"


def get_exercise_id() -> str:
    return os.path.split(os.path.dirname(os.getcwd()))[-1]


def download_test_conf(exercise_id: str) -> dict[str, str]:
    with urllib.request.urlopen(rf"{MASTER_URL}/{exercise_id[:-2]}/test.json") as resp:
        return json.loads(resp.read().decode("utf-8"))


def download_test_case(exercise_id: str, test_id: str) -> dict[str, str]:
    url = f"{MASTER_URL}/{exercise_id[:-2]}/{test_id}/test"
    with urllib.request.urlopen(f"{url}{exercise_id[-2:]}.in") as resp_in, urllib.request.urlopen(
            f"{url}.out") as resp_out:
        return {
            "in": resp_in.read().decode("utf-8"),
            "out": resp_out.read().decode("utf-8"),
        }


def download_unit_test_suite(exercise_id: str, test_id: str) -> dict[str, str]:
    with urllib.request.urlopen(f"{MASTER_URL}/{exercise_id[:-2]}/{test_id}/test.json") as resp:
        return json.loads(resp.read().decode("utf-8"))


def cmp(expected: any, actual: any, message):
    def dump(value: str, indent=0) -> str:
        if type(value) in {str, int, float}:
            return " " * indent + str(value)
        elif type(value) == list:
            if type(value[0]) in {str, int, float}:
                return " " * indent + str(value)
            else:
                buffer = []
                for i in range(len(value)):
                    buffer.append(f"{i}. {value[i]}")
                return "\n".join(buffer)
        else:
            return " " * indent + str(value)

    assert expected == actual, f"""

WHEN {message}

EXPECTED:
<<
{dump(expected)}
>>

ACTUAL:
<<
{dump(actual)}    
>>
"""


def exception_message(e: Exception, unit_name: str) -> str:
    return f"""

START ============================== UNIT TESTING {unit_name} ==============================

THE FOLLOWING EXCEPTION HAS BEEN THROWN:

{e}

END ================================ UNIT TESTING {unit_name} ==============================
"""


def call(module: object) -> None:
    conf = download_test_conf(get_exercise_id())
    for test_id in conf["tests"]:
        test_suite = download_unit_test_suite(get_exercise_id(), test_id)
        for type_name in test_suite["type-order"]:
            try:
                actual = getattr(module, type_name)
                expected = test_suite["types"][type_name]
                cmp(len(expected), len(actual._fields), f"checking number of fields")
                cmp(list(expected.keys()), list(actual._fields), "checking names of fields")

                cmp(
                    list(expected.values()),
                    [str(v) for v in actual.__annotations__.values()],
                    "checking types of fields"
                )
            except Exception as e:
                raise AssertionError(exception_message(e, type_name)) from None

        for function_name in test_suite["function-order"]:
            for test_case in test_suite["functions"][function_name]:
                try:
                    fun = getattr(module, function_name)
                except Exception as e:
                    raise AssertionError(exception_message(e, f"accessing function {function_name}()")) from None

                arguments = {}
                expected = None

                param_names = list(get_type_hints(getattr(module, function_name)).keys())
                if function_name == "from_line":
                    expected = getattr(module, test_suite["type-order"][0])(**test_case["out"])
                    arguments = test_case["in"]
                elif function_name == "to_line":
                    expected = test_case["out"]
                    arguments = {
                        param_names[0]: getattr(module, test_suite["type-order"][0])(**test_case["in"][param_names[0]])
                    }
                elif function_name == "order":
                    expected = [
                        getattr(module, test_suite["type-order"][0])(**value)
                        for value in test_case["out"]
                    ]
                    arguments = {
                        param_names[0]: [
                            getattr(module, test_suite["type-order"][0])(**value)
                            for value in test_case["in"][param_names[0]]
                        ]
                    }

                results = SetTimeoutDecorator(test_case["limit"])(fun)(**arguments)
                if results[1]:
                    raise AssertionError(
                        exception_message(
                            TimeoutError(f"Function <<{function_name}>> timed out after {test_case['limit']} seconds"),
                            function_name)) from None
                elif not results[0]:
                    raise AssertionError(exception_message(results[2], function_name)) from None
                cmp(expected, results[3], "checking the returned value")


def run() -> None:
    column_ids = ["in", "out", "act"]
    column_names = ["INPUT", "EXPECTED", "ACTUAL"]

    out = StringIO()
    conf = download_test_conf(get_exercise_id())
    for test_id in conf["tests"]:
        test_case = download_test_case(get_exercise_id(), test_id)
        try:
            process = subprocess.run(["python", "solution.py"], input=test_case["in"].encode("utf-8"),
                                     stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=float(conf["timeout-cmd"]),
                                     universal_newlines=False)
        except:
            raise AssertionError(f"""

The following error occurred:

{out}
""") from None

        channels = {
            "in": [line.rstrip("\n") for line in test_case["in"].splitlines()],
            "out": [line.rstrip("\n") for line in test_case["out"].splitlines()],
            "act": [line.rstrip("\n") for line in process.stdout.decode("utf-8").splitlines()],
            "err": [line.rstrip("\n") for line in process.stderr.decode("utf-8").splitlines()]
        }

        merged = []
        for i in range(max(len(channel) for channel in channels.values())):
            merged.append([
                channels[extension][i].replace(" ", "•") if i < len(channels[extension]) else ""
                for extension in column_ids
            ])

        width = [
            max(10, max(len(line) for line in channels[extension]) if channels[extension] else 0)
            for extension in column_ids
        ]

        if process.returncode != 0:
            print("=" * 30, "RUN", test_id, "=" * 30, file=out)
            print("\n".join([f"\t{line}" for line in channels["err"]]), file=out)

            out.seek(0)
            out = "".join(out.readlines())
            raise AssertionError(f"""

The following error occurred:

{out}
""") from None
        elif channels["act"] != channels["out"]:
            sep = {"sep": " | ", "file": out}
            end = {"end": " |\n"}

            print("=" * 30, "RUN", test_id, "=" * 30, file=out)
            print(file=out)
            print(f"{' ':4}", *[f"{column_names[i].center(width[i])}" for i in range(len(column_names))], **sep, **end)
            print(f"{' ':4}", *['-' * w for w in width], **sep, **end)
            for i in range(len(merged)):
                print(f"{i:4}", *[f"{merged[i][n]:{width[n]}}" for n in range(len(column_names))],
                      " " if merged[i][1] == merged[i][2] else "<< !!!", **sep)

            out.seek(0)
            out = "".join(out.readlines())
            raise AssertionError(f"""

The expected and actual outputs differ!
{out}
""") from None
