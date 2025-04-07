from odoo import models, fields, api

class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    previous_balance = fields.Monetary(
        string="الرصيد السابق",
        compute='_compute_previous_balance',
        store=False,
        currency_field='currency_id',
    )

    @api.depends('debit', 'credit', 'account_id')
    def _compute_previous_balance(self):
        lines = self.search(
            [('account_id', 'in', self.mapped('account_id').ids)],
            order="create_date, id"
        )

        balance_dict = {}
        cumulative = {}

        for line in lines:
            acc_id = line.account_id.id
            if acc_id not in cumulative:
                cumulative[acc_id] = 0.0
            balance_dict[line.id] = cumulative[acc_id]
            cumulative[acc_id] += line.debit - line.credit

        for rec in self:
            rec.previous_balance = balance_dict.get(rec.id, 0.0)
