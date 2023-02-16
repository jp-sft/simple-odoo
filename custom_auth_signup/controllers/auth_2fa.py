import logging
import odoo
import ipdb
import werkzeug

from odoo import http
from odoo.addons.web.controllers.main import Home,ensure_db,SIGN_UP_REQUEST_PARAMS
from odoo.http import request
from odoo.tools import plaintext2html, html_sanitize
import random
import string

_logger = logging.getLogger(__name__)



class TwoFactorAuthController(Home):

    @http.route('/web/login', type='http', auth="none", website=True)
    def web_login(self, redirect=None, **kw):
        ensure_db()
        request.params['login_success'] = False
        if request.httprequest.method == 'GET' and redirect and request.session.uid:
            return request.redirect(redirect)

        if not request.uid:
            request.uid = odoo.SUPERUSER_ID

        values = {k: v for k, v in request.params.items() if k in SIGN_UP_REQUEST_PARAMS}
        try:
            values['databases'] = http.db_list()
        except odoo.exceptions.AccessDenied:
            values['databases'] = None

        if request.httprequest.method == 'POST':
            old_uid = request.uid
            try:
                wsgienv = request.httprequest.environ
                env = dict(
                    interactive=True,
                    base_location=request.httprequest.url_root.rstrip('/'),
                    HTTP_HOST=wsgienv['HTTP_HOST'],
                    REMOTE_ADDR=wsgienv['REMOTE_ADDR'],
                )
                uid = odoo.registry(request.session.db)['res.users'].authenticate(request.session.db, request.params['login'], request.params['password'], env)
                request.session["uid_2fa"] = uid
                request.session["login"] = request.params['login']
                request.session["password"] = request.params['password']
                
                if uid: 
                    return werkzeug.utils.redirect('/two_factor_auth')
                else:
                    raise odoo.exceptions.AccessDenied
                # uid = request.session.authenticate(request.session.db, request.params['login'], request.params['password'])

                # request.params['login_success'] = True
                # return request.redirect(self._login_redirect(uid, redirect=redirect))
            except odoo.exceptions.AccessDenied as e:
                request.uid = old_uid
                if e.args == odoo.exceptions.AccessDenied().args:
                    values['error'] = _("Wrong login/password")
                else:
                    values['error'] = e.args[0]
        else:
            if 'error' in request.params and request.params.get('error') == 'access':
                values['error'] = _('Only employees can access this database. Please contact the administrator.')

        if 'login' not in values and request.session.get('auth_login'):
            values['login'] = request.session.get('auth_login')

        if not odoo.tools.config['list_db']:
            values['disable_database_manager'] = True

        response = request.render('web.login', values)
        response.headers['X-Frame-Options'] = 'DENY'
        return response



    @http.route('/two_factor_auth', auth='none')
    def show_2fa_form(self, **kw):
        uid = request.session["uid_2fa"]
        
        token = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        auth_token = request.env['two.factor.auth'].sudo().create({
            'user_id': uid,
            'token': token,
        })
        auth_token.sent_auth_code_mail()

        return request.render('custom_auth_signup.two_factor_auth_form2')

    @http.route('/two_factor_auth/verify', type='http', auth='none', website=True)
    def verify_2fa_token(self, **kw):
        uid = request.session["uid_2fa"]
        # Get the submitted token from the form
        token = kw.get('token')

        # Lookup the token in the database
        auth = request.env['two.factor.auth'].sudo().search([
            ('user_id', '=', uid),
            ('token', '=', token),
        ])

        # If the token is valid, redirect to the user's dashboard
        if auth:
            login = request.session['login'], 
            password = request.session['password']
            uid = request.session.authenticate(request.session.db, login, password)
            request.params['login_success'] = True
            return request.redirect("/web")
        else:
            # If the token is invalid, display an error message
            return request.render('custom_auth_signup.two_factor_auth_form2', {
                'error': 'Invalid 2FA token',
            })
