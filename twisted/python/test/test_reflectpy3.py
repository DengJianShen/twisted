# Copyright (c) Twisted Matrix Laboratories.
# See LICENSE for details.

"""
Tests for the parts of L{twisted.python.reflect} which have been ported to
Python 3.
"""

from __future__ import division, absolute_import

import os

# Switch to SynchronousTestCase as part of #5885:
from unittest import TestCase

from twisted.python._reflectpy3 import accumulateMethods, prefixedMethods
from twisted.python import _reflectpy3 as reflect
# After twisted.python.reflect is fully ported to Python 3, import
# fullyQualifiedName from there instead, to test the actual public interface
# instead of this implementation detail.  See #5929.
from twisted.python._deprecatepy3 import (
    _fullyQualifiedName as fullyQualifiedName)


class Base(object):
    """
    A no-op class which can be used to verify the behavior of method-discovering
    APIs.
    """
    def method(self):
        """
        A no-op method which can be discovered.
        """



class Sub(Base):
    """
    A subclass of a class with a method which can be discovered.
    """



class Separate(object):
    """
    A no-op class with methods with differing prefixes.
    """
    def good_method(self):
        """
        A no-op method which a matching prefix to be discovered.
        """


    def bad_method(self):
        """
        A no-op method with a mismatched prefix to not be discovered.
        """



class AccumulateMethodsTests(TestCase):
    """
    Tests for L{accumulateMethods} which finds methods on a class hierarchy and
    adds them to a dictionary.
    """
    def test_ownClass(self):
        """
        If x is and instance of Base} and Base defines a method named method,
        L{accumulateMethods} adds an item to the given dictionary with
        C{"method"} as the key and a bound method object for Base.method value.
        """
        x = Base()
        output = {}
        accumulateMethods(x, output)
        self.assertEqual({"method": x.method}, output)


    def test_baseClass(self):
        """
        If x is an instance of Sub and Sub is a subclass of Base and Base
        defines a method named method, L{accumulateMethods} adds an item to the
        given dictionary with C{"method"} as the key and a bound method object
        for Base.method as the value.
        """
        x = Sub()
        output = {}
        accumulateMethods(x, output)
        self.assertEqual({"method": x.method}, output)


    def test_prefix(self):
        """
        If a prefix is given, L{accumulateMethods} limits its results to methods
        beginning with that prefix.  Keys in the resulting dictionary also have
        the prefix removed from them.
        """
        x = Separate()
        output = {}
        accumulateMethods(x, output, 'good_')
        self.assertEqual({'method': x.good_method}, output)



class PrefixedMethodsTests(TestCase):
    """
    Tests for L{prefixedMethods} which finds methods on a class hierarchy and
    adds them to a dictionary.
    """
    def test_onlyObject(self):
        """
        L{prefixedMethods} returns a list of the methods discovered on an
        object.
        """
        x = Base()
        output = prefixedMethods(x)
        self.assertEqual([x.method], output)


    def test_prefix(self):
        """
        If a prefix is given, L{prefixedMethods} returns only methods named with
        that prefix.
        """
        x = Separate()
        output = prefixedMethods(x, 'good_')
        self.assertEqual([x.good_method], output)



class Summer(object):
    """
    A class we look up as part of the LookupsTestCase.
    """
    def reallySet(self):
        """
        Do something.
        """



class LookupsTestCase(TestCase):
    """
    Tests for L{namedClass}, L{namedModule}, and L{namedAny}.
    """

    # Remove as part of  #5885:
    def assertIdentical(self, a, b):
        """
        Assert that the two given parameters are the same object.
        """
        self.assertTrue(a is b)


    # Remove as part of  #5885:
    def assertRaises(self, exception, f, *args, **kwargs):
        """
        Fail the test unless calling the function C{f} with the given
        C{args} and C{kwargs} raises C{exception}. The failure will report
        the traceback and call stack of the unexpected exception.

        @param exception: exception type that is to be expected
        @param f: the function to call

        @return: The raised exception instance, if it is of the given type.
        @raise self.failureException: Raised if the function call does
            not raise an exception or if it raises an exception of a
            different type.
        """
        import sys
        try:
            result = f(*args, **kwargs)
        except exception as inst:
            return inst
        except:
            raise self.failureException('%s raised instead of %s'
                                        % (sys.exc_info()[0],
                                           exception.__name__))
        else:
            raise self.failureException('%s not raised (%r returned)'
                                        % (exception.__name__, result))


    def test_namedClassLookup(self):
        """
        L{namedClass} should return the class object for the name it is passed.
        """
        self.assertIdentical(
            reflect.namedClass("twisted.python.test.test_reflectpy3.Summer"),
            Summer)


    def test_namedModuleLookup(self):
        """
        L{namedModule} should return the module object for the name it is
        passed.
        """
        from twisted.python import monkey
        self.assertIdentical(
            reflect.namedModule("twisted.python.monkey"), monkey)


    def test_namedAnyPackageLookup(self):
        """
        L{namedAny} should return the package object for the name it is passed.
        """
        import twisted.python
        self.assertIdentical(
            reflect.namedAny("twisted.python"), twisted.python)

    def test_namedAnyModuleLookup(self):
        """
        L{namedAny} should return the module object for the name it is passed.
        """
        from twisted.python import monkey
        self.assertIdentical(
            reflect.namedAny("twisted.python.monkey"), monkey)


    def test_namedAnyClassLookup(self):
        """
        L{namedAny} should return the class object for the name it is passed.
        """
        self.assertIdentical(
            reflect.namedAny("twisted.python.test.test_reflectpy3.Summer"), Summer)


    def test_namedAnyAttributeLookup(self):
        """
        L{namedAny} should return the object an attribute of a non-module,
        non-package object is bound to for the name it is passed.
        """
        # Note - not assertEqual because unbound method lookup creates a new
        # object every time.  This is a foolishness of Python's object
        # implementation, not a bug in Twisted.
        self.assertEqual(
            reflect.namedAny("twisted.python.test.test_reflectpy3.Summer.reallySet"),
            Summer.reallySet)


    def test_namedAnySecondAttributeLookup(self):
        """
        L{namedAny} should return the object an attribute of an object which
        itself was an attribute of a non-module, non-package object is bound to
        for the name it is passed.
        """
        self.assertIdentical(
            reflect.namedAny(
                "twisted.python.test.test_reflectpy3.Summer.reallySet.__doc__"),
            Summer.reallySet.__doc__)


    def test_importExceptions(self):
        """
        Exceptions raised by modules which L{namedAny} causes to be imported
        should pass through L{namedAny} to the caller.
        """
        self.assertRaises(
            ZeroDivisionError,
            reflect.namedAny, "twisted.test.reflect_helper_ZDE")
        # Make sure that this behavior is *consistent* for 2.3, where there is
        # no post-failed-import cleanup
        self.assertRaises(
            ZeroDivisionError,
            reflect.namedAny, "twisted.test.reflect_helper_ZDE")
        self.assertRaises(
            ValueError,
            reflect.namedAny, "twisted.test.reflect_helper_VE")
        # Modules which themselves raise ImportError when imported should result in an ImportError
        self.assertRaises(
            ImportError,
            reflect.namedAny, "twisted.test.reflect_helper_IE")


    def test_attributeExceptions(self):
        """
        If segments on the end of a fully-qualified Python name represents
        attributes which aren't actually present on the object represented by
        the earlier segments, L{namedAny} should raise an L{AttributeError}.
        """
        self.assertRaises(
            AttributeError,
            reflect.namedAny, "twisted.nosuchmoduleintheworld")
        # ImportError behaves somewhat differently between "import
        # extant.nonextant" and "import extant.nonextant.nonextant", so test
        # the latter as well.
        self.assertRaises(
            AttributeError,
            reflect.namedAny, "twisted.nosuch.modulein.theworld")
        self.assertRaises(
            AttributeError,
            reflect.namedAny,
            "twisted.python.test.test_reflectpy3.Summer.nosuchattribute")


    def test_invalidNames(self):
        """
        Passing a name which isn't a fully-qualified Python name to L{namedAny}
        should result in one of the following exceptions:
        - L{InvalidName}: the name is not a dot-separated list of Python objects
        - L{ObjectNotFound}: the object doesn't exist
        - L{ModuleNotFound}: the object doesn't exist and there is only one
          component in the name
        """
        err = self.assertRaises(reflect.ModuleNotFound, reflect.namedAny,
                                'nosuchmoduleintheworld')
        self.assertEqual(str(err), "No module named 'nosuchmoduleintheworld'")

        # This is a dot-separated list, but it isn't valid!
        err = self.assertRaises(reflect.ObjectNotFound, reflect.namedAny,
                                "@#$@(#.!@(#!@#")
        self.assertEqual(str(err), "'@#$@(#.!@(#!@#' does not name an object")

        err = self.assertRaises(reflect.ObjectNotFound, reflect.namedAny,
                                "tcelfer.nohtyp.detsiwt")
        self.assertEqual(
            str(err),
            "'tcelfer.nohtyp.detsiwt' does not name an object")

        err = self.assertRaises(reflect.InvalidName, reflect.namedAny, '')
        self.assertEqual(str(err), 'Empty module name')

        for invalidName in ['.twisted', 'twisted.', 'twisted..python']:
            err = self.assertRaises(
                reflect.InvalidName, reflect.namedAny, invalidName)
            self.assertEqual(
                str(err),
                "name must be a string giving a '.'-separated list of Python "
                "identifiers, not %r" % (invalidName,))



class FilenameToModule(TestCase):
    """
    Test L{filenameToModuleName} detection.
    """

    # Switch to using self.mktemp() as part of #5885, if we can figure out
    # bytes vs. unicode:
    def setUp(self):
        import tempfile
        self.path = os.path.join(tempfile.mktemp(), "fakepackage", "test")
        os.makedirs(self.path)
        with open(os.path.join(self.path, "__init__.py"), "w") as f:
            f.write("")
        with open(os.path.join(os.path.dirname(self.path), "__init__.py"),
                  "w") as f:
            f.write("")


    def test_directory(self):
        """
        L{filenameToModuleName} returns the correct module (a package) given a
        directory.
        """
        module = reflect.filenameToModuleName(self.path)
        self.assertEqual(module, 'fakepackage.test')
        module = reflect.filenameToModuleName(self.path + os.path.sep)
        self.assertEqual(module, 'fakepackage.test')


    def test_file(self):
        """
        L{filenameToModuleName} returns the correct module given the path to
        its file.
        """
        module = reflect.filenameToModuleName(
            os.path.join(self.path, 'test_reflect.py'))
        self.assertEqual(module, 'fakepackage.test.test_reflect')


    def test_bytes(self):
        """
        L{filenameToModuleName} returns the correct module given a C{bytes}
        path to its file.
        """
        module = reflect.filenameToModuleName(
            os.path.join(self.path.encode("utf-8"), b'test_reflect.py'))
        # Module names are always native string:
        self.assertEqual(module, 'fakepackage.test.test_reflect')



class FullyQualifiedNameTests(TestCase):
    """
    Test for L{fullyQualifiedName}.
    """

    def _checkFullyQualifiedName(self, obj, expected):
        """
        Helper to check that fully qualified name of C{obj} results to
        C{expected}.
        """
        self.assertEqual(fullyQualifiedName(obj), expected)


    def test_package(self):
        """
        L{fullyQualifiedName} returns the full name of a package and a
        subpackage.
        """
        import twisted
        self._checkFullyQualifiedName(twisted, 'twisted')
        import twisted.python
        self._checkFullyQualifiedName(twisted.python, 'twisted.python')


    def test_module(self):
        """
        L{fullyQualifiedName} returns the name of a module inside a a package.
        """
        import twisted.python.compat
        self._checkFullyQualifiedName(
            twisted.python.compat,'twisted.python.compat')


    def test_class(self):
        """
        L{fullyQualifiedName} returns the name of a class and its module.
        """
        self._checkFullyQualifiedName(
            FullyQualifiedNameTests, '%s.FullyQualifiedNameTests' % (__name__,))


    def test_function(self):
        """
        L{fullyQualifiedName} returns the name of a function inside its module.
        """
        self._checkFullyQualifiedName(
            fullyQualifiedName, "twisted.python.reflect.fullyQualifiedName")


    def test_boundMethod(self):
        """
        L{fullyQualifiedName} returns the name of a bound method inside its
        class and its module.
        """
        self._checkFullyQualifiedName(
            self.test_boundMethod,
            "%s.%s.test_boundMethod" % (__name__, self.__class__.__name__))


    def test_unboundMethod(self):
        """
        L{fullyQualifiedName} returns the name of an unbound method inside its
        class and its module.
        """
        self._checkFullyQualifiedName(
            self.__class__.test_unboundMethod,
            "%s.%s.test_unboundMethod" % (__name__, self.__class__.__name__))
