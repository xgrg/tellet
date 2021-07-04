import tornado
from tornado.options import define
import argparse
from tellet import application

import logging as log
import sys

log.basicConfig(level=log.DEBUG,
                format='%(asctime)s - %(levelname)-8s - %(message)s',
                datefmt='%d/%m/%Y %Hh%Mm%Ss')
console = log.StreamHandler(sys.stderr)


define("port", default=8890, help="run on the given port", type=int)


def main(args):
    app = application.Application(args, config={})
    http_server = tornado.httpserver.HTTPServer(app)
    http_server.listen(args.port)
    t = tornado.ioloop.IOLoop.instance()
    return http_server, t


def create_parser():
    parser = argparse.ArgumentParser(description='Tellet app')
    parser.add_argument('filepath')
    parser.add_argument('--port', required=False, default=8890)
    return parser


if __name__ == "__main__":
    parser = create_parser()
    args = parser.parse_args()
    server, t = main(args)
    t.start()
