odoo.define('payroll_wizards.hr_payslip_run_tree', function (require) {
    "use strict";

    var core = require('web.core');
    var ListController = require('web.ListController');

    var _t = core._t;

    ListController.include({
        renderButtons: function () {
            this._super.apply(this, arguments);
            if (this.$buttons) {
                if(this.modelName == "hr.payslip.run") {
                    this.$buttons.on('click', '.o_list_button_add', this.on_click_create_button.bind(this));
                }
            }
        },
        on_click_create_button: function () {
            var self = this;
            // var batch_vals = {'name': 'Bulletins de paye - Mois <mois> - <société>', 'state': 'draft'};
            // self._rpc({
            //     model: 'hr.payslip.run',
            //     method: 'create',
            //     args: [batch_vals],
            // }).then(function (result) {
                self.do_action({
                    type: 'ir.actions.act_window',
                    name: 'Génération automatique des bulletins de paie',
                    res_model: 'hr.payslip.employees',
                    views: [[false, 'form']],
                    target: 'new',
                    // context: {'payslip_run_id': result},
                });
            // })
        }
    })
})
