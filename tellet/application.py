from tellet import handlers as h
import os.path as op
import tornado.web

DEBUG = True

DIRNAME = '/'.join(op.dirname(op.abspath(__file__)).split('/')[:-1])
STATIC_PATH = op.join(DIRNAME, 'web')
TEMPLATE_PATH = op.join(DIRNAME, 'web')
COOKIE_SECRET = 'L8LwECiNRxq2N0N2eGxx9MZlrpmuMEimlydNX/vt1LP='
print(DIRNAME)


class Application(tornado.web.Application):
    def __init__(self, args, config):

        params = {'fp': args.filepath}

        handlers = [
            (r"/", h.MainHandler, params),
            (r"/shopping", h.ShoppingHandler, params),
            (r"/add", h.AddHandler, params),
            (r"/stats", h.StatsHandler, params),
            (r"/todo", h.TodoHandler, params),
            (r"/reports", h.ReportsHandler, params),
            (r"/auth/login", h.AuthLoginHandler, params),
            (r"/auth/logout", h.AuthLogoutHandler)]

        s = {
            "autoreload": True,
            "template_path": TEMPLATE_PATH,
            "static_path": STATIC_PATH,
            "debug": DEBUG,
            "cookie_secret": COOKIE_SECRET,
            "login_url": "/auth/login"
        }
        tornado.web.Application.__init__(self, handlers,
            default_handler_class=h.My404Handler, autoescape=None, **s)
