from esprima.visitor import NodeVisitor, Visited
from esprima import parse
from random import randint

class JsVisitor(NodeVisitor):
    indentLevel = 0
    in_class = False
    i = -1
    oldHeads = []
    heads = [
"""from js2py.base import *
from js2py.constructors.jsmath import Math
from js2py.constructors.jsdate import Date
from js2py.constructors.jsobject import Object
from js2py.constructors.jsfunction import Function
from js2py.constructors.jsstring import String
from js2py.constructors.jsnumber import Number
from js2py.constructors.jsboolean import Boolean
from js2py.constructors.jsregexp import RegExp
from js2py.constructors.jsarray import Array
from js2py.constructors.jsarraybuffer import ArrayBuffer
from js2py.constructors.jsint8array import Int8Array
from js2py.constructors.jsuint8array import Uint8Array
from js2py.constructors.jsuint8clampedarray import Uint8ClampedArray
from js2py.constructors.jsint16array import Int16Array
from js2py.constructors.jsuint16array import Uint16Array
from js2py.constructors.jsint32array import Int32Array
from js2py.constructors.jsuint32array import Uint32Array
from js2py.constructors.jsfloat32array import Float32Array
from js2py.constructors.jsfloat64array import Float64Array
from js2py.prototypes.jsjson import JSON
from js2py.host.console import console
from js2py.host.jseval import Eval
from js2py.host.jsfunctions import parseFloat, parseInt, isFinite, \
    isNaN, escape, unescape, encodeURI, decodeURI, encodeURIComponent, decodeURIComponent
"""
    ]
    current_params = None

    def indent(self):
        self.indentLevel += 1

    def dedent(self):
        self.indentLevel -= 1

    def getIndent(self):
        return "    " * self.indentLevel

    def setHeads(self, heads):
        self.oldHeads = [x for x in self.heads]
        self.heads = heads

    def unSetHeads(self):
        self.heads = self.oldHeads

    def randnum(self):
        self.i += 1
        return self.i

    def visit_Object(self, node):
        return Visited(node)

    def visit_Script(self, node):
        ret = []
        for item in node.body:
            ret.append(self.visit(item))
        return self.heads + ret

    def visit_Program(self, node):
        return self.visit(node)

    def visit_Identifier(self, node):
        name = node.name
        if name == "global":
            name = "globals"
        if name == "Error":
            name = "Exception"
        return name

    # Functions
    def visit_FunctionDeclaration(self, node, param=None, direct=True):
        d = f'\n{self.getIndent()}@Js\n' if True else ''
        head = f"{d}{self.getIndent()}{'async ' if node.isAsync else ''}def {self.visit(node.id)}"
        params = f", ".join(self.visit(i) for i in ((param or []) + node.params))
        self.current_params = params
        head = head + f"({params}):\n"
        
        heads = []
        old = self.heads

        self.indent()
        self.setHeads(heads)
        body = (self.getIndent() if node.expression is True else "") + self.visit(node.body)
        self.setHeads(old)
        self.dedent()

        return head + f"".join(f"{i}\n{self.getIndent()}" for i in heads) + body

    def visit_FunctionExpression(self, node, name=None, heads=None, direct=True):
        if name:
            node.id = name
            nm = name
        else:
            num = self.randnum()
            nm = "_anonymous_func_" + f"{num}"
            node.id = nm
        

        body = self.visit_FunctionDeclaration(node, param=["this", "arguments"], direct=direct)
        heads = heads or self.heads

        heads.append(body)

        return nm

    def visit_AsyncFunctionDeclaration(self, node, *a, **kw):
        return self.visit_FunctionDeclaration(node, *a, direct=False, **kw)

    def visit_ArrowFunctionExpression(self, node, name="_", *a, **kw):
        return self.visit_FunctionExpression(node, name, *a, **kw)

    def BaseStatement(self, node, key):
        type = node.argument.type if node.argument else ""
        if node.argument and ("Expression" in type and type in ["UnaryExpression", "SequenceExpression", "UpdateExpression", "AssignmentExpression"]):
            if type == "SequenceExpression":
                last = node.argument.expressions.pop()
                return f"{self.visit(node.argument)}\n{self.getIndent()}{key} {self.visit(last)}"
            return f"{self.visit(node.argument)}\n{self.getIndent()}{key} {self.visit(node.argument.argument)}"
        return f"{key} {self.visit(node.argument)}"

    def visit_ReturnStatement(self, node):
        return self.BaseStatement(node, key="return")

    def visit_YieldExpression(self, node):
        return self.BaseStatement(node, key="yield")

    def visit_ThrowStatement(self, node):
        return self.BaseStatement(node, key="raise")

    # Block Statement
    def visit_BlockStatement(self, node):
        if node.body:
            ret = "\n" + f"\n".join([f"{self.getIndent()}{self.visit(i)}" if i.directive != "use strict" else "" for i in node.body])
        else:
            ret = f"{self.getIndent()}pass"
        return ret

    # Rest and Spread
    def visit_RestElement(self, node, isObject=False):
        return ("**" if isObject else "*") + self.visit(node.argument)

    def visit_SpreadElement(self, node, isObject=False):
        return ("**" if isObject else "*") + self.visit(node.argument)

    # If Statement
    def visit_IfStatement(self, node):
        head = f"if {self.visit(node.test)}:\n"
        heads = []

        self.indent()
        old = self.heads
        self.setHeads(heads)
        body = (self.getIndent() if node.consequent.type != "BlockStatement" else "") + self.visit(node.consequent)
        self.setHeads(old)
        self.dedent()

        alt = ""
        if node.alternate:
            if node.alternate.type == "IfStatement":
                cond = f"\n{self.getIndent()}el"
            else:
                cond = f"\n{self.getIndent()}else:\n"
                self.indent()
                alt = cond + self.visit(node.alternate)
                self.dedent()

        return head + f"{self.getIndent()}".join(f"{i}\n" for i in heads) + body + alt

    # Literals
    def visit_Literal(self, node):
        return repr(node.value)
    
    def visit_TemplateElement(self, node):
        return node.value.cooked

    def visit_TemplateLiteral(self, node):
        ret = f'f"""'
        for i, word in enumerate(node.quasis):
            try: ex = "{%s}"%self.visit(node.expressions[i])
            except IndexError: ex = ""
            ret = ret + f"{self.visit(word)}{ex}"
        ret = ret + '"""'
        return ret

    def visit_RegexLiteral(self, node):
        return repr(node.value)

    # Switch Case
    def visit_SwitchStatement(self, node):
        head = f"match {self.visit(node.discriminant)}:\n"

        self.indent()
        cases = []
        for cas in node.cases:
            cases.append(self.visit(cas))
        body = "\n".join(f"{self.getIndent()}{i}" for i in cases)
        self.dedent()

        return head + body

    def visit_SwitchCase(self, node):
        if node.test:
            head = f"case {self.visit(node.test)}:\n"
        else:
            head = "default:\n"

        self.indent()
        cases = []
        for cas in node.consequent:
            cases.append(self.visit(cas))
        body = "\n".join(f"{self.getIndent()}{i}" for i in cases)
        self.dedent()

        return head + body

    # Variables
    def visit_VariableDeclaration(self, node, default=True):
        decls = []
        for dec in node.declarations:
            if dec.type == "VariableDeclarator":
                decls.append(self.visit_VariableDeclarator(dec, default=default, is_global=(node.kind == "var")))
            else:
                decls.append(self.visit(dec))
        return f"\n" + f"".join(f"\n{self.getIndent()}{i}" for i in decls)

    def visit_VariableDeclarator(self, node, default=True, is_global=False):
        # print("VarDec", node)
        # heads = []
        tails = []
        # self.setHeads(heads)
        if node.init:
            if "Function" in node.init.type:
                name = self.visit(node.id)
                self.visit_FunctionExpression(node.init, name=name, direct=True)
                # body = self.getIndent() + f"{self.visit(node.id)} = {name}"
                # return head + "\n" + body
                val = name
            elif node.init.type in ["CallExpression", "NewExpression"]:
                b = self.visit_CallExpression(node.init)
                val = b
            else:
                val = self.visit(node.init)
        else:
            val = "None"

        if node.id.type == "ObjectPattern":
            num = self.randnum()
            key = None
            tail = f"del _temp_{num}"

            self.heads.append(f"_temp_{num} = {val}")

            for prop in node.id.properties:
                k = self.visit(prop.key)
                self.heads.append(f"{k} = _temp_{num}.{k}")

            tails.append(tail)
        else:
            key = self.visit(node.id)

        # self.unSetHeads()

        if default:
            main = f"{key} = {val}"
        else:
            main = f"{key}"

        return ((main if key else "")
            + ("".join(f"\n{self.getIndent()}{tails}") if tails else "")
        )

    # Expressions
    def visit_SequenceExpression(self, node):
        return "; ".join(self.visit(i) for i in node.expressions)

    def visit_UpdateExpression(self, node):
        if node.operator == "++":
            node.operator = "+=1"
        if node.operator == "--":
            node.operator = "-=1"
        return f"{self.visit(node.argument)}{node.operator}"

    def visit_UnaryExpression(self, node):
        a = self.visit(node.argument)
        op = node.operator

        if op == "!":
            op = "not"
        elif op == "delete":
            op = "del"
        elif op == "void":
            op = ""
        elif op == "typeof":
            return f"type(globals().get('{a}'))"

        pre = op if node.prefix else a
        suf = a if node.prefix else op

        return f"{pre} {suf}"

    def visit_ExpressionStatement(self, node):
        return self.visit(node.expression)
    
    def visit_EmptyStatement(self, node):
        return f""
    
    def visit_BreakStatement(self, node):
        return f"break"
    
    def visit_ContinueStatement(self, node):
        return f"continue"

    def visit_ConditionalExpression(self, node):
        return f"{self.visit(node.consequent)} if {self.visit(node.test)} else {self.visit(node.alternate)}"

    def visit_AssignmentExpression(self, node):
        return f"{self.visit(node.left)} {node.operator} {self.visit(node.right)}"

    def visit_AssignmentPattern(self, node):
        node.operator = "="
        return self.visit_AssignmentExpression(node)

    def visit_BinaryExpression(self, node):
        if node.operator == "&&":
            node.operator = "and"
        elif node.operator == "||":
            node.operator = "or"
        elif node.operator == "===":
            node.operator = "=="
        elif node.operator == "!==":
            node.operator = "!="
        return self.visit_AssignmentExpression(node)

    def visit_CallExpression(self, node, prepend=None):
        # print(node)
        # heads = []
        # if decorate and len(node.arguments) == 1:
        #     if "Function" in node.arguments[0].type:
        #         head = f"@{self.visit(node.callee)}\n"
        #         num = self.randnum()
        #         name = "_anonymous_func_" + f"{num}"
        #         body = self.visit_FunctionExpression(node.arguments[0], name=name)
        #         return self.getIndent() + head + body

        if "Function" in node.callee.type:
            num = self.randnum()
            name = "_anonymous_func_" + f"{num}"
            self.visit_FunctionExpression(node.callee, name=name, direct=False)
            callee = name
        else:
            callee = self.visit(node.callee)

        arg = []
        # self.setHeads(heads)
        for i in node.arguments:
            if "Function" in i.type:
                num = self.randnum()
                name = "_anonymous_func_" + f"{num}"
                self.visit_FunctionExpression(i, name=name, direct=False)
                arg.append(name)
            else:
                arg.append(self.visit(i))
        args = ", ".join(arg)
        # self.unSetHeads()

        return f"{prepend if prepend else ''}{callee}({args})"

    def visit_NewExpression(self, node):
        return self.visit_CallExpression(node)

    def visit_ArrayExpression(self, node):
        body = self.visit_ArrayPattern(node)
        return f"Js([{body}])"

    def visit_ArrayPattern(self, node):
        return ", ".join([self.visit(i) if i else "" for i in node.elements])

    def visit_ObjectExpression(self, node):
        return self.visit_ObjectPattern(node)

    def visit_ObjectPattern(self, node):
        # has_heads = self.heads is not None
        # heads = []
        # self.setHeads(heads)

        body = (
            "{"
            + ", ".join(
                [
                    (
                        self.visit_Property(i)
                        if i.type != "RestElement"
                        else self.visit_RestElement(i, isObject=True)
                    )
                    for i in node.properties
                ]
            )
            + "}"
        )

        return body

    def visit_Property(self, node):
        key = self.visit(node.key)

        if node.key.type == "Identifier":
            key = f"'{key}'"

        if node.value.type == "FunctionExpression":
            num = self.randnum()
            name = "_anonymous_func_" + self.visit(node.key) + f"{num}"
            self.visit_FunctionExpression(node.value, name=name)
            return f"{key}: {name}"
        else:
            return f"{key}: {self.visit(node.value)}"

    def visit_StaticMemberExpression(self, node):
        return f"{self.visit(node.object)}.{self.visit(node.property)}"

    def visit_ComputedMemberExpression(self, node):
        return f"{self.visit(node.object)}[{self.visit(node.property)}]"

    # Classes
    def visit_ClassDeclaration(self, node):
        head = f"class {self.visit(node.id)}"
        head = (
            head
            + f"({self.visit(node.superClass) if node.superClass else 'object'}):\n"
        )

        self.indent()
        self.in_class = True
        body = self.visit(node.body)
        self.in_class = False
        self.dedent()

        return head + body

    def visit_ClassBody(self, node):
        if node.body:
            return "\n".join(f"{self.getIndent()}{self.visit(i)}" for i in node.body)
        else:
            return self.getIndent() + "pass"

    def visit_MethodDefinition(self, node):
        head = f"@staticmethod\n{self.getIndent()}" if node.static else ""
        node.value.params.insert(0, "self")

        node.value.id = node.key
        body = self.visit_FunctionDeclaration(node.value)
        return head + body

    def visit_ThisExpression(self, node):
        if self.in_class:
            return "self"
        else:
            return "this"

    # For loop
    def visit_ForInStatement(self, node):
        head = f"for {self.visit(node.left) if node.left.type != 'VariableDeclaration' else self.visit_VariableDeclaration(node.left, default=False)} in {self.visit(node.right)}:\n"

        self.indent()
        body = self.visit(node.body)
        self.dedent()

        return head + body

    def visit_ForOfStatement(self, node):
        return self.visit_ForInStatement(node)

    def visit_ForStatement(self, node):
        head = f"{self.visit(node.init)}\n{self.getIndent()}"
        head = head + f"while {self.visit(node.test)}:\n"

        self.indent()
        body = self.visit(node.body)
        body = f"{self.getIndent()}" + body + f"\n{self.getIndent()}{self.visit(node.update)}"
        self.dedent()

        return head + body

    # While Loop
    def visit_WhileStatement(self, node):
        head = f"while {self.visit(node.test)}:\n"

        self.indent()
        body = self.visit(node.body)
        self.dedent()

        return head + body

    # Do While loop
    def visit_DoWhileStatement(self, node):
        return self.visit_WhileStatement(node)
    
    def visit_TryStatement(self, node):
        head = f"try:\n"
        self.indent()
        body = self.visit(node.block)
        self.dedent()
        handler = (f"\n{self.getIndent()}" + self.visit(node.handler) if node.handler else "")
        finalizer = (f"\n{self.getIndent()}" + self.visit(node.finalizer) if node.finalizer else "")
        return head + body + handler + finalizer
    
    def visit_CatchClause(self, node):
        head = f"except Exception as {self.visit(node.param)}:\n"
        self.indent()
        body = self.visit(node.body)
        self.dedent()
        return head + body

# prog = r"async function ev(a, ...b) {}"

# prog = "let a, b = function() {}, c = 2, c = 19"

# prog = "let [a, b] = [1, 2]"

# prog = "sayname(function() {})"

# prog = r"if (true) {} else if (false) {} else {}"

# prog = r"""switch (ages) {
#     case 17:
#         let a = "Hello World";
#     case 12, 89:
#         ret += 12;
#         ret ++;
#     default:
#         console.log('Hello World..', [1,2,4,5])
# }"""

# prog = """class Ages {
# }"""

# prog = """class Ages {
#     method() {}
# }"""

# prog = """class Ages {
#     constructor() {
#         this.age = 7;
#     }
#     method() {}
# }"""

# prog = """for (let i = 0; i < 100; i++) {
#     console.log(i)
# }"""

# prog = "do {} while (true)"

# prog = "let name = age => {console.log(age)}"

# prog = "if (true) console.log('Hiii') "

# prog = "true ? console.log('Hiii') : log('Nope')"

# prog = "let { x, y, ...z } = { x: 1, y: 2, a: 3, b: 4 };"

# prog = "const x = (x, y) => { return x * y };"

# prog = """
# const q1 = ["Jan", "Feb", "Mar"];
# const q2 = ["Apr", "May", "Jun"];
# const q3 = ["Jul", "Aug", "Sep"];
# const q4 = ["Oct", "Nov", "May"];

# const year = [...q1, ...q2, ...q3, ...q4];
# """

# prog = '''const numbers = [23,55,21,87,56];
# let maxValue = Math.max(...numbers);'''
# prog = '''const fruits = new Map([
# ["apples", 500],
# ["bananas", 300],
# ["oranges", 200]
# ]);'''

# prog = '''class Car {
#   constructor(name, year) {
#     this.name = name;
#     this.year = year;
#   }
# }
# const myCar1 = new Car("Ford", 2014);
# const myCar2 = new Car("Audi", 2019);
# '''

# prog = '''
# const myPromise = new Promise(function(myResolve, myReject) {
# // "Producing Code" (May take some time)

#   myResolve(); // when successful
#   myReject();  // when error
# });

# // "Consuming Code" (Must wait for a fulfilled Promise).
# myPromise.then(
#   function(value) { /* code if successful */ },
#   function(error) { /* code if some error */ }
# );'''

# prog = """function myFunction(x, y = 10) {
#   // y is 10 if not passed or undefined
#   return x + y;
# }
# myFunction(5); // will return 15"""

# prog = '''function sum(...args) {
#   let sum = 0;
#   for (let arg of args) sum += arg;
#   return sum;
# }

# let x = sum(4, 9, 16, 25, 29, 100, 66, 77);'''

# Fix....  
# prog = '''var customer = { name: "Foo" }
# var card = { amount: 7, product: "Bar", unitprice: 42 }
# var message = `Hello ${customer.name}, want to buy ${card.amount} ${card.product} for a total of ${card.amount * card.unitprice} bucks?`'''

# prog = '''let target = {
#     foo: "Welcome, foo"
# }
# let proxy = new Proxy(target, {
#     get (receiver, name) {
#         return name in receiver ? receiver[name] : `Hello, ${name}`
#     }
# })
# proxy.foo === "Welcome, foo"
# proxy.world === "Hello, world"'''

# prog = '''
# let Obj = {
#     * foo () {}
# }
# class Clz {
#     * bar () {}
# }
# '''

# prog = '''
# function* range (start, end, step) {
#     while (start < end) {
#         yield start
#         start += step
#     }
# }

# for (let i of range(0, 10, 2)) {
#     console.log(i) // 0, 2, 4, 6, 8
# }'''

# prog = '''
# class Rectangle extends Shape {
#     static defaultRectangle () {
#         return new Rectangle("default", 0, 0, 100, 100)
#     }
# }
# class Circle extends Shape {
#     static defaultCircle () {
#         return new Circle("default", 0, 0, 100)
#     }
# }
# var defRectangle = Rectangle.defaultRectangle()
# var defCircle    = Circle.defaultCircle()
# '''

# prog = '''
# let obj = {
#     foo: "bar",
#     [ "baz" + quux() ]: 42
# }
# '''

# prog = '''
# var x = 0, y = 0
# obj = { x, y }
# '''

# prog = '''
# obj = {
#     foo (a, b) {
#     },
#     bar (x, y) {
#     },
#     *quux (x, y) {
#     }
# }
# '''

# prog = '''var list = [ 1, 2, 3 ];
# var [ a, , b ] = list;
# [ b, a ] = [ a, b ]'''

# prog = """var { op, lhs, rhs } = getASTNode()"""

# with open("react.py", 'w') as t:
#     with open('react.bundle.js') as f:
#         prog = f.read()
#     parsed = parse(prog, {"comment": True})
#     transformed = JsVisitor().visit(parsed)
#     t.write("\n".join(transformed).replace("\n\n", "\n"))

# prog ='''t.utils.warn = (function (global) {
#   return function (message) {
#     if (global.console && console.warn) {
#       console.warn(message)
#     }
#   }
# })(this)
# '''
# parsed = parse(prog, {"comment": True})
# transformed = JsVisitor().visit(parsed)
# print("\n".join(transformed))
