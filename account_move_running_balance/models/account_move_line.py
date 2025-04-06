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

        # نأخذ فقط سجل واحد من self لتحديد الحساب والشركة
        sample = self[0]

        account_id = sample.account_id.id
        company_id = sample.company_id.id

        # نأتي بجميع السجلات المرتبطة بالحساب (حتى لو لم تكن ظاهرة في الشاشة)
        all_lines = self.env['account.move.line'].search([
            ('account_id', '=', account_id),
            ('company_id', '=', company_id),
        ], order='id')

        # نحسب التراكم الكامل
        running_total = 0.0
        currency_total = 0.0

        balance_map = {}
        currency_map = {}

        for line in all_lines:
            running_total += line.custom_amount or 0.0
            currency_total += line.amount_currency or 0.0
            balance_map[line.id] = running_total
            currency_map[line.id] = currency_total

        # نعيّن فقط للسجلات الظاهرة
        for line in self:
            line.running_balance = balance_map.get(line.id, 0.0)
            line.running_balance_currency = currency_map.get(line.id, 0.0)
