from odoo import models, fields, api


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    running_balance = fields.Monetary(
        string="الرصيد التراكمي",
        store=False,
        compute="_compute_running_balance",
        currency_field="currency_id"
    )

    running_balance_currency = fields.Monetary(
        string="الرصيد التراكمي بالعملة",
        store=False,
        compute="_compute_running_balance",
        currency_field="currency_id"
    )

    @api.depends('custom_amount', 'amount_currency', 'account_id', 'company_id', 'currency_id')
    def _compute_running_balance(self):
        # جهز الحسابات والشركات المطلوبة
        account_ids = self.mapped('account_id').ids
        company_ids = self.mapped('company_id').ids

        # اجلب كل السطور المرتبطة، مرتبة بـ id ASC (الوحيد الموثوق لترتيب دائم)
        domain = [
            ('account_id', 'in', account_ids),
            ('company_id', 'in', company_ids)
        ]
        all_lines = self.env['account.move.line'].search(domain, order='id ASC')

        # احسب الرصيد التراكمي
        balance = 0.0
        balance_currency = 0.0
        balance_map = {}
        currency_map = {}

        for line in all_lines:
            balance += line.custom_amount or 0.0
            balance_currency += line.amount_currency or 0.0
            balance_map[line.id] = balance
            currency_map[line.id] = balance_currency

        # خصص الرصيد فقط للسجلات المطلوبة الآن
        for rec in self:
            rec.running_balance = balance_map.get(rec.id, 0.0)
            rec.running_balance_currency = currency_map.get(rec.id, 0.0)
