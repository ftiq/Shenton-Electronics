from odoo import api, fields, models


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    # الحقل الأساسي الذي تستخدمه فعليًا
    running_balance = fields.Monetary(
        string="Running Balance",
        store=False,
        compute="_compute_running_balance",
        currency_field="currency_id",
    )

    # الحقل المطلوب فقط لعدم كسر الواجهة، لا يحسب أي شيء
    running_balance_currency = fields.Monetary(
        string="Running Balance (Currency)",
        store=False,
        compute="_noop_compute",
        currency_field="currency_id",
    )

    def _noop_compute(self):
        for rec in self:
            rec.running_balance_currency = 0.0

    def _compute_running_balance(self):
        if not self:
            return

        # اجمع المعرفات المطلوبة
        ids_set = set(self.ids)
        account_ids = list(set(self.mapped('account_id.id')))
        company_ids = list(set(self.mapped('company_id.id')))
        currency_ids = list(set(self.mapped('currency_id.id')))

        self.env.cr.execute("""
            SELECT
                aml.id,
                SUM(aml.custom_amount) OVER (
                    PARTITION BY aml.account_id, aml.company_id, aml.currency_id,
                        CASE WHEN aa.account_type IN ('asset_receivable', 'liability_payable') THEN aml.partner_id ELSE NULL END
                    ORDER BY aml.date, aml.move_id, aml.id
                ) AS running_balance
            FROM account_move_line aml
            JOIN account_account aa ON aml.account_id = aa.id
            WHERE aml.account_id = ANY(%s)
              AND aml.company_id = ANY(%s)
              AND aml.currency_id = ANY(%s)
              AND aml.id = ANY(%s)
        """, (
            account_ids,
            company_ids,
            currency_ids,
            list(ids_set),
        ))

        results = self.env.cr.fetchall()
        balance_map = {r[0]: r[1] or 0.0 for r in results}

        for rec in self:
            rec.running_balance = balance_map.get(rec.id, 0.0)
