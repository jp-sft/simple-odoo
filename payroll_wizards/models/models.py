# -*- coding: utf-8 -*-
import base64
import calendar

from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import datetime, timedelta, date

from odoo.tools import image_data_uri
from odoo.tools.pdf import merge_pdf


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    @api.model
    def format_date(self, value, _format='%Y-%m-%d'):
        if isinstance(value, str):
            value = datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
        return value.strftime(_format)


# class EmployeeForEmail(models.Model):
#     _name = "hr.employee.email"
#
#     employee_id = fields.Many2one("hr.employee")
#     payslip_id = fields.Many2one('hr.payslip')
#     contract_period = fields.Char(default='_default_contract_period')
#     work_month = fields.Char(default='_default_work_month')
#     work_days = fields.Char(default='_default_work_days')

def compute_email_value(payslip_id):
    # Calculer le nombre de jours de travail
    work_days = 0.0
    for line in payslip_id.worked_days_line_ids:
        work_days += line.number_of_days
    work_days = work_days

    if len(payslip_id.contract_id) > 0:
        contract_start = (fields.Date.from_string(payslip_id.contract_id.date_start).strftime('%d/%m/%Y')
                          if payslip_id.contract_id.date_start else '--')
        contract_end = (fields.Date.from_string(payslip_id.contract_id.date_end).strftime('%d/%m/%Y')
                        if payslip_id.contract_id.date_end else '--')
        contract_period = contract_start + ' - ' + contract_end
    else:
        contract_period = ""

    work_month = payslip_id.date_from.strftime('%B %Y')

    return {
        "work_days": work_days,
        "contract_period": contract_period,
        "work_month": work_month
    }


class HrPayslipRun(models.Model):
    _inherit = 'hr.payslip.run'

    def _send_email(self, employee, payslip, vals, smpt, logo_base64):
        """Fonction pour envoyer un email à l'employé avec son bulletin de paie"""
        email_to = employee.work_email
        if not email_to:
            raise UserError("L'employé %s n'a pas d'adresse e-mail professionnelle." % employee.name)

        name = f"Feuille de paie - {payslip.date_to.strftime('%B').capitalize()} - {employee.company_id.name} - {employee.name}"
        report_payslip_pdf = self.env.ref('om_hr_payroll.action_report_payslip').render_qweb_pdf([payslip.id])[0]
        pdf = base64.b64encode(report_payslip_pdf)
        attachment = self.env['ir.attachment'].create(
            {'name': f"{name}.pdf", 'res_model': 'hr.payslip', 'type': 'binary', 'datas': pdf, 'store_fname': pdf,
             'mimetype': 'application/x-pdf', 'res_id': payslip.id})

        mail_template = self.env.ref('payroll_wizards.email_template_payslip')
        body_html = f"""
                <div>
                        <p>
                          Chère {employee.name},
                        </p>
                        <p>
                          Veuillez trouver ci-joint une copie de fiche de paie relative au :
                        </p>
                        <ul>
                          <li>Salarié: {employee.name}</li>
                          <li>CIN: {employee.identification_id}</li>
                          <li>Période du contrat: {vals['contract_period']}</li>
                          <li>Mois de travail: {vals['work_month']}</li>
                          <li>Nombre de jours de travail: {vals['work_days']}</li>
                          <li>Société: {employee.company_id.name}</li>
                        </ul>
                        <p>
                          Nous restons à votre disposition pour des amples informations.
                        </p>
                        <div>
                          <p>Cordialement,</p>
                          <img src="data:image/png;base64,{logo_base64}" width="auto" height="50"/>
                          <p>
                            Nom de société: {employee.name}<br/>
                            MF: {employee.identification_id}<br/>
                            Registre de commerce: {employee.company_id.company_registry}<br/>
                            Adresse: {employee.company_id.street}<br/>
                          </p>
                        </div>
                      </div>
                """
        mail_template.send_mail(payslip.id, force_send=True, email_values={
            'subject': name,
            'email_to': email_to,
            'email_from': smpt.smtp_user,
            'auto_delete': True,
            'attachment_ids': [(4, attachment.id)],
            'body_html': body_html
        })
        return attachment

    def _send_emails(self, slip_ids=None):
        """Fonction pour envoyer des emails à tous les employés et au responsable"""
        smpt = self.env['ir.mail_server'].search([])[0]
        logo_base64 = base64.b64encode(self.env.user.company_id.logo).decode('utf-8')
        attachments = []
        body_html = f"""
            <div>
                    <p>
                      Chère {self.env.user.name},
                    </p>
                    <p>
                      Veuillez trouver ci-joint des copies de fiche de paie des employées :
                    </p>
                    <ul>
        """
        slip_ids = slip_ids or self.slip_ids
        date = ''
        for payslip in slip_ids:
            if not payslip:
                continue
            for employee in payslip.employee_id:
                vals = compute_email_value(payslip)
                att = self._send_email(employee, payslip, vals, smpt, logo_base64)
                attachments.append(att)
                body_html += f"""
                    <li><ul>
                      <li>Salarié: {employee.name}</li>
                      <li>CIN: {employee.identification_id}</li>
                      <li>Période du contrat: {vals['contract_period']}</li>
                      <li>Mois de travail: {vals['work_month']}</li>
                      <li>Nombre de jours de travail: {vals['work_days']}</li>
                      <li>Société: {employee.company_id.name}</li>
                    </ul></li>
                """
            body_html += f"""
            </ul>
            <div>
              <p>Cordialement,</p>
              <img src="data:image/png;base64,{logo_base64}" width="auto" height="50"/>
              <p>
                Nom de société: {self.env.user.company_id.name}<br/>
                Adresse: {self.env.user.company_id.street}<br/>
              </p>
            </div>
          </div>
            """
            date = payslip.date_to.strftime('%B').capitalize()
        else:
            name = f"Feuille de paie - {date} - {self.env.user.company_id.name} - Tout Les Employées"

            # Pour l'admin
            mail_template = self.env.ref('payroll_wizards.email_template_payslip')
            mail_template.send_mail(payslip.id, force_send=True, email_values={
                'subject': name,
                'email_to': self.env.user.email,
                'email_from': smpt.smtp_user,
                'auto_delete': True,
                'attachment_ids': [(4, attachment.id) for attachment in attachments],
                'body_html': body_html
            })

    def action_send_payslips(self, payslips=None):
        self._send_emails(slip_ids=payslips)


class HrPayslipEmployees(models.TransientModel):
    _inherit = 'hr.payslip.employees'

    employee_ids = fields.Many2many('hr.employee', 'hr_employee_group_rel', 'payslip_id', 'employee_id', 'Employees')
    payslip_run_id = fields.Many2one('hr.payslip.run', string='Payroll Batch', required=False,
                                     default=lambda self: self._default_payslip_run_id())
    date_start = fields.Date(string="Date de début", default=lambda self: self._get_default_date_start())
    date_end = fields.Date(string="Date de fin", default=lambda self: self._get_default_date_end())
    credit_note = fields.Boolean(string='Credit Note', readonly=True,
                                 default=lambda self: self._get_default_credit_note(),
                                 help="If its checked, "
                                      "indicates that all payslips generated from here are refund payslips.")

    @api.model
    def _default_employee_ids(self):
        return self.env["hr.employee"].search([])

    @api.model
    def _default_payslip_run_id(self):
        return self.env.context.get('payslip_run_id')

    @api.model
    def _get_default_date_start(self):
        payslip_run_id = self.env.context.get('payslip_run_id')
        if payslip_run_id:
            [run_data] = self.env['hr.payslip.run'].browse(payslip_run_id).read(['date_start'])
            return run_data.get('date_start')
        today = date.today()
        return date(today.year, today.month, 1)

    @api.model
    def _get_default_date_end(self):
        payslip_run_id = self.env.context.get('payslip_run_id')
        if payslip_run_id:
            [run_data] = self.env['hr.payslip.run'].browse(payslip_run_id).read(['date_end'])
            return run_data.get('date_end')
        today = date.today()
        return date(today.year, today.month, calendar.monthrange(today.year, today.month)[1])

    @api.model
    def _get_default_credit_note(self):
        payslip_run_id = self.env.context.get('payslip_run_id')
        if payslip_run_id:
            [run_data] = self.env['hr.payslip.run'].browse(payslip_run_id).read(['credit_note', ])
            return run_data.get('credit_note')
        return False

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

    @api.model
    def do_automation(self, **kwargs):
        today = datetime.today().replace(day=1)
        data_start = date(today.year, today.month, 1)
        date_end = date(today.year, today.month, calendar.monthrange(today.year, today.month)[1])

        # Creation du lot
        credit_note = kwargs.get('credit_note', False)
        payslip_run_name = f"Bulletins de paye - Mois {today.strftime('%B').capitalize()} - {self.env.company.name}"
        batch_vals = {
            'name': payslip_run_name,
            'state': 'draft',
            "date_start": data_start,
            "date_end": date_end,
            "credit_note": credit_note
        }
        payslip_run_id = self.env['hr.payslip.run'].create(batch_vals)
        payslip_run_id, payslips = self.create_slips(
            credit_note=credit_note,
            employee_ids=self.env['hr.employee'].search([]).ids,
            from_date=data_start,
            payslip_run_id=payslip_run_id,
            to_date=date_end
        )
        payslip_run_id.action_send_payslips(payslips=payslips)

    def compute_sheet(self):
        employee_ids = self.read()[0]['employee_ids']
        payslip_run_id = self.payslip_run_id or self.env['hr.payslip.run'].create({
            "name": f"Bulletins de paye",
            'state': 'draft'
        })
        from_date = self.date_start or payslip_run_id.date_start
        to_date = self.date_end or payslip_run_id.date_end
        credit_note = self.credit_note or payslip_run_id.credit_note

        if not employee_ids:
            raise UserError(_("You must select employee(s) to generate payslip(s)."))

        payslip_run_id, payslips = self.create_slips(credit_note, employee_ids, from_date, payslip_run_id, to_date)

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

    @api.model
    def create_slips(self, credit_note, employee_ids, from_date, payslip_run_id, to_date):
        payslips = self.env['hr.payslip']
        for employee in self.env['hr.employee'].browse(employee_ids):
            slip_data = self.env['hr.payslip'].onchange_employee_id(
                from_date,
                to_date,
                employee.id,
                contract_id=False
            )
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

        payslip_run_name = f"Bulletins de paye - Mois {from_date.strftime('%B').capitalize()} - {self.env.company.name}"
        payslip_run_id.write({"name": payslip_run_name})
        return payslip_run_id, payslips
