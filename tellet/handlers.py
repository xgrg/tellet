import tornado.web
import json
import difflib
import pandas as pd
from datetime import datetime
import os.path as op


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
        rp['what2'] = rp.apply(lambda row: row.what.split(';')[0], axis=1)


        # last poubelle
        rp = df.query('action == "did" & where == "reports"')
        rp['what2'] = rp.apply(lambda row: row.what.split(';')[0], axis=1)
        lp = rp.query('what2 == "poubelles"').iloc[0]
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
        lw = rp.query('what2 == "wc"').iloc[0]
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


def get_list_html(j, action_label):
    sl = ['''<li class="list-group-item d-flex justify-content-between
              align-items-center">
                %s
                <span>
                <span class="badge bg-danger">Retirer</span>
                <span class="badge bg-success">%s </span></span>
              </li>''' % (each, action_label) for each in j]
    list_html = '<div id="itemlist"><ul class="list-group">%s</ul></div>' % ''.join(sl)
    return list_html


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


class ShoppingHandler(BaseHandler, ListHandler):
    @tornado.web.authenticated
    def get(self):
        username = str(self.current_user[1:-1], 'utf-8')

        print('\n*** %s is shopping.' % username)
        shopping = json.load(open(self.fp))['shopping']
        sl = get_list_html(shopping, action_label='Acheté')
        self.render("html/shopping.html", list=sl)

    def post(self):
        username = str(self.current_user[1:-1], 'utf-8')
        action = str(self.get_argument("action", ""))
        what = str(self.get_argument("what", "\n")).split('\n')[0]

        print((username, action, what))

        that_list = self.remove_from_list(what, 'shopping', action)
        is_found = that_list is not None
        sl = None
        if is_found:
            sl = 'La liste est vide. Rien à acheter !'
            if len(that_list) != 0:
                sl = get_list_html(that_list, action_label='Acheté')

        self.write(json.dumps([is_found, sl]))

    def initialize(self, **kwargs):
        _initialize(self, **kwargs)


class TodoHandler(BaseHandler, ListHandler):
    @tornado.web.authenticated
    def get(self):
        username = str(self.current_user[1:-1], 'utf-8')
        print('\n*** %s is todoing.' % username)
        todo = json.load(open(self.fp))['todo']
        tl = get_list_html(todo, action_label='Effectué')
        self.render("html/todo.html", list=tl)

    def post(self):
        username = str(self.current_user[1:-1], 'utf-8')
        action = str(self.get_argument("action", ""))
        what = str(self.get_argument("what", "")).split('\n')[0]

        print((username, action, what))
        that_list = self.remove_from_list(what, 'todo', action)
        is_found = that_list is not None
        sl = None
        if is_found:
            sl = 'La liste est vide. Rien à faire !'
            if len(that_list) != 0:
                sl = get_list_html(that_list, action_label='Effectué')
        self.write(json.dumps([is_found, sl]))

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

        print((username, to, what.split('\n')[0]))
        if to in ['shopping', 'todo']:
            shopping = self.add_to_list(what, to)
            sl = get_list_html(shopping, action_label='Acheté')
            self.write(json.dumps([True, sl]))
        else:
            j = json.load(open(self.fp))

            dt = datetime.strftime(datetime.now(), '%Y%m%d_%H%M%S')
            entry = (dt, username, 'did', what, to)
            j['log'].append(entry)
            json.dump(j, open(self.fp, 'w'), indent=4)

    def initialize(self, **kwargs):
        _initialize(self, **kwargs)


def get_doughnut(df, label='My dataset'):
    labels = ['Greg', 'Cha']
    data = []
    for i in labels:
        data.append(len(df.query('who == "%s" & action == "did"' % i)))

    graph = {'labels': labels,
             'datasets': [{'label': label,
                           'data': data,
                           'backgroundColor': ['rgb(54, 162, 235)',
                                               'rgb(255, 99, 132)'],
                           'hoverOffset': 4}]}

    config = {'type': 'doughnut',
              'data': graph}
    return config


def get_radar(df, label='My dataset'):
    labels = ['Greg', 'Cha']

    actions = ['aspirateur', 'lavevaisselle', 'linge', 'lessive',
               'litière', 'nettoyer', 'pavé', 'douche', 'wc', 'piscine',
               'poubelles', 'cuisine', 'autres']
    sorted_actions = {}
    for i, row in df.iterrows():
        if row.action != 'did' or str(row['where']) != 'reports': continue
        sorted_actions.setdefault(row.who, {})
        what = row.what
        has_found = False
        for a in actions[:-1]:
            sorted_actions[row.who].setdefault(a, [])
            if what.startswith(a):
                sorted_actions[row.who][a].append(what)
                has_found = True
        if not has_found:
            sorted_actions[row.who].setdefault('autres', [])
            sorted_actions[row.who]['autres'].append(row.what)
    print(sorted_actions['Cha']['autres'])
    print(sorted_actions['Greg']['autres'])

    datasets = []
    colors = [{'backgroundColor': 'rgba(54, 162, 235, 0.2)',
               'borderColor': 'rgb(54, 162, 235)',
               'pointBackgroundColor': 'rgb(54, 162, 235)',
               'pointBorderColor': '#fff',
               'pointHoverBackgroundColor': '#fff',
               'pointHoverBorderColor': 'rgb(54, 162, 235)'},
              {'backgroundColor': 'rgba(255, 99, 132, 0.2)',
               'borderColor': 'rgb(255, 99, 132)',
               'pointBackgroundColor': 'rgb(255, 99, 132)',
               'pointBorderColor': '#fff',
               'pointHoverBackgroundColor': '#fff',
               'pointHoverBorderColor': 'rgb(255, 99, 132)'}]

    for who, c in zip(labels, colors):
        d = {'label': who,
             'data': [len(sorted_actions[who][a]) for a in actions],
             'fill': True}
        d.update(c)
        datasets.append(d)

    data = {'labels': actions,
            'datasets': datasets}
    options = {'elements': {'line': {'borderWidth': 3}},
               'plugins': {'colorschemes': {'scheme': 'brewer.SetThree12'}}}

    config = {'type': 'radar',
              'data': data,
              'options': options}
    return config


def get_stacked_doughnut(df):
    sorted_actions = {}
    for i, row in df.iterrows():
        if row.action != 'did' or str(row['where']) != 'reports': continue
        sorted_actions.setdefault(row.who, {})
        items = row.what.split(';')
        what = items[0]
        duration = items[2]
        sorted_actions[row.who].setdefault(duration, [])
        sorted_actions[row.who][duration].append(what)

    d1 = [len(sorted_actions['Cha'].get(e, [])) for e in '012345']
    d2 = [len(sorted_actions['Greg'].get(e, [])) for e in '012345']

    data = {'labels': ['<1 min', '1-7 min', '10-15 min', '20-30 min',
                       '>30 min', '>2 h'],
            'datasets': [{'label': 'Cha',
                          'data': d1,
                          'borderColor': 'rgb(255, 99, 132)',
                          'backgroundColor': 'rgba(255, 99, 132, 0.2)'},
                         {'label': 'Greg',
                          'data': d2,
                          'borderColor': 'rgb(54, 162, 235)',
                          'backgroundColor': 'rgba(54, 162, 235, 0.2)'}]}

    config = {'type': 'bar',
              'data': data,
              'options': {
                'indexAxis': 'y',
                'elements': {'bar': {'borderWidth': 2}},
                'responsive': True,
                'plugins': {
                  'legend': {'position': 'right'}
                 }
              }}
    return config


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
        graph1 = get_doughnut(df, '# total de contributions')
        graph2 = get_radar(df, 'Répartition des actions')
        graph3 = get_stacked_doughnut(df)
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
