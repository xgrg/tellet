import tornado.web
import json
import difflib
import pandas as pd
from datetime import datetime
import os.path as op
from glob import glob
from loguru import logger
import numpy as np
import json

from tellet.handlers.main import _initialize, BaseHandler


class ListHandler():

    def get_money_list(self):
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
        sl = []
        for row in df.itertuples():
            sl.append(f'''<li class="list-group-item d-flex justify-content-between
                    align-items-left">
                    <span class="badge bg-secondary">{datetime.strftime(datetime.strptime(row.ts, '%Y%m%d'),'%d/%m/%Y')}</span>  {row.amount} € <i>{row.desc}</i>
                    <span>
                    <span class="badge bg-info">{row.label}</span>
                    
                    </li>''')

        list_html = '<div id="itemlist"><ul class="list-group">%s</ul></div>' % ''.join(sl)
        return list_html

    def remove_from_list(self, what, which_list, action):
        username = str(self.current_user[1:-1], 'utf-8')
        j = json.load(open(self.session['fp'])) 
        that_list = j[which_list]

        matches = difflib.get_close_matches(what, that_list)
        logger.info(f'what = {what} that_list = {that_list} matches = {matches}')
        dt = datetime.strftime(datetime.now(), '%Y%m%d_%H%M%S')

        j = json.load(open(self.session['fp']))

        if len(matches) == 0:
            action = 'tried_to_%s' % action
            res = None
        else:
            that_list.remove(matches[0])
            j[which_list] = that_list
            res = that_list

        entry = (dt, username, action, what, which_list)
        j['log'].append(entry)
        json.dump(j, open(self.session['fp'], 'w'), indent=4)
        return res

    def perform_action(self):
        username = str(self.current_user[1:-1], 'utf-8')
        action = str(self.get_argument("action", ""))
        
        what = str(self.get_argument("what", "\n")).split('\n')[0]
        logger.info(f'action = {action} what = {what}')

        if action == 'show':
            html = self.get_list_html()
            self.write(html)
            return

        logger.info(f'username = {username} action = {action} what = {what}')

        that_list = self.remove_from_list(what, self._id, action)
        is_found = that_list is not None
        sl = None
        if is_found:
            sl = 'La liste est vide.'
            if len(that_list) != 0:
                sl = self.get_list_html()

        self.write(json.dumps([is_found, sl]))

    def _get_(self):
        username = str(self.current_user[1:-1], 'utf-8')

        logger.info(f'\n*** {username} is looking at {self._id}.')

        j = json.load(open(self.session['fp']))
        shopping = j[self._id]
        if len(shopping) == 0:
            sl = '<div id="itemlist">Liste vide !</div>'
        else:
            sl = self.get_list_html()

        files = glob(op.join(op.dirname(op.dirname(op.dirname(__file__))),
                              'web/html/modals/*.html'))
        modals = '\n'.join([open(e).read() for e in files])
        self.render("html/%s.html" % self._id, list=sl, modals=modals)

    def get_list_html(self):
        def sort_dates(j):
            res1 = []  # with correct dates
            res2 = []  # with wrong dates
            res3 = []  # without dates
            for each in j:
                label, q, original_q, unit, ed = each.split(';')
                if ed != '':
                    try:
                        ed = datetime.strptime(ed, '%d%m%y')
                        res1.append((label, q, original_q, unit, ed))
                    except ValueError:
                        res2.append(each)
                else:
                    res3.append(each)
            columns = ['label', 'q', 'q1', 'unit', 'ed']
            df = pd.DataFrame(res1, columns=columns).sort_values(by='ed')
            res1b = [e.to_list() for _, e in df.iterrows()]
            res1 = []
            for label, q, original_q, unit, ed in res1b:
                ed = ed.strftime('%d%m%y')
                e = [label, q, original_q, unit, ed]
                res1.append(';'.join(e))

            res = []
            for each in (res1, res2, res3):
                res.extend(each)
            return res

        j = json.load(open(self.session['fp'])) 
        if self._id == 'todo':
            logger.success('Handling money list')
            return self.get_money_list()

        j = j[self._id]
        if len(j) == 0:
            list_html = '<div id="itemlist">Liste vide !</div>'
            return list_html
        if self._id in ('fridge', 'pharmacy'):
            sl = []
            j = sort_dates(j)
            for each in j:
                label, q, original_q, unit, ed = each.split(';')
                if ed != '':
                    try:
                        ed = datetime.strptime(ed, '%d%m%y')
                        dt = ed - datetime.now()
                        style = '&nbsp; (%s)'
                        if dt.days < 0:
                            style = '&nbsp; <span style="color:red; font-weight:600">(%s)</span>'
                        elif dt.days < 2:
                            style = '&nbsp; <span style="color:red">(%s)</span>'
                        elif dt.days < 7:
                            style = '&nbsp; <span style="color:darksalmon">(%s)</span>'
                        ed = 'exp. %s' % ed.strftime('%d-%m-20%y')
                        ed = style % ed
                    except ValueError:
                        ed = ' <span style="color:red; font-weight:600">(%s)</span>' % ed
                if unit == 'units':
                    unit = ''
                    original_q = '/'+original_q
                else:
                    unit = '%'
                    original_q = ''

                sl.append('''<li class="list-group-item d-flex justify-content-between
                      align-items-center" data-data="%s">
                        %s &#8211; %s%s%s%s
                        <span>
                        <span class="badge bg-danger">Editer</span>
                        <span class="badge bg-success">%s </span></span>
                      </li>''' % (each, label, q, original_q, unit, ed,
                                  self._action_label))
        else:
            sl = ['''<li class="list-group-item d-flex justify-content-between
                  align-items-center">
                    %s
                    <span>
                    <span class="badge bg-danger">Editer</span>
                    <span class="badge bg-success">%s </span></span>
                  </li>''' % (each, self._action_label) for each in j]
        list_html = '<div id="itemlist"><ul class="list-group">%s</ul></div>' % ''.join(sl)
        return list_html



class AddHandler(BaseHandler):
    def add_to_list(self, what, which_list):
        username = str(self.current_user[1:-1], 'utf-8')

        j = json.load(open(self.session['fp']))
        that_list = j[which_list]
        that_list.append(what)
        j[which_list] = that_list

        dt = datetime.strftime(datetime.now(), '%Y%m%d_%H%M%S')
        entry = (dt, username, 'add', what, which_list)
        j['log'].append(entry)

        json.dump(j, open(self.session['fp'], 'w'), indent=4)
        return that_list

    @tornado.web.authenticated
    def post(self):
        username = str(self.current_user[1:-1], 'utf-8')
        to = str(self.get_argument("to", ""))
        what = str(self.get_argument("what", ""))
        # then = str(self.get_argument("then", to))

        _what = what.split("\n")[0]
        logger.info(f'{username} is adding {_what} to {to}')
        if to not in ['log', 'reports', 'money']:
            shopping = self.add_to_list(what, to)
            logger.info(f'shopping = {shopping}')
            self.write(json.dumps(True))

        else: # log
            j = json.load(open(self.session['fp']))
            dt = datetime.strftime(datetime.now(), '%Y%m%d_%H%M%S')
            entry = (dt, username, 'did', what, to)
            j['log'].append(entry)
            json.dump(j, open(self.session['fp'], 'w'), indent=4)

        if to == 'money':
            self.write(json.dumps(True))


    def initialize(self, **kwargs):
        _initialize(self, **kwargs)


class EditHandler(BaseHandler):
    def add_to_list(self, what, which_list, item):
        username = str(self.current_user[1:-1], 'utf-8')

        #j = json.load(open(self.fp))
        j = json.load(open(self.session['fp']))
        that_list = j[which_list]
        i = that_list.index(item)
        that_list.remove(item)
        that_list.insert(i, what)
        j[which_list] = that_list

        dt = datetime.strftime(datetime.now(), '%Y%m%d_%H%M%S')
        entry = (dt, username, 'edit', what, which_list)
        j['log'].append(entry)

        json.dump(j, open(self.session['fp'], 'w'), indent=4)
        # hk.dump_to_db(j, self.session['ws'])
        return that_list

    @tornado.web.authenticated
    def post(self):
        username = str(self.current_user[1:-1], 'utf-8')
        to = str(self.get_argument("to", ""))
        what = str(self.get_argument("what", ""))
        item = str(self.get_argument("item", ""))
        # then = str(self.get_argument("then", to))
        logger.info('to = {to}')

        _what = what.split("\n")[0]
        logger.info(f'{username} to {_what}')
        if to != 'log':
            shopping = self.add_to_list(what, to, item)
            self.write(json.dumps(True))
        else: # log
            #j = json.load(open(self.fp))
            j = json.load(open(self.session['fp'])) # hk.dump_to_json(self.session['ws'])
            dt = datetime.strftime(datetime.now(), '%Y%m%d_%H%M%S')
            entry = (dt, username, 'did', what, to)
            j['log'].append(entry)
            json.dump(j, open(self.session['fp'], 'w'), indent=4)
            # hk.dump_to_db(j, self.session['ws'])

    def initialize(self, **kwargs):
        _initialize(self, **kwargs)