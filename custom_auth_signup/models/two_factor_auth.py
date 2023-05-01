import logging

from odoo import fields, models
import odoo
import werkzeug

from odoo import http, _
from odoo.addons.web.controllers.main import Home, ensure_db, SIGN_UP_REQUEST_PARAMS
from odoo.http import request

_logger = logging.getLogger(__name__)
class TwoFactorAuth(models.Model):
    _name = 'two.factor.auth'

    token = fields.Char()
    user_id = fields.Many2one("res.users")
    ip = fields.Char()

    def sent_auth_code_mail(self):
        template = self.env.ref('custom_auth_signup.two_factor_auth_mail_template')
        ip_address = request.httprequest.environ['REMOTE_ADDR']
        rendered_template = template.render({
            'token': self.token,
            'user': self.user_id,
            'ip':ip_address,
        }, engine="ir.qweb")
        smpt = self.env['ir.mail_server'].search([])[0]
        print(smpt.smtp_user)
        self.env['mail.mail'].create({
            'subject': 'Code sécurité - SMARTPAY APP',
            'body_html': rendered_template,
            'email_to': self.user_id.email_formatted,
            'email_from': smpt.smtp_user,
            'auto_delete': True,
        }).send()

        return True
