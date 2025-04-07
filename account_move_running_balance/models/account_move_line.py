from odoo import api, fields, models


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    running_balance = fields.Monetary(
        string="Running Balance",
        store=False,
        compute="_compute_running_balance",
        currency_field="currency_id",
    )

    def _compute_running_balance(self):
        if not self:
            return

        # اجمع كل السطور الحالية
        ids_set = set(self.ids)
        lines_map = {line.id: line for line in self}

        # اجمع الحسابات والشركات والعملات
        all_account_ids = list(set(self.mapped('account_id.id')))
        all_company_ids = list(set(self.mapped('company_id.id')))
        all_currency_ids = list(set(self.mapped('currency_id.id')))

        # SQL لحساب الرصيد التراكمي بحسب ترتيب أودو الرسمي
        self.env.cr.execute("""
            SELECT
                aml.id,
                aml.account_id,
                aml.company_id,
                aml.currency_id,
                aml.partner_id,
                aml.custom_amount,
                aml.amount_currency,
                SUM(aml.custom_amount) OVER (
                    PARTITION BY aml.account_id, aml.company_id, aml.currency_id,
                        CASE WHEN aa.account_type IN ('asset_receivable', 'liability_payable') THEN aml.partner_id ELSE NULL END
                    ORDER BY aml.date, aml.move_id, aml.id
                ) AS running_balance,
                SUM(aml.amount_currency) OVER (
                    PARTITION BY aml.account_id, aml.company_id, aml.currency_id,
                        CASE WHEN aa.account_type IN ('asset_receivable', 'liability_payable') THEN aml.partner_id ELSE NULL END
                    ORDER BY aml.date, aml.move_id, aml.id
                ) AS running_balance_currency
            FROM account_move_line aml
            JOIN account_account aa ON aml.account_id = aa.id
            WHERE aml.account_id = ANY(%s)
              AND aml.company_id = ANY(%s)
              AND aml.currency_id = ANY(%s)
              AND aml.id = ANY(%s)
        """, (
            all_account_ids,
            all_company_ids,
            all_currency_ids,
            list(ids_set),
        ))

        result = self.env.cr.fetchall()
        balance_map = {r[0]: (r[7] or 0.0) for r in result}

        # نعيّن القيمة فقط للسجلات الظاهرة حالياً
        for line in self:
            line.running_balance = balance_map.get(line.id, 0.0)
