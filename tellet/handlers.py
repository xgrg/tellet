import tornado.web
import json


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

        self.render("html/index.html")

    def initialize(self, **kwargs):
        _initialize(self, **kwargs)


def get_list_html(j):
    sl = ['''<li class="list-group-item d-flex justify-content-between align-items-center">
                %s
                <span class="badge badge-pill badge-danger">Retirer</span>
                <span class="badge badge-pill badge-success">Acheté</span>
              </li>''' % each for each in j]
    list_html = '<div id="itemlist"><ul class="list-group">%s</ul></div>' % ''.join(sl)
    return list_html


class ShoppingHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        username = str(self.current_user[1:-1], 'utf-8')

        print('\n*** %s is shopping.' % username)
        shopping = json.load(open(self.fp))['shopping']
        sl = get_list_html(shopping)

        self.render("html/shopping.html", list=sl)

    def post(self):
        username = str(self.current_user[1:-1], 'utf-8')
        action = str(self.get_argument("action", ""))
        what = str(self.get_argument("what", "\n")).split('\n')[0]

        print((username, action, what))
        if action == 'remove':
            shopping = json.load(open(self.fp))['shopping']
            import difflib
            matches = difflib.get_close_matches(what, shopping)
            print(matches)
            if len(matches) == 0:
                self.write(json.dumps([False]))
            else:
                shopping.remove(matches[0])
                j = json.load(open(self.fp))
                j['shopping'] = shopping
                json.dump(j, open(self.fp, 'w'))
                if len(shopping) != 0:
                    sl = get_list_html(shopping)
                else:
                    sl = 'La liste est vide. Rien à acheter !'
                self.write(json.dumps([True, sl]))

    def initialize(self, **kwargs):
        _initialize(self, **kwargs)


class StatsHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        username = str(self.current_user[1:-1], 'utf-8')
        print('\n*** %s is stating.' % username)

        self.render("html/stats.html")

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


class TodoHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        username = str(self.current_user[1:-1], 'utf-8')
        print('\n*** %s is todoing.' % username)
        todo = json.load(open(self.fp))['todo']
        tl = get_list_html(todo)
        self.render("html/todo.html", list=tl)

    def post(self):
        username = str(self.current_user[1:-1], 'utf-8')
        action = str(self.get_argument("action", ""))
        what = str(self.get_argument("what", ""))

        print((username, action, what.split('\n')[0]))
        if action == 'remove':
            todo = json.load(open(self.fp))['todo']

    def initialize(self, **kwargs):
        _initialize(self, **kwargs)


class AddHandler(BaseHandler):
    @tornado.web.authenticated
    def post(self):
        username = str(self.current_user[1:-1], 'utf-8')
        to = str(self.get_argument("to", ""))
        what = str(self.get_argument("what", ""))

        print((username, to, what.split('\n')[0]))
        if to == 'shopping':
            j = json.load(open(self.fp))
            shopping = j['shopping']
            shopping.append(what)
            j['shopping'] = shopping
            json.dump(j, open(self.fp, 'w'))
            sl = get_list_html(shopping)
            self.write(json.dumps([True, sl]))

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
