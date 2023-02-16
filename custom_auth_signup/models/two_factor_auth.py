import string
import random
import pprint

from odoo import fields, models
from odoo.tools import plaintext2html, html_sanitize


class TwoFactorAuth(models.Model):
    _name = 'two.factor.auth'

    token = fields.Char()
    user_id = fields.Many2one("res.users")

    def sent_auth_code_mail(self):
        mail_template = self.env.ref('custom_auth_signup.two_factor_auth_mail_template')
        rendered_template = self.env['ir.ui.view']._render_template('custom_auth_signup.two_factor_auth_mail_template', {
            'token': self.token,
            'user': self.user_id,
        })
        print(rendered_template)
        self.env['mail.mail'].create({
            'subject': 'Your 2FA token',
            'body_html': rendered_template,
            'email_to': self.user_id.email_formatted,
            'auto_delete': True,
        }).send()

        return True
