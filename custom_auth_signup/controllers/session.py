"""
Author    : Jessy Pango
Github    : @jp-sft
Date      : 30/04/2023
Purpose   : Accepter le token de l'utilisateur et le sauvegarder dans la session
"""
import logging

import odoo.exceptions
from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class TokenSession(http.Controller):
    @http.route('/web/session/authenticate/token', type='json', auth="none")
    def authenticate_with_token(self, db, login, password, token, base_location=None):
        request.session['token'] = token
        request.session['check_token'] = True
        _logger.debug("Enregistrement du token dans la session.")
        request.session.authenticate(db, login, password)
        return request.env['ir.http'].session_info()

    @http.route('/web/session/authenticate2', type='json', auth="none")
    def authenticate(self, db, login, password, base_location=None):
        request.session['check_token'] = False
        request.session.authenticate(db, login, password)
        return request.env['ir.http'].session_info()