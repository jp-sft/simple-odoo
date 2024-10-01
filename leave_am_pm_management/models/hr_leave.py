import logging
from odoo import models, fields, api
from datetime import datetime, time

_logger = logging.getLogger(__name__)


class HrLeave(models.Model):
    _inherit = "hr.leave"

    date_from = fields.Datetime(
        "Start Date",
        readonly=True,
        index=True,
        copy=False,
        required=True,
        default=fields.Datetime.now,
        states={"draft": [("readonly", True)], "confirm": [("readonly", False)]},
        tracking=True,
        store=True,
    )
    date_to = fields.Datetime(
        "End Date",
        readonly=True,
        copy=False,
        required=True,
        default=fields.Datetime.now,
        states={"draft": [("readonly", True)], "confirm": [("readonly", False)]},
        tracking=True,
        store=True,
    )
    request_date_from_period = fields.Selection(
        [("am", "AM"), ("pm", "PM")],
        string="Date Period Start",
        default="am",
    )
    request_date_to_period = fields.Selection(
        [("am", "AM"), ("pm", "PM")],
        string="Date Period To",
        default="pm",
    )
    hour_from = fields.Selection(
        [(str(x), str(x)) for x in range(12)],
        string="Hour From",
        default="0",
    )
    hour_to = fields.Selection(
        [(str(x), str(x)) for x in range(12)],
        string="Hour To",
        default="11",
    )

    @api.onchange(
        "request_date_from_period",
        "request_date_to_period",
        # "request_hour_from",
        # "request_hour_to",
        "request_date_from",
        "request_date_to",
        "employee_id",
        "hour_to",
        "hour_from",
    )
    def _onchange_request_parameters(self):
        if self.hour_from and self.hour_to:
            # Convert request_date_from and request_date_to to datetime objects
            date_from = datetime.combine(self.request_date_from, time(0, 0))
            date_to = datetime.combine(self.request_date_to, time(0, 0))

            # Adjust the start time of request_date_from with request_hour_from
            hour_from = int(self.hour_from)
            if self.request_date_from_period == "pm" and hour_from < 12:
                hour_from += 12
            request_hour_from = str(hour_from)

            # Fetch start work hour if needed
            start_work_hour = 6
            date_from = date_from.replace(hour=max(int(start_work_hour), hour_from))

            # Adjust the end time of request_date_to with request_hour_to
            hour_to = int(self.hour_to)
            if self.request_date_to_period == "pm" and hour_to < 12:
                hour_to += 12
            request_hour_to = str(hour_to)

            # Fetch end work hour if needed
            end_work_hour = 17
            date_to = date_to.replace(hour=min(int(end_work_hour), hour_to))

            self.update(
                {
                    "date_from": date_from,
                    "date_to": date_to,
                    "request_hour_from": request_hour_from,
                    "request_hour_to": request_hour_to,
                }
            )
        else:
            date_from = self.request_date_from
            date_to = self.request_date_to
            self.update(
                {
                    "date_from": date_from,
                    "date_to": date_to,
                }
            )

        self._onchange_leave_dates()
