from js2py.base import *
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
from js2py.host.jsfunctions import parseFloat, parseInt, isFinite,     isNaN, escape, unescape, encodeURI, decodeURI, encodeURIComponent, decodeURIComponent


@Js
def x(this, arguments, x, y):

    return x * y


obj = {'foo': 'bar', 'baz' + quux(): 42}
