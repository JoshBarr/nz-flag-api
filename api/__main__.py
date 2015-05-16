import sys
import os
sys.path.insert(1, os.path.join(sys.path[0], '..'))

from app import app as application

if __name__ == '__main__':
    application.run(debug=True, port=5000)
