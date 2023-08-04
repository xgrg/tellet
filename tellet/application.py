from tellet import handlers as h
import os.path as op
import tornado.web
import json
from loguru import logger

DEBUG = True

DIRNAME = '/'.join(op.dirname(op.abspath(__file__)).split('/')[:-1])
STATIC_PATH = op.join(DIRNAME, 'web')
TEMPLATE_PATH = op.join(DIRNAME, 'web')
COOKIE_SECRET = 'L8LwECiNRxq2N0N2eGxx9MZlrpmuMEimlydNX/vt1LP='
logger.info(f'DIRNAME = {DIRNAME}')
global params

class Application(tornado.web.Application):
    def __init__(self, args, config):

        fp = args.filepath
        params = {'session': {'fp':fp}}

        # If fp does not exist, then create it from empty template
        if not op.isfile(fp):
            d = {'shopping': [],
                 'todo': [],
                 'log': [],
                 'fridge': [],
                 'pharmacy': []}
            logger.warning('File not found. Created %s' % fp)
            json.dump(d, open(fp, 'w'))
        else:
            logger.success('Loaded %s' % fp)

        handlers = [(r"/", h.MainHandler, params),
                    (r"/shopping", h.ShoppingHandler, params),
                    (r"/add", h.AddHandler, params),
                    (r"/edit", h.EditHandler, params),
                    (r"/stats", h.StatsHandler, params),
                    (r"/todo", h.TodoHandler, params),
                    (r"/reports", h.ReportsHandler, params),
                    (r"/fridge", h.FridgeHandler, params),
                    (r"/pharmacy", h.PharmacyHandler, params),
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
                                         default_handler_class=h.My404Handler,
                                         autoescape=None, **s)
