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
        Account = self.env['account.account']
        grouped_lines = {}

        # جلب جميع السطور المطلوبة
        all_lines = self.env['account.move.line'].search([
            ('account_id', 'in', self.mapped('account_id').ids),
            ('company_id', 'in', self.mapped('company_id').ids),
        ], order='id ASC')

        # التجميع حسب (partner_id + account_id) فقط إذا كان نوع الحساب يتطلب ذلك
        for line in all_lines:
            account_type = line.account_id.account_type
            key = (line.account_id.id, line.company_id.id)

            if account_type in ['receivable', 'payable']:
                key = (line.partner_id.id, line.account_id.id, line.company_id.id)

            if key not in grouped_lines:
                grouped_lines[key] = []

            grouped_lines[key].append(line)

        # حساب الرصيد التراكمي
        balance_map = {}
        currency_map = {}

        for group in grouped_lines.values():
            balance = 0.0
            balance_currency = 0.0
            for line in group:
                balance += line.custom_amount or 0.0
                balance_currency += line.amount_currency or 0.0
                balance_map[line.id] = balance
                currency_map[line.id] = balance_currency

        # تعيين النتائج للسجلات الحالية فقط
        for rec in self:
            rec.running_balance = balance_map.get(rec.id, 0.0)
            rec.running_balance_currency = currency_map.get(rec.id, 0.0)
