Mockable Doc Tests
==================
Doctests are extremely useful for showing how functions and modules in a
product are to be used as part of documentation.  They also encourage
maintainers keep the documentation up to date, since they'll be updating
the tests that are right next to it anyway.  There are two problems with
them that make unittest more practical.

------------------
Problem 1: Mocking
------------------
Unittest allows globals to be mocked out for the purpose of testing
functions that use them, but doctests do not allow for it.  This means
that if a function makes use of an imported module, the test must use it
as well.  This prevents any meaningful unit tests and prevents testing
from being done without all the product's requirements being available.

The only way to get around this is extensive modification of tested
functions, allowing for the test to pass in mocks to it.  This is a
truly terrible way to do things.  It makes the code more complex than it
needs to be, and the resulting tests aren't descriptive.

---------------------
Solution to Problem 1
---------------------
Using this package, mocks of variables and functions can be supplied,
based on package and function to use the mocks.  The mocks will be
applied to the global variables in both the test itself and the methods
indicated.

The following will mock the 'foo' variable in tests of the 'function'
function in the 'module' module in the tests it finds:
>>> foo_mock = {
...   "module": {
...     "function": {
...       "foo": 10}}}

The above example shows a simple variable being mocked, but it is also
possible to mock internal attributes of an object.  The following will
mock the 'attribute' attribute of the 'object' object with the function.
Any other attributes of the object will remain unchanged.
>>> object_attribute_mock = {
...   "module": {
...     "function": {
...       "object.attribute": 20}}}

Often, the thing that needs mocking is not a simple variable type,
though.  We can also mock out functions, and classes:
>>> from mockabledoctests import Mock.
>>> class MockClass(Mock):
...   pass
>>> def mock_function():
...   pass
>>> mock_class_and_function = {
...   "module": {
...     "function": {
...       "class": MockClass,
...       "f": mock_function}}}

Methods of all sorts are also mockable.  This works with both new- and
old-style classes.  Here is how the above would be put together to
create the DocTestParser that will do the mocking.
>>> from mockabledoctests import MockableDocTestParser
>>> mdtp = MockableDocTestParser(
...   mocks={
...     "module": {
...       "function": {
...         "foo": 10,
...         "object.attribute": 20,
...         "class": MockClass,
...         "f": mock_function}}}

It can be used in the load_tests function, so that unittest will find it
in its discovery:
>>> def load_tests(loader, tests, ignore):
...   dtf = doctest.DocTestFinder(parser=mdtp)
...   for name in mdtp.mocks:
...     for test in dtf.find(sys.modules[name]):
...       dtc = doctest.DocTestCase(test)
...       tests.addTest(dtc)
...   return tests

--------------------------------------
Problem 2: Only one test per docstring
--------------------------------------
Doctest are intended to cover the intended use of a function, class,
or module, and assumes that that can be handled with only one test.
This leads to long, circuitous tests, and failures can be difficult to
find, since unittest treats them as happening at the start of the
docstring.

---------------------
Solution to Problem 2
---------------------
A solution to this problem will be supplied in a future PR.

----------------------
Implementation details
----------------------
The mocking in this product is caused my making copies of whatever is to
be mocked, altering the global namespaces they are using, and injecting
them into the test's namespace in place of the original.  Since doctest
creates a separate namespace for each test, there's no worries about
copies made for one test bleeding over into another.  This injection is
done by a subclass of doctest.DocTestParser which is then passed to a
doctest.DocTestFinder as part of the load_test function of the module
that unittest is searching for tests.  unittest will run our stuff,
which will add all the mocked doctests into the list of tests that
unittest has already found.

More information about unittest's load_tests protocol can be found at
https://docs.python.org/2/library/unittest.html#load-tests-protocol.
More information on how to make unittest discover doctests can be found
at https://docs.python.org/2/library/doctest.html and in the doctest
source.
