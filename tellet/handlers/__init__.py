import tornado.web
import json
import pandas as pd
import os.path as op
from loguru import logger
import git
import numpy as np
import json

from glob import glob

from tellet import stats, get_users
from tellet.handlers.main import BaseHandler, _initialize
from tellet.handlers.list import ListHandler



class ShoppingHandler(BaseHandler, ListHandler):
    _id = 'shopping'
    _action_label = 'Acheté'

    @tornado.web.authenticated
    def get(self):
        self._get_()

    def post(self):
        self.perform_action()

    def initialize(self, **kwargs):
        _initialize(self, **kwargs)


class PharmacyHandler(BaseHandler, ListHandler):
    _id = 'pharmacy'
    _action_label = 'Utiliser'

    @tornado.web.authenticated
    def get(self):
        self._get_()

    def post(self):
        self.perform_action()

    def initialize(self, **kwargs):
        _initialize(self, **kwargs)


class FridgeHandler(BaseHandler, ListHandler):
    _id = 'fridge'
    _action_label = 'Utiliser'

    @tornado.web.authenticated
    def get(self):
        self._get_()

    def post(self):
        self.perform_action()

    def initialize(self, **kwargs):
        _initialize(self, **kwargs)
    

class TodoHandler(BaseHandler, ListHandler):
    _id = 'todo'
    _action_label = 'Fait'

    @tornado.web.authenticated
    def get(self):
        username = str(self.current_user[1:-1], 'utf-8')
        logger.info(f'*** {username} is looking at money.')

        log = self.get_money_list()

        files = glob(op.join(op.dirname(op.dirname(op.dirname(__file__))),
                              'web/html/modals/*.html'))
        modals = '\n'.join([open(e).read() for e in files])

        self.render("html/todo.html", modals=modals, reports=log)

    def post(self):
        self.perform_action()

    def initialize(self, **kwargs):
        _initialize(self, **kwargs)




class StatsHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        username = str(self.current_user[1:-1], 'utf-8')
        logger.info(f'*** {username} is looking at stats.')

        j = json.load(open(self.session['fp']))
        loglist = j['log']
        columns = ['ts', 'who', 'action', 'what', 'where']
        data = pd.DataFrame(loglist, columns=columns).set_index('ts')
        df = data.query('where != "reports"')
        df = df.sort_index(ascending=False)

        tpl = '''
        <style>
            table.df { display: block;
            overflow-x: auto;
            white-space: nowrap;}
            .df tbody tr:nth-child(even) { background-color: lightblue; }
        </style>
        '''
        log = tpl + df.to_html(classes="df")

        df = data.query('where == "reports"')
        df = df.sort_index(ascending=False)
        reports = tpl + df.to_html(classes="df")
        self.render("html/stats.html", reports=reports, log=log)

    def post(self):
        j = json.load(open(self.session['fp'])) 
        loglist = j['log']
        columns = ['ts', 'who', 'action', 'what', 'where']
        df = pd.DataFrame(loglist, columns=columns).set_index('ts')

        # n total
        graph1 = stats.get_doughnut(df, '# total de contributions', self.session['ws'])
        graph2 = stats.get_radar(df, 'Répartition des actions', self.session['ws'])
        graph3 = stats.get_stacked_doughnut(df, self.session['ws'])
        config = {'ntotal': graph1,
                  'radar': graph2,
                  'stacked': graph3}

        self.write(json.dumps(config))

    def initialize(self, **kwargs):
        _initialize(self, **kwargs)



class ReportsHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        username = str(self.current_user[1:-1], 'utf-8')
        logger.info(f'*** {username} is reporting.')
        users = get_users()[self.session['ws']]
        rep = users.get('reports', [])
        default_reports = [('Passer le pavé', 'cleaning', 'pavé'),
                           ('Passer l\'aspirateur', 'vacuum', 'aspirateur'),
                           ('Faire une lessive', 'washingmachine', 'lessive'),
                           ('Piscine', 'swimmingpool', 'piscine'),
                           ('Nettoyer la douche', 'shower', 'douche'),
                           ('Nettoyer une surface', 'cleaningsurface', 'nettoyer'),
                           ('Sortir poubelles', 'trashout', 'poubelles'),
                           ('(D)étendre le linge', 'hangingclothes', 'linge'),
                           ('Vider le lave-vaisselle', 'dishwasher', 'lavevaisselle'),
                           ('Nettoyer WC', 'toilet', 'wc'),
                           ('Préparer le repas', 'cooking', 'cuisine'),
                           ('Arroser les plantes', 'waterplants', 'plantes')]

        rep.extend(default_reports)
        tpl2 = """<p><div class="col-md-6">{buttons}</div></p>"""
        tpl = """<button type="button" class="btn btn-secondary">
                    <img id="{id}" data-description="{desc}" data-value="{value}" width=75 src="/static/data/icons/{id}.png">
                 </button> """
        reports = []
        for desc, id, value in rep:
            reports.append(tpl.format(id=id, desc=desc, value=value))

        html_reports = ''
        i = 0
        while i < len(reports):
            html_reports += tpl2.format(buttons=''.join(reports[i:i+3]))
            i += 3

        self.render("html/reports.html", reports=html_reports)

    def initialize(self, **kwargs):
        _initialize(self, **kwargs)




class AuthLogoutHandler(BaseHandler):
    def get(self):
        self.clear_cookie("user")
        self.redirect("/")


class AuthLoginHandler(BaseHandler):
    def get(self):
        ws = self.get_argument('id', self.session.get('ws', ''))
        try:
            errormessage = self.get_argument("error")
        except Exception:
            errormessage = ""
        ws = 'cha'
        self.render("html/login.html", ws=ws,
                    errormessage=errormessage, users=json.dumps(get_users()))

    def post(self):
        username = str(self.get_argument("username", ""))
        ws = str(self.get_argument("workspace", ""))
        self.set_current_user(username)
        self.session['ws'] = ws
        self.write(json.dumps([]))

    def initialize(self, **kwargs):
        _initialize(self, **kwargs)
