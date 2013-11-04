#! /usr/bin/env python

"""
Generate some internal code.
"""

from __future__ import absolute_import
from collections import defaultdict
from os.path import splitext

from pykit.ir import ops, defs

def getorder():
    pos = defaultdict(int) # { 'opname': index }
    fn, ext = splitext(ops.__file__)
    lines = list(open(fn + '.py'))
    for name, op in vars(ops).iteritems():
        if isinstance(op, basestring) and name not in ('__file__', '__name__',
                                                       'constant'):
            for i, line in enumerate(lines):
                if line.startswith(op):
                    pos[op] = i
                    break

    order = sorted((lineno, op) for op, lineno in pos.iteritems())
    return order

order = getorder()

def gen_builder():
    """Generate code for pykit.ir.builder operations"""
    print("    # Generated by pykit.utils._generate")
    for lineno, op in order:
        if op[0].isupper():
            print("    %-20s = _const(ops.%s)" % (op, op))
        else:
            print("    %-20s = _op(ops.%s)" % (op, op))

def gen_builder_methods():
    """Generate code for pykit.ir.builder operations"""
    print("""
    #===------------------------------------------------------------------===
    # Generated by pykit.utils._generate
    #===------------------------------------------------------------------===
    """)

    names = {
        ops.List: 'lst',
        ops.Value: 'value',
        ops.Const: 'const',
        ops.Any: 'any',
        ops.Obj: 'obj'
    }

    for lineno, op in order:
        if op[0].isupper():
            print("    %-20s = _const(ops.%s)" % (op, op))
        else:
            counts = defaultdict(int)
            params = []
            args = []
            stmts = []

            if not ops.is_void(op):
                params.append("type")
                type = "type"
            else:
                type = "types.Void"

            for s in ops.op_syntax[op]:
                if s == ops.Star:
                    params.append('*args')
                    args.append('list(args)')
                else:
                    param = "%s%d" % (names[s], counts[s])
                    params.append(param)
                    args.append(param)

                    if s == ops.List:
                        ty = "list"
                    elif s == ops.Value:
                        ty = "Value"
                    elif s == ops.Const:
                        ty = "Const"
                    else:
                        continue

                    stmts.append("assert isinstance(%s, %s)" % (param, ty))

                counts[s] += 1

            params = ", ".join(params) + "," if params else ""
            args = ", ".join(args)
            if type:
                stmts.append('assert type is not None')
            else:
                stmts.append('type = types.Void')

            d = {
                'op': op, 'params': params, 'args': args, 'type': type,
                'stmts': '\n        '.join(stmts),
            }

            print("""
    def %(op)s(self, %(params)s **kwds):
        %(stmts)s
        register = kwds.pop('result', None)
        op = Op('%(op)s', %(type)s, [%(args)s], register, metadata=kwds)
        if config.op_verify:
            verify_op_syntax(op)
        self._insert_op(op)
        return op""" % d)

def gen_visitor():
    """Generate code for any visitor"""
    for lineno, op in order:
        if not op[0].isupper():
            print("    def %s(self, op):\n        pass\n" % (op,))

def gen_ops(lst):
    """Generate ops for ops.py"""
    for name in lst:
        print("%-18s = %r" % (name, name))

def gen_ops2():
    for op in defs.unary:
        print("    %-20s = unary(%r)" % (op, op))
    for op in defs.binary:
        print("    %-20s = binop(%r)" % (op, op))
    for op in defs.compare:
        print("    %-20s = binop(%-10s, type=types.Bool)" % (op, repr(op)))



if __name__ == "__main__":
    #gen_ops2()
    gen_builder_methods()

