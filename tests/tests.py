#! /usr/bin/env python3

import os
import sys
import pathlib

sys.path.append(str(pathlib.Path(__file__).parent.parent))
from main import parse, JsVisitor

for case_name in os.listdir(pathlib.Path(__file__).parent /"cases"):
    print(case_name)
    with open(pathlib.Path(__file__).parent /f"cases/{case_name}/input.js") as f:
        prog = f.read()
    expected = None
    if os.path.exists(pathlib.Path(__file__).parent /f"cases/{case_name}/output.py"):
        with open(pathlib.Path(__file__).parent /f"cases/{case_name}/output.py") as f:
            expected = f.read()
    parsed = parse(prog, {"comment": True})
    actual = "\n".join(JsVisitor().visit(parsed)) + "\n"
    if expected:
        assert actual == expected

    # update snapshot
    with open(pathlib.Path(__file__).parent /f"cases/{case_name}/output.py", "w") as f:
        f.write(actual)



# with open("react.py", 'w') as t:
#     with open('react.bundle.js') as f:
#         prog = f.read()
#     parsed = parse(prog, {"comment": True})
#     transformed = JsVisitor().visit(parsed)
#     t.write("\n".join(transformed).replace("\n\n", "\n"))
