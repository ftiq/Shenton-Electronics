from odoo import models, fields, api

class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    previous_balance = fields.Monetary(
        string='الرصيد السابق',
        compute='_compute_previous_balance',
        currency_field='currency_id',
        store=False,
    )

    @api.depends('debit', 'credit', 'account_id')
    def _compute_previous_balance(self):
        all_lines = self.env['account.move.line'].search(
            [('account_id', 'in', self.mapped('account_id').ids)],
            order='create_date, id'
        )
        balance_dict = {}
        running_balance = {}

        for line in all_lines:
            acc_id = line.account_id.id
            running_balance.setdefault(acc_id, 0)
            balance_dict[line.id] = running_balance[acc_id]
            running_balance[acc_id] += line.debit - line.credit

        for rec in self:
            rec.previous_balance = balance_dict.get(rec.id, 0.0)
