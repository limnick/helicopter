import cherrypy, os
from cherrypy.lib.static import serve_file
abs_path = os.path.dirname(os.path.realpath(__file__))

print '%s/'%(abs_path)
class Root:
    static_handler = cherrypy.tools.staticdir.handler(section='/', dir='%s/'%(abs_path))
    cherrypy.tree.mount(static_handler, '/game')
    
    
if __name__ == '__main__':
    pwd = os.path.dirname(os.path.abspath(__file__))
    cherrypy.config.update('gserver.conf')
    cherrypy.quickstart(Root())