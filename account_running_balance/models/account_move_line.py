from odoo import models, fields, api

class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    running_balance_line = fields.Monetary(
        string='الرصيد التراكمي',
        compute='_compute_running_balance_line',
        store=False,
        currency_field='currency_id'
    )

    @api.depends('move_id', 'account_id', 'date')
    def _compute_running_balance_line(self):
        for record in self:
            domain = [
                ('account_id', '=', record.account_id.id),
                ('company_id', '=', record.company_id.id),
            ]
            all_lines = self.env['account.move.line'].search(domain, order='id')

            running_total = 0.0
            for line in all_lines:
                custom_amount = line.debit - line.credit
                running_total += custom_amount
                if line.id == record.id:
                    record.running_balance_line = running_total
                    break
