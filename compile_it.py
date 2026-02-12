import sys
import py_compile
py_compile.compile(sys.argv[1], cfile=sys.argv[2], doraise=True, quiet=0)
