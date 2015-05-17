import sys
import os
sys.path.insert(1, os.path.join(sys.path[0], '..'))
from app import app as application


if __name__ == '__main__':
    application.run(debug=application.config['DEBUG'],
                    port=application.config['PORT'],
                    host=application.config['HOST'])
