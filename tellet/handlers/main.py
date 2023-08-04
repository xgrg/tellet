import tornado.web
import json
import pandas as pd
from datetime import datetime
import os.path as op
from loguru import logger
import git
import numpy as np
import json
from tellet import get_users


def _initialize(self, session):
    self.session = session

    

def get_color_ndays(n, cutoffs=[7, 15], ascending=True):
    mini, maxi = cutoffs
    if ascending:
        if n < mini:
            if ascending:
                return 'bs-callout-info'
            else:
                return 'bs-callout-danger'
        elif n < maxi:
            return 'bs-callout-warning'
        elif n > maxi:
            if ascending:
                return 'bs-callout-danger'
            else:
                return 'bs-callout-info'

class My404Handler(tornado.web.RequestHandler):
    def prepare(self):
        self.set_status(404)
        self.redirect('/')


class BaseHandler(tornado.web.RequestHandler):
    def get_current_user(self):
        return self.get_secure_cookie("user")

    def set_current_user(self, user):
        if user:
            self.set_secure_cookie("user", tornado.escape.json_encode(user))
        else:
            self.clear_cookie("user")


class MainHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        logger.info(f"session = {self.session}")
        if 'ws' not in self.session.keys():
            self.clear_cookie("user")
            self.redirect('/auth/')

        labels = get_users()[self.session['ws']]['users']
        logger.info(f'labels = {labels}')
        username = str(self.current_user[1:-1], 'utf-8')
        logger.success(f'\n*** {username} has just logged in.')

        # Get version tag

        repo = git.Repo(op.dirname(op.dirname(op.dirname(__file__))))
        commit = list(repo.iter_commits(max_count=1))[0]
        dt = datetime.fromtimestamp(commit.committed_date)
        version = datetime.strftime(dt, '%Y%m%d-%H%M%S')
        logger.info(f'version = {version}')

        # Select reports
        j = json.load(open(self.session['fp']))
        
        loglist = j['log']
        logger.success(f'JSON contents successfully loaded. ({len(j["log"])} entries)')
        columns = ['ts', 'who', 'action', 'what', 'where']
        df = pd.DataFrame(loglist, columns=columns).set_index('ts')

        rp = df.query('action == "did" & where == "reports"')
        logger.info(f'{len(rp)} reports collected.')

        # Select specifics
        callout = ''
        if not rp.empty:
            rp['what2'] = rp.apply(lambda row: row.what.split(';')[0], axis=1)

            # last poubelle
            lp = rp.query('what2 == "poubelles"')
            if not lp.empty:
                lp = lp.iloc[0]
                dt = datetime.now() - datetime.strptime(lp.name, '%Y%m%d_%H%M%S')
                comments = lp.what.split(';')[-1]
                if comments != '': comments = ' ' + comments
                opt = {'ndays': dt.days,
                       'who': lp.who,
                       'comments': comments,
                       'color': get_color_ndays(dt.days, [7,15], False)}
                callout = '<div class="bs-callout bs-callout-info {color}">'\
                          'Dernière poubelle il y a <strong>{ndays} jours</strong>'\
                          ' ({who}{comments})</div>'''.format(**opt)

            # # last wc
            # lw = rp.query('what2 == "wc"')
            # if not lw.empty:
            #     lw = lw.iloc[0]
            #     dt = datetime.now() - datetime.strptime(lw.name, '%Y%m%d_%H%M%S')
            #     comments = lw.what.split(';')[-1]
            #     if comments != '': comments = ' ' + comments
            #     opt = {'ndays': dt.days,
            #            'who': lw.who,
            #            'comments': comments,
            #            'color': get_color_ndays(dt.days, [7, 15], True)}
            #     callout = callout + '<div class="bs-callout {color}">'\
            #               'Dernier nettoyage WC il y a <strong>{ndays} jours</strong>'\
            #               ' ({who}{comments})</div>'''.format(**opt)

            # current score + last actions

            # Counts per user
            p0, p1 = labels

            cha = rp.query('who == "%s"'%p0)
            greg = rp.query('who == "%s"'%p1)
            gt = np.sum([int(row.split(';')[2]) for i, row in greg.what.items()])
            ct = np.sum([int(row.split(';')[2]) for i, row in cha.what.items()])


            def count_each(cha):
                last_cha = ''
                if len(cha) != 0:
                    _lc = cha.what.reset_index().iloc[0]
                    ts_cha = datetime.strftime(datetime.strptime(_lc.ts, '%Y%m%d_%H%M%S'), '%d-%m-%Y %H:%M')
                    cha_com = ' (' +  _lc.what.split(';')[-1] +')'
                    if cha_com == ' ()':
                        cha_com = ''
                    last_cha =   ' - ' + _lc.what.split(';')[0] + cha_com + ' (' + ts_cha + ')'
                return last_cha

            opt = {'color': 'bs-callout-info',
                   'greg': len(greg),
                   'cha': len(cha),
                   'gt': gt, 'p0':p0, 'p1': p1,
                   'ct': ct,
                   'last_cha': count_each(cha),
                   'last_greg': count_each(greg)}

            callout = callout + '<div class="bs-callout {color}">'\
                                '{p0}: <b>{cha}</b> 🕑 {ct}{last_cha} <br> '\
                                '{p1}: <b>{greg}</b> 🕑 {gt}{last_greg}</div>'.format(**opt)

            # Is it laundry day
            wd = datetime.now().weekday()
            if wd == 2:
                callout = callout + '<div class="bs-callout bs-callout-warning">'\
                      '<strong>Jour de lessive</strong> &nbsp; '\
                      '<span class="badge bg-warning">Rappel</span></div>'''
            elif wd == 1:
                callout = callout + '<div class="bs-callout bs-callout-warning">'\
                      'Demain jour de lessive &nbsp;'\
                      '<span class="badge bg-warning">Rappel</span></div>'''

        self.render("html/index.html", version=version, callout=callout,
                    ws=self.session['ws'], username=username)

    def initialize(self, **kwargs):
        _initialize(self, **kwargs)


class MoneyHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        action = self.get_argument('action', None)
        if action == 'download':
            j = json.load(open(self.session['fp']))
            loglist = j['log']
            columns = ['ts', 'who', 'action', 'what', 'where']
            df = pd.DataFrame(loglist, columns=columns).query('where == "money"')[['who', 'what']]
            data = []
            for each in df.itertuples():
                row = [each.who, *each.what.split(';')]
                data.append(row)
            columns = ['who', 'desc', 'amount', 'label', 'ts']
            df = pd.DataFrame(data, columns=columns)
            fn = '/tmp/download.xls'

            df.to_excel(fn, index=False, engine="openpyxl")

            buf_size = 4096
            self.set_header('Content-Type', 'application/octet-stream')
            self.set_header('Content-Disposition', 'attachment; filename='\
                            + op.basename(fn))
            with open(fn, 'rb') as f:
                while True:
                    data = f.read(buf_size)
                    if not data:
                        break
                    self.write(data)
            self.finish()
        elif action == 'undo':
            j = json.load(open(self.session['fp']))
            loglist = list(j['log'])
            if len(loglist) > 0:
                loglist2 = [e for e in loglist if e[-1] != 'money']
                moneylist = [e for e in loglist if e[-1] == 'money']
                j['log'] = loglist2
                for e in moneylist[:-1]:
                    j['log'].append(e)
                json.dump(j, open(self.session['fp'], 'w'))

            self.write('File was reset successfully.')
            


    def initialize(self, **kwargs):
        _initialize(self, **kwargs)

