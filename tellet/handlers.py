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

        self.render("html/index.html", version=version)

    def initialize(self, **kwargs):
        _initialize(self, **kwargs)


def get_list_html(j, action_label):
    sl = ['''<li class="list-group-item d-flex justify-content-between
              align-items-center">
                %s
                <span class="badge badge-pill badge-danger">Retirer</span>
                <span class="badge badge-pill badge-success">%s </span>
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

        html = '''
        <style>
            .df tbody tr:nth-child(even) { background-color: lightblue; }
        </style>
        ''' + df.to_html(classes="df")
        self.render("html/stats.html", list=html)

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
        return True

    def post(self):
        username = str(self.get_argument("username", ""))

        auth = self.check_permission(username)
        if auth:
            self.set_current_user(username)
            self.redirect(u"/")
        else:
            error_msg = u"?error=" + tornado.escape.url_escape("Wrong login/password.")
            self.redirect(u"/auth/login/" + error_msg)

    def initialize(self, **kwargs):
        _initialize(self, **kwargs)
