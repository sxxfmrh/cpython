# A test suite for pdb; not very comprehensive at the moment.

import imp
import pdb
import sys
import unittest
import subprocess

from test import support
# This little helper class is essential for testing pdb under doctest.
from test.test_doctest import _FakeInput


class PdbTestInput(object):
    """Context manager that makes testing Pdb in doctests easier."""

    def __init__(self, input):
        self.input = input

    def __enter__(self):
        self.real_stdin = sys.stdin
        sys.stdin = _FakeInput(self.input)

    def __exit__(self, *exc):
        sys.stdin = self.real_stdin


def test_pdb_displayhook():
    """This tests the custom displayhook for pdb.

    >>> def test_function(foo, bar):
    ...     import pdb; pdb.Pdb().set_trace()
    ...     pass

    >>> with PdbTestInput([
    ...     'foo',
    ...     'bar',
    ...     'for i in range(5): print(i)',
    ...     'continue',
    ... ]):
    ...     test_function(1, None)
    > <doctest test.test_pdb.test_pdb_displayhook[0]>(3)test_function()
    -> pass
    (Pdb) foo
    1
    (Pdb) bar
    (Pdb) for i in range(5): print(i)
    0
    1
    2
    3
    4
    (Pdb) continue
    """


def test_pdb_basic_commands():
    """Test the basic commands of pdb.

    >>> def test_function_2(foo, bar='default'):
    ...     print(foo)
    ...     for i in range(5):
    ...         print(i)
    ...     print(bar)
    ...     for i in range(10):
    ...         never_executed
    ...     print('after for')
    ...     print('...')
    ...     return foo.upper()

    >>> def test_function():
    ...     import pdb; pdb.Pdb().set_trace()
    ...     ret = test_function_2('baz')
    ...     print(ret)

    >>> with PdbTestInput([  # doctest: +ELLIPSIS, +NORMALIZE_WHITESPACE
    ...     'step',       # entering the function call
    ...     'args',       # display function args
    ...     'list',       # list function source
    ...     'bt',         # display backtrace
    ...     'up',         # step up to test_function()
    ...     'down',       # step down to test_function_2() again
    ...     'next',       # stepping to print(foo)
    ...     'next',       # stepping to the for loop
    ...     'step',       # stepping into the for loop
    ...     'until',      # continuing until out of the for loop
    ...     'next',       # executing the print(bar)
    ...     'jump 8',     # jump over second for loop
    ...     'return',     # return out of function
    ...     'retval',     # display return value
    ...     'continue',
    ... ]):
    ...    test_function()
    > <doctest test.test_pdb.test_pdb_basic_commands[1]>(3)test_function()
    -> ret = test_function_2('baz')
    (Pdb) step
    --Call--
    > <doctest test.test_pdb.test_pdb_basic_commands[0]>(1)test_function_2()
    -> def test_function_2(foo, bar='default'):
    (Pdb) args
    foo = 'baz'
    bar = 'default'
    (Pdb) list
      1  ->     def test_function_2(foo, bar='default'):
      2             print(foo)
      3             for i in range(5):
      4                 print(i)
      5             print(bar)
      6             for i in range(10):
      7                 never_executed
      8             print('after for')
      9             print('...')
     10             return foo.upper()
    [EOF]
    (Pdb) bt
    ...
      <doctest test.test_pdb.test_pdb_basic_commands[2]>(18)<module>()
    -> test_function()
      <doctest test.test_pdb.test_pdb_basic_commands[1]>(3)test_function()
    -> ret = test_function_2('baz')
    > <doctest test.test_pdb.test_pdb_basic_commands[0]>(1)test_function_2()
    -> def test_function_2(foo, bar='default'):
    (Pdb) up
    > <doctest test.test_pdb.test_pdb_basic_commands[1]>(3)test_function()
    -> ret = test_function_2('baz')
    (Pdb) down
    > <doctest test.test_pdb.test_pdb_basic_commands[0]>(1)test_function_2()
    -> def test_function_2(foo, bar='default'):
    (Pdb) next
    > <doctest test.test_pdb.test_pdb_basic_commands[0]>(2)test_function_2()
    -> print(foo)
    (Pdb) next
    baz
    > <doctest test.test_pdb.test_pdb_basic_commands[0]>(3)test_function_2()
    -> for i in range(5):
    (Pdb) step
    > <doctest test.test_pdb.test_pdb_basic_commands[0]>(4)test_function_2()
    -> print(i)
    (Pdb) until
    0
    1
    2
    3
    4
    > <doctest test.test_pdb.test_pdb_basic_commands[0]>(5)test_function_2()
    -> print(bar)
    (Pdb) next
    default
    > <doctest test.test_pdb.test_pdb_basic_commands[0]>(6)test_function_2()
    -> for i in range(10):
    (Pdb) jump 8
    > <doctest test.test_pdb.test_pdb_basic_commands[0]>(8)test_function_2()
    -> print('after for')
    (Pdb) return
    after for
    ...
    --Return--
    > <doctest test.test_pdb.test_pdb_basic_commands[0]>(10)test_function_2()->'BAZ'
    -> return foo.upper()
    (Pdb) retval
    'BAZ'
    (Pdb) continue
    BAZ
    """


def test_pdb_breakpoint_commands():
    """Test basic commands related to breakpoints.

    >>> def test_function():
    ...     import pdb; pdb.Pdb().set_trace()
    ...     print(1)
    ...     print(2)
    ...     print(3)
    ...     print(4)

    First, need to clear bdb state that might be left over from previous tests.
    Otherwise, the new breakpoints might get assigned different numbers.

    >>> from bdb import Breakpoint
    >>> Breakpoint.next = 1
    >>> Breakpoint.bplist = {}
    >>> Breakpoint.bpbynumber = [None]

    Now test the breakpoint commands.  NORMALIZE_WHITESPACE is needed because
    the breakpoint list outputs a tab for the "stop only" and "ignore next"
    lines, which we don't want to put in here.

    >>> with PdbTestInput([  # doctest: +NORMALIZE_WHITESPACE
    ...     'break 3',
    ...     'disable 1',
    ...     'ignore 1 10',
    ...     'condition 1 1 < 2',
    ...     'break 4',
    ...     'break',
    ...     'condition 1',
    ...     'enable 1',
    ...     'clear 1',
    ...     'commands 2',
    ...     'print 42',
    ...     'end',
    ...     'continue',  # will stop at breakpoint 2 (line 4)
    ...     'clear',     # clear all!
    ...     'y',
    ...     'tbreak 5',
    ...     'continue',  # will stop at temporary breakpoint
    ...     'break',     # make sure breakpoint is gone
    ...     'continue',
    ... ]):
    ...    test_function()
    > <doctest test.test_pdb.test_pdb_breakpoint_commands[0]>(3)test_function()
    -> print(1)
    (Pdb) break 3
    Breakpoint 1 at <doctest test.test_pdb.test_pdb_breakpoint_commands[0]>:3
    (Pdb) disable 1
    Disabled breakpoint 1 at <doctest test.test_pdb.test_pdb_breakpoint_commands[0]>:3
    (Pdb) ignore 1 10
    Will ignore next 10 crossings of breakpoint 1.
    (Pdb) condition 1 1 < 2
    New condition set for breakpoint 1.
    (Pdb) break 4
    Breakpoint 2 at <doctest test.test_pdb.test_pdb_breakpoint_commands[0]>:4
    (Pdb) break
    Num Type         Disp Enb   Where
    1   breakpoint   keep no    at <doctest test.test_pdb.test_pdb_breakpoint_commands[0]>:3
            stop only if 1 < 2
            ignore next 10 hits
    2   breakpoint   keep yes   at <doctest test.test_pdb.test_pdb_breakpoint_commands[0]>:4
    (Pdb) condition 1
    Breakpoint 1 is now unconditional.
    (Pdb) enable 1
    Enabled breakpoint 1 at <doctest test.test_pdb.test_pdb_breakpoint_commands[0]>:3
    (Pdb) clear 1
    Deleted breakpoint 1 at <doctest test.test_pdb.test_pdb_breakpoint_commands[0]>:3
    (Pdb) commands 2
    (com) print 42
    (com) end
    (Pdb) continue
    1
    42
    > <doctest test.test_pdb.test_pdb_breakpoint_commands[0]>(4)test_function()
    -> print(2)
    (Pdb) clear
    Clear all breaks? y
    Deleted breakpoint 2 at <doctest test.test_pdb.test_pdb_breakpoint_commands[0]>:4
    (Pdb) tbreak 5
    Breakpoint 3 at <doctest test.test_pdb.test_pdb_breakpoint_commands[0]>:5
    (Pdb) continue
    2
    Deleted breakpoint 3 at <doctest test.test_pdb.test_pdb_breakpoint_commands[0]>:5
    > <doctest test.test_pdb.test_pdb_breakpoint_commands[0]>(5)test_function()
    -> print(3)
    (Pdb) break
    (Pdb) continue
    3
    4
    """


def do_nothing():
    pass

def do_something():
    print(42)

def test_list_commands():
    """Test the list and source commands of pdb.

    >>> def test_function_2(foo):
    ...     import test_pdb
    ...     test_pdb.do_nothing()
    ...     'some...'
    ...     'more...'
    ...     'code...'
    ...     'to...'
    ...     'make...'
    ...     'a...'
    ...     'long...'
    ...     'listing...'
    ...     'useful...'
    ...     '...'
    ...     '...'
    ...     return foo

    >>> def test_function():
    ...     import pdb; pdb.Pdb().set_trace()
    ...     ret = test_function_2('baz')

    >>> with PdbTestInput([  # doctest: +ELLIPSIS, +NORMALIZE_WHITESPACE
    ...     'list',      # list first function
    ...     'step',      # step into second function
    ...     'list',      # list second function
    ...     'list',      # continue listing to EOF
    ...     'list 1,3',  # list specific lines
    ...     'list x',    # invalid argument
    ...     'next',      # step to import
    ...     'next',      # step over import
    ...     'step',      # step into do_nothing
    ...     'longlist',  # list all lines
    ...     'source do_something',  # list all lines of function
    ...     'source fooxxx',        # something that doesn't exit
    ...     'continue',
    ... ]):
    ...    test_function()
    > <doctest test.test_pdb.test_list_commands[1]>(3)test_function()
    -> ret = test_function_2('baz')
    (Pdb) list
      1         def test_function():
      2             import pdb; pdb.Pdb().set_trace()
      3  ->         ret = test_function_2('baz')
    [EOF]
    (Pdb) step
    --Call--
    > <doctest test.test_pdb.test_list_commands[0]>(1)test_function_2()
    -> def test_function_2(foo):
    (Pdb) list
      1  ->     def test_function_2(foo):
      2             import test_pdb
      3             test_pdb.do_nothing()
      4             'some...'
      5             'more...'
      6             'code...'
      7             'to...'
      8             'make...'
      9             'a...'
     10             'long...'
     11             'listing...'
    (Pdb) list
     12             'useful...'
     13             '...'
     14             '...'
     15             return foo
    [EOF]
    (Pdb) list 1,3
      1  ->     def test_function_2(foo):
      2             import test_pdb
      3             test_pdb.do_nothing()
    (Pdb) list x
    *** ...
    (Pdb) next
    > <doctest test.test_pdb.test_list_commands[0]>(2)test_function_2()
    -> import test_pdb
    (Pdb) next
    > <doctest test.test_pdb.test_list_commands[0]>(3)test_function_2()
    -> test_pdb.do_nothing()
    (Pdb) step
    --Call--
    > /home/gbr/devel/python/Lib/test/test_pdb.py(260)do_nothing()
    -> def do_nothing():
    (Pdb) longlist
    ...  ->     def do_nothing():
    ...             pass
    (Pdb) source do_something
    ...         def do_something():
    ...             print(42)
    (Pdb) source fooxxx
    *** ...
    (Pdb) continue
    """


def test_pdb_skip_modules():
    """This illustrates the simple case of module skipping.

    >>> def skip_module():
    ...     import string
    ...     import pdb; pdb.Pdb(skip=['stri*']).set_trace()
    ...     string.capwords('FOO')

    >>> with PdbTestInput([
    ...     'step',
    ...     'continue',
    ... ]):
    ...     skip_module()
    > <doctest test.test_pdb.test_pdb_skip_modules[0]>(4)skip_module()
    -> string.capwords('FOO')
    (Pdb) step
    --Return--
    > <doctest test.test_pdb.test_pdb_skip_modules[0]>(4)skip_module()->None
    -> string.capwords('FOO')
    (Pdb) continue
    """


# Module for testing skipping of module that makes a callback
mod = imp.new_module('module_to_skip')
exec('def foo_pony(callback): x = 1; callback(); return None', mod.__dict__)


def test_pdb_skip_modules_with_callback():
    """This illustrates skipping of modules that call into other code.

    >>> def skip_module():
    ...     def callback():
    ...         return None
    ...     import pdb; pdb.Pdb(skip=['module_to_skip*']).set_trace()
    ...     mod.foo_pony(callback)

    >>> with PdbTestInput([
    ...     'step',
    ...     'step',
    ...     'step',
    ...     'step',
    ...     'step',
    ...     'continue',
    ... ]):
    ...     skip_module()
    ...     pass  # provides something to "step" to
    > <doctest test.test_pdb.test_pdb_skip_modules_with_callback[0]>(5)skip_module()
    -> mod.foo_pony(callback)
    (Pdb) step
    --Call--
    > <doctest test.test_pdb.test_pdb_skip_modules_with_callback[0]>(2)callback()
    -> def callback():
    (Pdb) step
    > <doctest test.test_pdb.test_pdb_skip_modules_with_callback[0]>(3)callback()
    -> return None
    (Pdb) step
    --Return--
    > <doctest test.test_pdb.test_pdb_skip_modules_with_callback[0]>(3)callback()->None
    -> return None
    (Pdb) step
    --Return--
    > <doctest test.test_pdb.test_pdb_skip_modules_with_callback[0]>(5)skip_module()->None
    -> mod.foo_pony(callback)
    (Pdb) step
    > <doctest test.test_pdb.test_pdb_skip_modules_with_callback[1]>(10)<module>()
    -> pass  # provides something to "step" to
    (Pdb) continue
    """


def test_pdb_continue_in_bottomframe():
    """Test that "continue" and "next" work properly in bottom frame (issue #5294).

    >>> def test_function():
    ...     import pdb, sys; inst = pdb.Pdb()
    ...     inst.set_trace()
    ...     inst.botframe = sys._getframe()  # hackery to get the right botframe
    ...     print(1)
    ...     print(2)
    ...     print(3)
    ...     print(4)

    >>> with PdbTestInput([  # doctest: +ELLIPSIS
    ...     'next',
    ...     'break 7',
    ...     'continue',
    ...     'next',
    ...     'continue',
    ...     'continue',
    ... ]):
    ...    test_function()
    > <doctest test.test_pdb.test_pdb_continue_in_bottomframe[0]>(4)test_function()
    -> inst.botframe = sys._getframe()  # hackery to get the right botframe
    (Pdb) next
    > <doctest test.test_pdb.test_pdb_continue_in_bottomframe[0]>(5)test_function()
    -> print(1)
    (Pdb) break 7
    Breakpoint ... at <doctest test.test_pdb.test_pdb_continue_in_bottomframe[0]>:7
    (Pdb) continue
    1
    2
    > <doctest test.test_pdb.test_pdb_continue_in_bottomframe[0]>(7)test_function()
    -> print(3)
    (Pdb) next
    3
    > <doctest test.test_pdb.test_pdb_continue_in_bottomframe[0]>(8)test_function()
    -> print(4)
    (Pdb) continue
    4
    """


def pdb_invoke(method, arg):
    """Run pdb.method(arg)."""
    import pdb; getattr(pdb, method)(arg)


def test_pdb_run_with_incorrect_argument():
    """Testing run and runeval with incorrect first argument.

    >>> pti = PdbTestInput(['continue',])
    >>> with pti:
    ...     pdb_invoke('run', lambda x: x)
    Traceback (most recent call last):
    TypeError: exec() arg 1 must be a string, bytes or code object

    >>> with pti:
    ...     pdb_invoke('runeval', lambda x: x)
    Traceback (most recent call last):
    TypeError: eval() arg 1 must be a string, bytes or code object
    """


def test_pdb_run_with_code_object():
    """Testing run and runeval with code object as a first argument.

    >>> with PdbTestInput(['step','x', 'continue']):
    ...     pdb_invoke('run', compile('x=1', '<string>', 'exec'))
    > <string>(1)<module>()
    (Pdb) step
    --Return--
    > <string>(1)<module>()->None
    (Pdb) x
    1
    (Pdb) continue

    >>> with PdbTestInput(['x', 'continue']):
    ...     x=0
    ...     pdb_invoke('runeval', compile('x+1', '<string>', 'eval'))
    > <string>(1)<module>()->None
    (Pdb) x
    1
    (Pdb) continue
    """


class PdbTestCase(unittest.TestCase):

    def test_issue7964(self):
        # open the file as binary so we can force \r\n newline
        with open(support.TESTFN, 'wb') as f:
            f.write(b'print("testing my pdb")\r\n')
        cmd = [sys.executable, '-m', 'pdb', support.TESTFN]
        proc = subprocess.Popen(cmd,
            stdout=subprocess.PIPE,
            stdin=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            )
        stdout, stderr = proc.communicate(b'quit\n')
        self.assertNotIn(b'SyntaxError', stdout,
                         "Got a syntax error running test script under PDB")

    def tearDown(self):
        support.unlink(support.TESTFN)


def test_main():
    from test import test_pdb
    support.run_doctest(test_pdb, verbosity=True)
    support.run_unittest(PdbTestCase)


if __name__ == '__main__':
    test_main()
