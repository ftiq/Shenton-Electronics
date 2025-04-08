from odoo import api, fields, models

class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    running_balance = fields.Monetary(
        string="الرصيد التراكمي",
        store=False,
        compute="_compute_running_balance",
        currency_field="currency_id",
    )

    running_balance_currency = fields.Monetary(
        string="الرصيد التراكمي بالعملة",
        store=False,
        compute="_compute_running_balance",
        currency_field="currency_id",
    )

    @api.depends('custom_amount', 'amount_currency', 'account_id', 'company_id', 'partner_id', 'currency_id')
    def _compute_running_balance(self):
        if not self:
            return

        account_ids = self.mapped('account_id').ids
        company_ids = self.mapped('company_id').ids
        partner_ids = self.mapped('partner_id').ids
        currency_ids = self.mapped('currency_id').ids

        domain = [
            ('account_id', 'in', account_ids),
            ('company_id', 'in', company_ids),
        ]
        if partner_ids:
            domain.append(('partner_id', 'in', partner_ids))
        if currency_ids:
            domain.append(('currency_id', 'in', currency_ids))

        all_lines = self.env['account.move.line'].search(domain, order='id ASC')

        balance = 0.0
        balance_currency = 0.0
        balance_map = {}
        currency_map = {}

        for line in all_lines:
            balance += line.custom_amount or 0.0
            balance_currency += line.amount_currency or 0.0
            balance_map[line.id] = balance
            currency_map[line.id] = balance_currency

        for rec in self:
            rec.running_balance = balance_map.get(rec.id, 0.0)
            rec.running_balance_currency = currency_map.get(rec.id, 0.0)
