# -*- coding: utf-8 -*-
import base64

from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import datetime

from odoo.tools.pdf import merge_pdf


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    @api.model
    def format_date(self, value, _format='%Y-%m-%d'):
        if isinstance(value, str):
            value = datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
        return value.strftime(_format)


class HrPayslipRun(models.Model):
    _inherit = 'hr.payslip.run'

    send_email = fields.Boolean(default=False, string="Envoyer automatiquement les bulletins de paie")

    def _send_email(self, employee, payslip):
        """Fonction pour envoyer un email à l'employé avec son bulletin de paie"""

        email_to = employee.work_email
        if not email_to:
            raise UserError("L'employé %s n'a pas d'adresse e-mail professionnelle." % employee.name)

        name = f"Feuille de paie - {payslip.date_to.strftime('%B').capitalize()} - {employee.company_id.name} - {employee.name}"
        report_payslip_pdf = self.env.ref('om_hr_payroll.action_report_payslip').render_qweb_pdf([payslip.id])[0]
        pdf = base64.b64encode(report_payslip_pdf)
        attachment = self.env['ir.attachment'].create({
            'name': name + ".pdf",
            'res_model': 'hr.payslip',
            'type': 'binary',
            'datas': pdf,
            'store_fname': pdf,
            'mimetype': 'application/x-pdf',
            'res_id': payslip.id,
        })
        mail_template = self.env.ref('payroll_wizards.email_template_payslip')
        smpt = self.env['ir.mail_server'].search([])[0]
        mail_template.send_mail(payslip.id, force_send=True, email_values={
            'subject': name,
            'email_to': email_to,
            'email_from': smpt.smtp_user,
            'auto_delete': True,
            'attachment_ids': [(4, attachment.id)],
        })

    def _send_emails(self):
        """Fonction pour envoyer des emails à tous les employés et au responsable"""
        for payslip in self.slip_ids:
            for employee in payslip.employee_id:
                self._send_email(employee, payslip)
        return

    def _send_emails_admin(self):
        """Envoyer un email au responsable avec tous les bulletins de paie"""
        employee = self.env.user
        email_to = employee.email
        if not email_to:
            raise UserError("L'employé %s n'a pas d'adresse e-mail professionnelle." % employee.name)
        attachment_list = []
        for payslip in self.slip_ids:
            name = f"Feuille de paie - {payslip.date_to.strftime('%B').capitalize()} - {employee.company_id.name}"
            report_payslip_pdf = self.env.ref('om_hr_payroll.action_report_payslip').render_qweb_pdf([payslip.id])[0]
            pdf = base64.b64encode(report_payslip_pdf)
            attachment = self.env['ir.attachment'].create({
                'name': name + ".pdf",
                'res_model': 'hr.payslip',
                'type': 'binary',
                'datas': pdf,
                'store_fname': pdf,
                'mimetype': 'application/x-pdf',
                'res_id': payslip.id,
            })
            attachment_list.append(attachment)

        mail_template = self.env.ref('payroll_wizards.email_template_payslip')
        smpt = self.env['ir.mail_server'].search([])[0]
        mail_template.send_mail(payslip.id, force_send=True, email_values={
            'subject': name,
            'email_to': email_to,
            'email_from': smpt.smtp_user,
            'auto_delete': True,
            'attachment_ids': [(4, attachment.id) for attachment in attachment_list],
        })

    def action_send_payslips(self):
        self._send_emails()
        self._send_emails_admin2()


class HrPayslipEmployees(models.TransientModel):
    _inherit = 'hr.payslip.employees'

    # employee_ids = fields.Many2many('hr.employee', 'hr_employee_group_rel', 'payslip_id', 'employee_id', 'Employees')
    payslip_run_id = fields.Many2one('hr.payslip.run', string='Payroll Batch', required=False,
                                     default=lambda self: self._default_payslip_run_id())
    date_start = fields.Date(string="Date de début", default=lambda self: self._get_default_date_start())
    date_end = fields.Date(string="Date de fin", default=lambda self: self._get_default_date_end())
    credit_note = fields.Boolean(string='Credit Note', readonly=True,
                                 default=lambda self: self._get_default_credit_note(),
                                 help="If its checked, indicates that all payslips generated from here are refund payslips.")

    @api.model
    def _default_payslip_run_id(self):
        return self.env.context.get('payslip_run_id')

    @api.model
    def _get_default_date_start(self):
        payslip_run_id = self.env.context.get('payslip_run_id')
        if payslip_run_id:
            [run_data] = self.env['hr.payslip.run'].browse(payslip_run_id).read(['date_start'])
        return run_data.get('date_start')

    @api.model
    def _get_default_date_end(self):
        payslip_run_id = self.env.context.get('payslip_run_id')
        if payslip_run_id:
            [run_data] = self.env['hr.payslip.run'].browse(payslip_run_id).read(['date_end'])
        return run_data.get('date_end')

    @api.model
    def _get_default_credit_note(self):
        payslip_run_id = self.env.context.get('payslip_run_id')
        if payslip_run_id:
            [run_data] = self.env['hr.payslip.run'].browse(payslip_run_id).read(['credit_note', ])
            return run_data.get('credit_note')

    def select_all_employees(self):
        self.write({"employee_ids": self.env['hr.employee'].search([])})
        return {
            'name': "Génération automatique des bulletins de paie",
            'type': 'ir.actions.act_window',
            'res_model': 'hr.payslip.employees',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }

    def compute_sheet(self):
        payslips = self.env['hr.payslip']
        [data] = self.read()
        from_date = self.date_start
        to_date = self.date_end
        credit_note = self.credit_note
        payslip_run_id = self.payslip_run_id

        if not data['employee_ids']:
            raise UserError(_("You must select employee(s) to generate payslip(s)."))
        for employee in self.env['hr.employee'].browse(data['employee_ids']):
            slip_data = self.env['hr.payslip'].onchange_employee_id(from_date, to_date, employee.id,
                                                                    contract_id=False)
            res = {
                'employee_id': employee.id,
                'name': slip_data['value'].get('name'),
                'struct_id': slip_data['value'].get('struct_id'),
                'contract_id': slip_data['value'].get('contract_id'),
                'payslip_run_id': payslip_run_id.id,
                'input_line_ids': [(0, 0, x) for x in slip_data['value'].get('input_line_ids')],
                'worked_days_line_ids': [(0, 0, x) for x in slip_data['value'].get('worked_days_line_ids')],
                'date_from': from_date,
                'date_to': to_date,
                'credit_note': credit_note,
                'company_id': employee.company_id.id,
            }
            payslips += self.env['hr.payslip'].create(res)
        payslips.compute_sheet()
        payslip_run_name = f"Bulletins de paye - Mois {from_date.strftime('%B').capitalize()} - {employee.company_id.name}"
        payslip_run_id.write({"name": payslip_run_name})
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'hr.payslip.run',
            'res_id': payslip_run_id.id,
            'view_mode': 'form',
            'target': 'parent',
            'flags': {
                'form': {
                    'action_buttons': True,
                    'options': {'mode': 'edit'}
                }
            },
        }
