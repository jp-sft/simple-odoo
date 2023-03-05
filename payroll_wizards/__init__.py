
from odoo import api, SUPERUSER_ID
from . import models


# enregistrer de fonction en tant que point d'entrée pour l'exécution automatique au démarrage
def _auto_create_payslip_and_send(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    model = env['ir.model'].search([("model", "=", "hr.payslip.employees")])
    assert len(model) > 0
    model = model[0]

    env['ir.cron'].create({
        'name': 'Génération automatique des bulletins de salaire',
        'interval_type': 'months',
        'numbercall': -1,
        # 'nextcall': next_month,
        'model_id': model.id,
        'code': "model.do_automation()",
        'priority': 1,
    })
