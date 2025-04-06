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

    @api.depends('custom_amount', 'amount_currency', 'account_id', 'company_id')
    def _compute_running_balance(self):
        if not self:
            return

        # الحسابات المعروضة الآن
        account_ids = self.mapped('account_id').ids
        company_ids = self.mapped('company_id').ids

        # استرجاع كل السجلات الخاصة بهذه الحسابات والشركات
        all_lines = self.env['account.move.line'].search([
            ('account_id', 'in', account_ids),
            ('company_id', 'in', company_ids),
        ], order='id ASC')  # مهم أن يكون الترتيب تصاعدي

        # تحضير التراكم
        balance = 0.0
        balance_currency = 0.0
        balance_map = {}
        balance_currency_map = {}

        for line in all_lines:
            balance += line.custom_amount or 0.0
            balance_currency += line.amount_currency or 0.0
            balance_map[line.id] = balance
            balance_currency_map[line.id] = balance_currency

        # إظهار الرصيد فقط للسجلات المعروضة
        for line in self:
            line.running_balance = balance_map.get(line.id, 0.0)
            line.running_balance_currency = balance_currency_map.get(line.id, 0.0)
