from odoo import api, fields, models

class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    previous_balance = fields.Monetary(
        string="الرصيد السابق",
        store=False,
        compute="_compute_previous_balance",
        currency_field="currency_id",
    )

    @api.depends('debit', 'credit', 'account_id')
    def _compute_previous_balance(self):
        # احضر كل الحركات بهذا الحساب لاحتساب الرصيد السابق
        all_lines = self.env['account.move.line'].search(
            [('account_id', 'in', self.mapped('account_id').ids)],
            order='create_date, id'  # مهم جداً الحفاظ على ترتيب أودو الطبيعي
        )

        balances = {}
        running = {}

        for line in all_lines:
            key = line.account_id.id

            running.setdefault(key, 0)
            balances[line.id] = running[key]

            running[key] += line.debit - line.credit

        for rec in self:
            rec.previous_balance = balances.get(rec.id, 0.0)
