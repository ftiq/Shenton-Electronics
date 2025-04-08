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

        Account = self.env['account.account']
        MoveLine = self.env['account.move.line']

        # تجميع الحسابات المرتبطة بكل سجل
        account_ids = self.mapped('account_id').ids
        company_ids = self.mapped('company_id').ids

        # جلب نوع الحساب
        account_type_map = {
            acc.id: acc.account_type
            for acc in Account.browse(account_ids)
        }

        # إعداد الرصيد
        balance_map = {}
        currency_balance_map = {}

        # جلب كافة السطور المطلوبة للحسابات المعنية
        all_lines = MoveLine.search([
            ('account_id', 'in', account_ids),
            ('company_id', 'in', company_ids),
        ], order='id ASC')

        # المتغيرات المؤقتة
        grouped_balance = {}
        grouped_currency_balance = {}

        for line in all_lines:
            acc_type = account_type_map.get(line.account_id.id)
            key = None

            # تحديد المفتاح التجميعي بحسب نوع الحساب
            if acc_type in ['receivable', 'payable']:
                key = (line.account_id.id, line.company_id.id, line.partner_id.id)
            else:
                key = (line.account_id.id, line.company_id.id)

            grouped_balance.setdefault(key, 0.0)
            grouped_currency_balance.setdefault(key, 0.0)

            grouped_balance[key] += line.custom_amount or 0.0
            grouped_currency_balance[key] += line.amount_currency or 0.0

            balance_map[line.id] = grouped_balance[key]
            currency_balance_map[line.id] = grouped_currency_balance[key]

        # تعيين القيم على السجلات المطلوبة
        for rec in self:
            rec.running_balance = balance_map.get(rec.id, 0.0)
            rec.running_balance_currency = currency_balance_map.get(rec.id, 0.0)
