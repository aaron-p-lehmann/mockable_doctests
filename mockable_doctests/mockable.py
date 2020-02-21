"""
This provides MockableDocTestParser, a DocTestParser that allows
doctests to be mocked as a part of a unittest suite.
"""
import copy
import doctest
import functools
import types


class Mock(object):
    """
    Dummy class to mark mocked objects, so that other injections know
    they don't need to make a mock.  It also has an __init__ method,
    because we need to make sure there's one in the __dict__ for when we
    copy classes.
    """
    def __init__(self):
        super(Mock, self).__init__()


class MockCallable(Mock):
    """
    Dummy class to mark mocked callables so that other injects know they
    don't need to make a mock.
    >>> def f():
    ...   return 5
    >>> mc = MockCallable(f)
    >>> f is mc.cal
    True
    >>> mc()
    5
    """
    def __init__(self, cal):
        super(MockCallable, self).__init__()
        self.cal = cal

    def __call__(self, *args, **kwargs):
        return self.cal(*args, **kwargs)


def copy_callable(name, original, new_globals=None, clas=None):
    """
    Copies globals into a copy of the provided non-class callable
    >>> def f():
    ...   pass
    >>> lamb = lambda: None
    >>> class A(object):
    ...   def print_foo(self):
    ...     pass
    ...   @classmethod
    ...   def print_bar(self):
    ...     pass
    ...   @staticmethod
    ...   def print_baz(self):
    ...     pass
    ...   @property
    ...   def qux(self):
    ...     pass
    ...   @qux.setter
    ...   def qux(self, val):
    ...     pass
    ...   @qux.deleter
    ...   def qux(self):
    ...     pass
    >>> meth = copy_callable("print_foo", A.print_foo, new_globals, A)
    Copying <type 'instancemethod'>: print_foo
    >>> classmeth = copy_callable("print_bar", A.print_bar, new_globals, A)
    Copying classmethod: print_bar
    >>> staticmeth = copy_callable("print_baz", A.print_baz, new_globals, A)
    Copying staticmethod: print_baz
    >>> func = copy_callable("f", f, new_globals, A)
    Copying <type 'function'>: f
    >>> func = copy_callable("lamb", lamb, new_globals, A)
    Copying <type 'function'>: <lambda>
    """
    if isinstance(original, types.MethodType):
        if original.im_self:
            return copy_classmethod(original, new_globals)
        else:
            return copy_method(original, clas, new_globals)
    elif isinstance(original, types.FunctionType):
        if clas and isinstance(getattr(clas, name, None), types.FunctionType):
            # This is a staticmethod, because if it weren't, this would
            # be a bound or unbound method
            return copy_staticmethod(original, new_globals)
        else:
            # Just a regular function
            return copy_function(original, new_globals)
    else:
        return original


def copy_class(clas, new_globals):
    """
    Makes a copy of a class, all its attributes, and all its methods.
    All the methods will have the new globals included.
    >>> class NewStyle(object):
    ...     "A new style class"
    >>> class OldStyle:
    ...     "An old style class"
    >>> A = copy_class(NewStyle, new_globals)
    Copying <type 'dictproxy'>: __dict__
    Copying <type 'str'>: __doc__
    Copying <type 'str'>: __module__
    Copying <type 'getset_descriptor'>: __weakref__
    >>> A = copy_class(OldStyle, new_globals)
    Copying <type 'str'>: __doc__
    Copying <type 'str'>: __module__
    """
    copy_clas = clas
    if not issubclass(copy_clas, Mock):
        copy_dict = dict(clas.__dict__)
        copy_clas = type(clas.__name__, (Mock,) + clas.__bases__, copy_dict)
        new_globals[clas.__name__] = copy_clas

        for name in sorted(copy_clas.__dict__):
            try:
                copy_val = copy_value(name, getattr(copy_clas, name), new_globals, copy_clas)
                setattr(copy_clas, name, copy_val)
            except (AttributeError, KeyError, TypeError):
                pass
    return copy_clas


def copy_classmethod(original, new_globals):
    """
    Copies the function part of a classmethod, then makes a new
    classmethod out of it.
    >>> class Class(object):
    ...   @classmethod
    ...   def cmethod(cls):
    ...     pass
    >>> newcmethod = copy_classmethod(Class.cmethod, {})
    >>> newcmethod #doctest: +ELLIPSIS
    <classmethod object at 0x...>
    >>> newcmethod is not Class.cmethod
    True
    >>> newcmethod.__func__.func_code is Class.cmethod.__func__.func_code
    True
    """
    return classmethod(copy_function(original.__func__, new_globals))


def copy_function(f, new_globals=None):
    """
    Makes a copy of a function
    Based on http://stackoverflow.com/a/6528148/190597 (Glenn Maynard)
    >>> baz = 10
    >>> def f():
    ...   print baz
    >>> g = copy_function(f)
    >>> f()
    10
    >>> g()
    10
    >>> g is not f
    True

    Optionally, a dict can be passed in, and the new globals dict will
    be update()'d with it.
    >>> h = copy_function(f, new_globals)
    >>> h()
    7
    """
    globs = {}
    globs.update(f.func_globals)
    globs.update(new_globals or {})
    g = types.FunctionType(f.func_code, globs, name=f.func_name,
                           argdefs=f.func_defaults,
                           closure=f.func_closure)
    g.func_globals[g.func_name] = g
    g = functools.update_wrapper(g, f)
    return g


def copy_method(meth, clas, new_globals):
    """
    Copies a method by copying the underlying function and making a new
    method out of it.
    >>> class NewStyle(object):
    ...   def f(self):
    ...     pass
    >>> new_f = copy_method(NewStyle.f, NewStyle, new_globals)
    Copying f
    >>> NewStyle.f is not new_f
    True
    >>> NewStyle.f.im_func.func_code is new_f.im_func.func_code
    True
    """
    return types.MethodType(copy_function(meth.im_func, new_globals), None, clas)


def copy_miscellanious(misc):
    """
    Returns a deepcopy of an object
    """
    return copy.deepcopy(misc)


def copy_name(thing, new_globals):
    """
    Makes a copy of a class, a function, a method, or a property
    >>> new = copy_name('NewStyle.number', new_globals)
    Copying value: NewStyle
    Copying value: NewStyle.number
    >>> new = copy_name('NewStyle.array', new_globals)
    Copying value: NewStyle
    Copying value: NewStyle.array
    >>> old = copy_name('OldStyle.module', new_globals)
    Copying value: OldStyle
    Copying value: OldStyle.module
    """
    copy_object = current_object = None
    part_names = thing.split(".")
    part_names_paths = [(part_names[i], ".".join(part_names[:i + 1])) for i in range(len(part_names))]
    while part_names_paths:
        part_name, part_path = part_names_paths.pop(0)
        next_object = new_globals.get(part_path, getattr(current_object, part_name, Mock()))
        if isinstance(next_object, (types.ClassType, type)):
            next_object_class = next_object
        else:
            next_object_class = type(next_object)
        next_object = copy_value(
            part_path,
            next_object,
            new_globals,
            next_object_class)
        if copy_object is None:
            copy_object = current_object = next_object
        else:
            setattr(current_object, part_name, next_object)
            current_object = next_object
    return copy_object


def copy_property(prop, new_globals):
    """
    Copies a property
    >>> prop_doc = "A property"
    >>> prop = property(
    ...   fget=lambda x: None,
    ...   fset=lambda x, y: None,
    ...   fdel=lambda x: None,
    ...   doc=prop_doc)
    >>> copied_prop = copy_property(prop, new_globals)
    Copying function
    Copying function
    Copying function
    >>> copied_prop is not prop
    True
    """
    return property(
        fget=copy_function(prop.fget, new_globals) if prop.fget else None,
        fset=copy_function(prop.fset, new_globals) if prop.fset else None,
        fdel=copy_function(prop.fdel, new_globals) if prop.fdel else None,
        doc=prop.__doc__)


def copy_staticmethod(original, new_globals):
    """
    Copies the function part of a staticmethod, then makes a new
    staticmethod out of it.
    >>> class Class(object):
    ...   @staticmethod
    ...   def smethod(cls):
    ...     pass
    >>> newsmethod = copy_staticmethod(Class.smethod, {})
    >>> newsmethod #doctest: +ELLIPSIS
    <staticmethod object at 0x...>
    >>> newsmethod is not Class.smethod
    True
    >>> newsmethod.__func__.func_code is Class.smethod.func_code
    True
    """
    return staticmethod(copy_function(original, new_globals))


def copy_value(name, original, new_globals=None, clas=None):
    """
    Makes a copy of a class, a function, a method, or a property
    >>> foo = new_globals['foo'] = range(5)
    >>> def f():
    ...   pass
    >>> lamb = lambda: None
    >>> class A(object):
    ...   def print_foo(self):
    ...     pass
    ...   @classmethod
    ...   def print_bar(self):
    ...     pass
    ...   @staticmethod
    ...   def print_baz(self):
    ...     pass
    ...   @property
    ...   def qux(self):
    ...     pass
    ...   @qux.setter
    ...   def qux(self, val):
    ...     pass
    ...   @qux.deleter
    ...   def qux(self):
    ...     pass

    Methods (instance, class, or static), functions, and lambdas are all
    handled by the callable copying code
    >>> meth = copy_value("print_foo", A.print_foo, new_globals, A)
    Copying callable: print_foo
    >>> classmeth = copy_value("print_bar", A.print_bar, new_globals, A)
    Copying callable: print_bar
    >>> staticmeth = copy_value("print_baz", A.print_baz, new_globals, A)
    Copying callable: print_baz
    >>> func = copy_value("f", f, new_globals, A)
    Copying callable: f
    >>> func = copy_value("lamb", lamb, new_globals, A)
    Copying callable: <lambda>

    Properties are handled by property copying code
    >>> prop = copy_value("qux", A.qux, new_globals, A)
    Copying property

    Classes are handled by class copying code
    >>> C = copy_value("A", A, new_globals, A)
    Copying class: A

    Other things are handled by the miscellanious code
    >>> misc = copy_value("foo", foo, new_globals, A)
    Copying miscellanious: [0, 1, 2, 3, 4]

    If a Mock object is passed, it is returned unchanged.
    >>> copy_value("print_foo", mock, new_globals, A) is mock
    True
    """
    if issubclass(original, Mock) if isinstance(original, type) else isinstance(original, Mock):
        return original
    elif isinstance(original, (types.ClassType, type)):
        return copy_class(original, new_globals)
    elif isinstance(original, (types.FunctionType, types.MethodType)):
        return copy_callable(name, original, new_globals, clas)
    elif isinstance(original, property):
        return copy_property(original, new_globals)
    else:
        return copy_miscellanious(new_globals[name])


class MockableDocTestParser(doctest.DocTestParser):
    """
    This is a DocTestParser that allows doctests to have variables
    mocked.

    Create an instance of this class with a dict of doctests to mock to
    values to mock in them.  Then pass it to a doctest.DocTestFinder,
    and follow the instructions in the doctest documentation.  There's a
    handie example of use in this module, as well :)
    """
    def __init__(self, mocks=None):
        self.mocks = mocks or {}

    def flatten_mocks(self):
        """
        This will flatten the structure of the mocks for the parser to
        a dict that is full name of the mock, versions a nested dict
        with the packaging on the outside and the local name on the
        inside.
        """
        flat_mocks = {}
        for mock_module, mocks in self.mocks.items():
            for mock_name, mock in mocks.items():
                flat_name = "{module}.{name}".format(
                    module=mock_module,
                    name=mock_name)
                flat_mocks[flat_name] = mock
        return flat_mocks

    def apply_mocks(self, name, globs):
        """
        This takes a dictionary of globals and applies the mocks to them.
        It then applies the mocks to the global namespace of the thing
        under test, if it is a function-type object.
        >>> globs = {'fred': 5, 'barney': 10}
        >>> mdtp = MockableDocTestParser(
        ...   mocks={
        ...     "flintstone": {
        ...       "fred": {"fred": 10}}})
        >>> new_globals = mdtp.apply_mocks(name="flintstone.fred", globs=globs)
        >>> print sorted(new_globals.items()) # doctest: +ELLIPSIS
        [('barney', 10), ('fred', 10)]
        """
        mocks = self.flatten_mocks()
        if name in mocks:
            new_globals = {}
            new_globals.update(globs)
            new_globals.update(mocks[name])

            # mock the globals of the callable we're testing
            for mock_name in sorted(mocks[name]):
                new_globals[mock_name.split(".")[0]] = copy_name(mock_name, new_globals)

            # mock the callable itself
            for real_name in new_globals:
                if name.endswith(real_name):
                    new_globals[real_name] = copy_callable(
                        real_name,
                        new_globals[real_name],
                        new_globals,
                        clas=type(new_globals[real_name]))
            globs = new_globals
        return globs

    def get_doctest(self, string, globs, name, filename, lineno):
        """
        Returns the DocTest for the string after applying the mocks that
        were provided in __init__.
        """
        # This applies the mocks to the globals directory that will
        # be used by the functions called from the test.
        applied = self.apply_mocks(name, globs)
        dt = doctest.DocTestParser.get_doctest(
            self,
            string=string,
            globs=applied,
            name=name,
            filename=filename,
            lineno=lineno)

        # This applies the mocks to the test itself.
        dt.globs = self.apply_mocks(name, dt.globs)
        return dt
