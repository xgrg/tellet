import tornado.web
import json
import difflib
import pandas as pd
from datetime import datetime
import os.path as op

actions_labels = {'shopping': 'Acheté',
                  'todo': 'Fait',
                  'fridge': 'Utiliser',
                  'pharmacy': 'Utiliser'}


class BaseHandler(tornado.web.RequestHandler):
    def get_current_user(self):
        return self.get_secure_cookie("user")

    def set_current_user(self, user):
        if user:
            self.set_secure_cookie("user", tornado.escape.json_encode(user))
        else:
            self.clear_cookie("user")


class My404Handler(tornado.web.RequestHandler):
    # Override prepare() instead of get() to cover all possible HTTP methods.
    def prepare(self):
        self.set_status(404)
        self.redirect('/')


def _initialize(self, fp):
    self.fp = fp


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


class MainHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        username = str(self.current_user[1:-1], 'utf-8')
        print('\n*** %s has just logged in.' % username)
        import git
        repo = git.Repo(op.dirname(op.dirname(__file__)))
        commit = list(repo.iter_commits(max_count=1))[0]
        dt = datetime.fromtimestamp(commit.committed_date)
        version = datetime.strftime(dt, '%Y%m%d-%H%M%S')

        loglist = json.load(open(self.fp))['log']
        columns = ['ts', 'who', 'action', 'what', 'where']
        df = pd.DataFrame(loglist, columns=columns).set_index('ts')
        df = df.sort_index(ascending=False)
        rp = df.query('action == "did" & where == "reports"')

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

            # last wc
            lw = rp.query('what2 == "wc"')
            if not lw.empty:
                lw = lw.iloc[0]
                dt = datetime.now() - datetime.strptime(lw.name, '%Y%m%d_%H%M%S')
                comments = lw.what.split(';')[-1]
                if comments != '': comments = ' ' + comments
                opt = {'ndays': dt.days,
                       'who': lw.who,
                       'comments': comments,
                       'color': get_color_ndays(dt.days, [7, 15], True)}
                callout = callout + '<div class="bs-callout {color}">'\
                          'Dernier nettoyage WC il y a <strong>{ndays} jours</strong>'\
                          ' ({who}{comments})</div>'''.format(**opt)

            # is it laundry day
            wd = datetime.now().weekday()
            if wd == 2:
                callout = callout + '<div class="bs-callout bs-callout-warning">'\
                      '<strong>Jour de lessive</strong> &nbsp; '\
                      '<span class="badge bg-warning">Rappel</span></div>'''
            elif wd == 1:
                callout = callout + '<div class="bs-callout bs-callout-warning">'\
                      'Demain jour de lessive &nbsp;'\
                      '<span class="badge bg-warning">Rappel</span></div>'''

        self.render("html/index.html", version=version, callout=callout)

    def initialize(self, **kwargs):
        _initialize(self, **kwargs)


class ListHandler():
    def remove_from_list(self, what, which_list, action):
        username = str(self.current_user[1:-1], 'utf-8')
        that_list = json.load(open(self.fp))[which_list]

        matches = difflib.get_close_matches(what, that_list)
        print(what, that_list, matches)
        dt = datetime.strftime(datetime.now(), '%Y%m%d_%H%M%S')
        j = json.load(open(self.fp))

        if len(matches) == 0:
            action = 'tried_to_%s' % action
            res = None
        else:
            that_list.remove(matches[0])
            j[which_list] = that_list
            res = that_list

        entry = (dt, username, action, what, which_list)
        j['log'].append(entry)
        json.dump(j, open(self.fp, 'w'), indent=4)
        return res

    def perform_action(self):
        username = str(self.current_user[1:-1], 'utf-8')
        action = str(self.get_argument("action", ""))
        print(str(self.get_argument("what", "\n")))
        what = str(self.get_argument("what", "\n")).split('\n')[0]

        if action == 'show':
            html = self.get_list_html()
            self.write(html)
            return

        print((username, action, what))

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

        print('\n*** %s is looking at %s.' % (username, self._id))
        shopping = json.load(open(self.fp))[self._id]
        if len(shopping) == 0:
            sl = '<div id="itemlist">Liste vide !</div>'
        else:
            sl = self.get_list_html()

        from glob import glob
        files = glob(op.join(op.dirname(op.dirname(__file__)),
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

        j = json.load(open(self.fp))[self._id]
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

                sl.append('''<li class="list-group-item d-flex justify-content-between
                      align-items-center" data-data="%s">
                        %s &#8211; %s/%s %s%s
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
        self._get_()

    def post(self):
        self.perform_action()

    def initialize(self, **kwargs):
        _initialize(self, **kwargs)


class AddHandler(BaseHandler):
    def add_to_list(self, what, which_list):
        username = str(self.current_user[1:-1], 'utf-8')

        j = json.load(open(self.fp))
        that_list = j[which_list]
        that_list.append(what)
        j[which_list] = that_list

        dt = datetime.strftime(datetime.now(), '%Y%m%d_%H%M%S')
        entry = (dt, username, 'add', what, which_list)
        j['log'].append(entry)

        json.dump(j, open(self.fp, 'w'), indent=4)
        return that_list

    @tornado.web.authenticated
    def post(self):
        username = str(self.current_user[1:-1], 'utf-8')
        to = str(self.get_argument("to", ""))
        what = str(self.get_argument("what", ""))
        # then = str(self.get_argument("then", to))

        print((username, 'adding', what.split('\n')[0], 'to', to))
        if to in actions_labels.keys():
            shopping = self.add_to_list(what, to)
            print(shopping)
            # if then != to:
            #     j = json.load(open(self.fp))
            #     shopping = j[then]
            # sl = self.get_list_html(shopping, action_label=actions_labels[to],
            #                    fridge=then in ('fridge', 'pharmacy'))
            self.write(json.dumps(True))
        else: # log
            j = json.load(open(self.fp))

            dt = datetime.strftime(datetime.now(), '%Y%m%d_%H%M%S')
            entry = (dt, username, 'did', what, to)
            j['log'].append(entry)
            json.dump(j, open(self.fp, 'w'), indent=4)

    def initialize(self, **kwargs):
        _initialize(self, **kwargs)


class EditHandler(BaseHandler):
    def add_to_list(self, what, which_list, item):
        username = str(self.current_user[1:-1], 'utf-8')

        j = json.load(open(self.fp))
        that_list = j[which_list]
        i = that_list.index(item)
        that_list.remove(item)
        that_list.insert(i, what)
        j[which_list] = that_list

        dt = datetime.strftime(datetime.now(), '%Y%m%d_%H%M%S')
        entry = (dt, username, 'edit', what, which_list)
        j['log'].append(entry)

        json.dump(j, open(self.fp, 'w'), indent=4)
        return that_list

    @tornado.web.authenticated
    def post(self):
        username = str(self.current_user[1:-1], 'utf-8')
        to = str(self.get_argument("to", ""))
        what = str(self.get_argument("what", ""))
        item = str(self.get_argument("item", ""))
        # then = str(self.get_argument("then", to))
        print('to', to)

        print((username, to, what.split('\n')[0]))
        if to in actions_labels.keys():
            shopping = self.add_to_list(what, to, item)
            # if then != to:
            #     j = json.load(open(self.fp))
            #     shopping = j[then]
            # sl = get_list_html(shopping, action_label=actions_labels[to],
            #                    fridge=to in ('fridge', 'pharmacy'))

            self.write(json.dumps(True))
        else: # log
            j = json.load(open(self.fp))

            dt = datetime.strftime(datetime.now(), '%Y%m%d_%H%M%S')
            entry = (dt, username, 'did', what, to)
            j['log'].append(entry)
            json.dump(j, open(self.fp, 'w'), indent=4)

    def initialize(self, **kwargs):
        _initialize(self, **kwargs)


class StatsHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        username = str(self.current_user[1:-1], 'utf-8')
        print('\n*** %s is stating.' % username)

        loglist = json.load(open(self.fp))['log']
        columns = ['ts', 'who', 'action', 'what', 'where']
        df = pd.DataFrame(loglist, columns=columns).set_index('ts')
        df = df.sort_index(ascending=False)

        html = '''
        <style>
            table.df { display: block;
            overflow-x: auto;
            white-space: nowrap;}
            .df tbody tr:nth-child(even) { background-color: lightblue; }
        </style>
        ''' + df.to_html(classes="df")
        self.render("html/stats.html", list=html)

    def post(self):
        loglist = json.load(open(self.fp))['log']
        columns = ['ts', 'who', 'action', 'what', 'where']
        df = pd.DataFrame(loglist, columns=columns).set_index('ts')

        # n total
        from tellet import stats
        graph1 = stats.get_doughnut(df, '# total de contributions')
        graph2 = stats.get_radar(df, 'Répartition des actions')
        graph3 = stats.get_stacked_doughnut(df)
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
        print('\n*** %s is reporting.' % username)

        self.render("html/reports.html")

    def initialize(self, **kwargs):
        _initialize(self, **kwargs)


class AuthLogoutHandler(BaseHandler):
    def get(self):
        self.clear_cookie("user")
        self.redirect(self.get_argument("next", "/"))


class AuthLoginHandler(BaseHandler):
    def get(self):
        try:
            errormessage = self.get_argument("error")
        except Exception:
            errormessage = ""

        self.render("html/login.html", errormessage=errormessage,)

    def check_permission(self, username):
        if username in ['Cha', 'Greg']:
            print(username)
            return True

    def post(self):
        username = str(self.get_argument("username", ""))

        auth = self.check_permission(username)
        if auth:
            self.set_current_user(username)
            self.write(json.dumps([]))
        else:
            error_msg = u"?error=" + tornado.escape.url_escape("Wrong login/password.")
            self.redirect(u"/auth/login/" + error_msg)

    def initialize(self, **kwargs):
        _initialize(self, **kwargs)
