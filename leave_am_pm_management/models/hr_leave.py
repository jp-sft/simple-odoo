from odoo import models, fields, api
from datetime import datetime


class HrLeave(models.Model):
    _inherit = "hr.leave"

    request_date_from_am_pm = fields.Selection(
        [
            ("am", "AM"),
            ("pm", "PM"),
        ],
        string="Start AM/PM",
        default="am",
    )

    request_date_to_am_pm = fields.Selection(
        [
            ("am", "AM"),
            ("pm", "PM"),
        ],
        string="End AM/PM",
        default="pm",
    )

    @api.onchange("request_date_from_am_pm", "request_date_to_am_pm")
    def _onchange_am_pm(self):
        # Mettre à jour date_from et date_to selon AM ou PM
        if self.request_date_from and self.request_date_from_am_pm:
            self.date_from = self._adjust_date_am_pm(
                self.request_date_from, self.request_date_from_am_pm
            )
        if self.request_date_to and self.request_date_to_am_pm:
            self.date_to = self._adjust_date_am_pm(
                self.request_date_to, self.request_date_to_am_pm
            )

    def _adjust_date_am_pm(self, date, am_pm):
        if isinstance(date, datetime):
            # Si la date est déjà un datetime, nous pouvons ajuster l'heure
            if am_pm == "am":
                return date.replace(hour=8, minute=0)  # Exemple d'heure pour AM
            else:
                return date.replace(hour=13, minute=0)  # Exemple d'heure pour PM
        else:
            # Si la date est un objet 'date', nous la convertissons en 'datetime'
            date_dt = datetime.combine(date, datetime.min.time())
            if am_pm == "am":
                return date_dt.replace(hour=8, minute=0)  # AM
            else:
                return date_dt.replace(hour=13, minute=0)  # PM
