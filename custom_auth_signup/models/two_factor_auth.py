import logging

from odoo import fields, models

_logger = logging.getLogger(__name__)
class TwoFactorAuth(models.Model):
    _name = 'two.factor.auth'

    token = fields.Char()
    user_id = fields.Many2one("res.users")

    def sent_auth_code_mail(self):
        template = self.env.ref('custom_auth_signup.two_factor_auth_mail_template')
        rendered_template = template.render({
            'token': self.token,
            'user': self.user_id,
        }, engine="ir.qweb")
        smpt = self.env['ir.mail_server'].search([])[0]
        print(smpt.smtp_user)
        self.env['mail.mail'].create({
            'subject': 'Your 2FA token',
            'body_html': rendered_template,
            'email_to': self.user_id.email_formatted,
            'email_from': smpt.smtp_user,
            'auto_delete': True,
        }).send()

        return True
