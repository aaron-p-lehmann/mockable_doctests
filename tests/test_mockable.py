import doctest
import sys

from mockabledoctests import Mock, MockableDocTestParser, mockable


def printer(string, retval=None):
    """
    Prints a string, then returns the passed return value
    >>> printer("Fred", 5)
    Fred
    5
    """
    print string
    return retval


class empty_test_class(object):
    """
    An empty class for use with testing class mocking
    """
    pass


# These global values exist to be mocked out in the test_class class,
# below.
foo = 10
bar = 20
baz = 30
qux = 40
quxx = 50


class test_class(object):
    """
    This is a class for testing that the MockableDocTestParser works on
    classes.

    The global values of foo, bar, baz, qux, and quxx have been mocked
    out, as have the values of the class variables r and b.  That is why
    they are all different in the test results from what you would
    ordinarlily expect.
    >>> print test_class.r
    [0, 2, 4, 6, 8]
    >>> print test_class.b.__name__
    mocked_empty_class
    >>> test_class.print_bar()
    17
    >>> test_class.print_baz()
    27
    >>> c = test_class()
    >>> print c.test_var
    7
    >>> c.print_foo()
    7
    >>> print c.quxer
    37
    >>> c.quxer = 5
    >>> print c.quxer
    52
    """
    r = range(5)
    b = empty_test_class

    def __init__(self):
        super(test_class, self).__init__()
        self.test_var = foo

    def print_foo(self):
        print foo

    @classmethod
    def print_bar(cls):
        print bar

    @staticmethod
    def print_baz():
        print baz

    @property
    def quxer(self):
        if not hasattr(self, "_qux"):
            self._qux = qux
        return self._qux

    @quxer.setter
    def quxer(self, val):
        self._qux = quxx + val
        return self._qux


def load_tests(loader, tests, ignore):
    # Create mocks for copy_callable
    copy_callable_mocks = {
        'copy_function': lambda func, new_globals: printer("Copying %s: %s" % (type(func), func.__name__)),
        'copy_method': lambda m, clas, new_globals: printer("Copying %s: %s" % (type(m), m.__name__)),
        'copy_classmethod': lambda m, new_globals: printer("Copying classmethod: %s" % m.__name__),
        'copy_staticmethod': lambda m, new_globals: printer("Copying staticmethod: %s" % m.__name__)
    }
    copy_callable_mocks['new_globals'] = dict(copy_callable_mocks)

    # Create mocks for copy_class
    copy_class_mocks = {
        'copy_value': lambda name, value, new_globals, copy_class: printer("Copying %s: %s" % (type(value), name))}
    copy_class_mocks['new_globals'] = dict(copy_class_mocks)

    # Create mocks for copy_function
    copy_function_mocks = {'baz': 7}
    copy_function_mocks['new_globals'] = dict(copy_function_mocks)

    # Create mocks for copy_method
    copy_method_mocks = {
        'copy_function': lambda value, new_globals: printer("Copying %s" % value.__name__, value)}
    copy_method_mocks['new_globals'] = dict(copy_method_mocks)

    # Create mocks for copy_name
    class NewStyle(object):
        "A new style class" 
        number = 5
        array = range(5)
    class OldStyle:
        "An old style class"
        module = NewStyle
    copy_name_mocks = {
        'NewStyle': NewStyle,
        'OldStyle': OldStyle,
        'copy_value': lambda name, original, new_globals, clas: printer("Copying value: %s" % name, original)}
    copy_name_mocks['new_globals'] = dict(copy_name_mocks)

    # Create mocks for copy_property
    copy_property_mocks = {
        'copy_function': lambda *args, **kwargs: printer("Copying function"),
        'prop_doc': "A copied property"}
    copy_property_mocks['new_globals'] = dict(copy_property_mocks)

    # Create mocks for copy_value
    copy_value_mocks = {
        'copy_miscellanious': lambda original: printer("Copying miscellanious: %s" % original),
        'copy_callable': lambda name, original, new_globals, clas: printer("Copying callable: %s" % original.__name__),
        'copy_property': lambda prop, new_globals: printer("Copying property"),
        'copy_class': lambda clas, new_globals: printer("Copying class: %s" % clas.__name__),
        'mock': Mock()}
    copy_value_mocks['new_globals'] = dict(copy_value_mocks)

    # Create mocks for the test_class
    test_class_mocks = {
        'test_class.b': type("mocked_empty_class", (Mock,), {}),
        'test_class.r': range(0, 10, 2),
        'foo': 7,
        'bar': 17,
        'baz': 27,
        'qux': 37,
        'quxx': 47}
    test_class_mocks['new_globals'] = dict(test_class_mocks)

    # Find tests
    mdtp = MockableDocTestParser(
        mocks={
            __name__: {
                "test_class": test_class_mocks},
            "mockabledoctests.mockable": {
                'copy_callable': copy_callable_mocks,
                'copy_class': copy_class_mocks,
                'copy_function': copy_function_mocks,
                'copy_method': copy_method_mocks,
                'copy_name': copy_name_mocks,
                'copy_property': copy_property_mocks,
                'copy_value': copy_value_mocks}})
    dtf = doctest.DocTestFinder(parser=mdtp)
    for name in mdtp.mocks:
        for test in dtf.find(sys.modules[name]):
            dtc = doctest.DocTestCase(test)
            tests.addTest(dtc)
    return tests
