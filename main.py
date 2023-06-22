from esprima.visitor import NodeVisitor, Visited
from esprima import parse
from random import randint

class JsVisitor(NodeVisitor):
    indentLevel = 0
    in_class = False
    i = -1
    oldHeads = []
    heads = []
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
        name = self.visit(node.id) or "__anonymous_function__"
        head = f"{self.getIndent()}{'async ' if node.isAsync else ''}def {name}"
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
        if node.type == "SpreadElement":
            return self.visit_SpreadElement(self, node, isObject=True)

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

    # TODO refactor import and export
    def visit_ImportDeclaration(self, node):
        result = []
        assert node.source.type == "Literal"
        for specifier in node.specifiers:
            if specifier.type == "ImportDefaultSpecifier" or specifier.type == "ImportSpecifier":
                assert specifier.local.type == "Identifier"
                dst = specifier.local.name
                src = node.source.value
                if src.endswith(".js"):
                    src = src[:-3]
                src = src.replace("@", "__at__")
                src = src.replace("-", "_")
                if src.startswith("./"):
                    src = "." + src[2:]
                src = src.replace("/", ".")
                if specifier.type == "ImportDefaultSpecifier":
                    src += ".__default__"
                elif specifier.type == "ImportSpecifier":
                    assert specifier.imported.type == "Identifier"
                    src += "." + specifier.imported.name
                if src == dst:
                    result += [f"import {dst}"]
                elif src == f".{dst}":
                    result += [f"from . import {dst}"]
                else:
                    result += [f"import {src} as {dst}"]
                #result += f"
            else:
                return f"# FIXME: ImportDeclaration: node = " + str(node).replace("\n", "\n# ")
                # import { encode } from '@jridgewell/sourcemap-codec';
                #raise NotImplementedError("# FIXME:\n" + str(node))
            #s = ", ".join(node.specifiers)
            #return f"from {node.source.value} import {}"
        #print(node, file=sys.stderr)
        return "\n".join(result)

    # TODO refactor import and export
    def visit_ExportDefaultDeclaration(self, node):
        #return f"# FIXME: ExportDefaultDeclaration: node = " + str(node).replace("\n", "\n# ")
        # export default SomeIdentifier;
        body = ""
        # export default function someFunction() {};
        # TODO anonymous declarations:
        # export default function () {};
        # export default class SomeClass {};
        if node.declaration.type != "Identifier":
            body = self.visit(node.declaration) + "\n"
        src = ""
        if node.declaration.type == "FunctionDeclaration":
            src = self.visit(node.declaration.id) or "__anonymous_function__"
        elif node.declaration.type == "ClassDeclaration": # TODO verify
            assert node.declaration.id.type == "Identifier"
            src = node.declaration.id.name
        else:
            return f"# FIXME: ExportDefaultDeclaration: node = " + str(node).replace("\n", "\n# ")
        foot = f"__default__ = {src}"
        return body + foot

    # TODO refactor import and export
    def visit_ExportNamedDeclaration(self, node):
        if node.source:
            # js: export { default as Bundle } from './Bundle.js';
            # py: import .Bundle.__default__ as Bundle
            # py: from . import Bundle.__default__ as Bundle
            result = []
            for specifier in node.specifiers:
                assert specifier.type == "ExportSpecifier"
                assert specifier.local.type == "Identifier"
                assert specifier.exported.type == "Identifier"
                src = node.source.value
                if src.endswith(".js"):
                    src = src[:-3]
                # FIXME from . import foo
                # FIXME from .bar import foo
                if src.startswith("./"):
                    src = "." + src[2:]
                src = src.replace("/", ".")
                if specifier.local.name == "default":
                    src += ".__default__"
                else:
                    src += "." + specifier.local.name
                dst = specifier.exported.name
                result += [f"import {src} as {dst}"]
            return "\n".join(result)
        else:
            # no source
            # js: export { a as b };
            result = []
            for specifier in node.specifiers:
                assert specifier.type == "ExportSpecifier"
                assert specifier.local.type == "Identifier"
                assert specifier.exported.type == "Identifier"
                src = specifier.local.name
                dst = specifier.exported.name
                result += [f"{dst} = {src}"]
            return "\n".join(result)

        return f"# FIXME: ExportNamedDeclaration: node = " + str(node).replace("\n", "\n# ")

        #print(node, file=sys.stderr)
        return f"# FIXME ExportNamedDeclaration {node}"
        raise NotImplementedError
        head = f"# FIXME ExportDefaultDeclaration\n"
        body = self.visit(node.declaration)
        return head + body


if __name__ == "__main__":
    import sys
    with open(sys.argv[1]) as f:
        prog = f.read()
        parsed = parse(prog, {"comment": True, "tolerant": True})
        transformed = JsVisitor().visit(parsed)
        print("\n".join(transformed))
