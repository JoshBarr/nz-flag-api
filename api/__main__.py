import sys
import os
sys.path.insert(1, os.path.join(sys.path[0], '..'))
from app import app as application
from app import cache


if __name__ == '__main__':

    if len(sys.argv) > 1:
        if sys.argv[1] == '--clearcache':
            cache.clear()
            print "Cleared the cache"
            exit()

    application.run(debug=application.config['DEBUG'],
                    port=application.config['PORT'],
                    host=application.config['HOST'])
