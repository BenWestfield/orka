import os
import sys

ORKAHOME = os.environ['ORKAHOME']

scriptpath = ORKAHOME + 'src'
print scriptpath

# Add the directory containing your module to the Python path (wants absolute paths)
sys.path.append(os.path.abspath(scriptpath))

# Do the import
import lauren
