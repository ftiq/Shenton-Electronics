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

    def _compute_running_balance(self):
        if not self:
            return

        # كل الحسابات الظاهرة الآن في الصفحة
        line_ids = self.ids
        account_ids = list(set(self.mapped('account_id.id')))
        company_ids = list(set(self.mapped('company_id.id')))

        # نأتي بجميع السطور المطابقة من قاعدة البيانات (بدون domain)
        query = """
            SELECT
                aml.id,
                SUM(aml.custom_amount) OVER (
                    PARTITION BY aml.account_id, aml.company_id
                    ORDER BY aml.date, aml.id
                    ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
                ) AS running_balance,
                SUM(aml.amount_currency) OVER (
                    PARTITION BY aml.account_id, aml.company_id
                    ORDER BY aml.date, aml.id
                    ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
                ) AS running_balance_currency
            FROM account_move_line aml
            WHERE aml.account_id = ANY(%s) AND aml.company_id = ANY(%s)
              AND aml.custom_amount IS NOT NULL
        """
        self.env.cr.execute(query, (account_ids, company_ids))
        results = self.env.cr.fetchall()

        # نحفظ النتائج في dict حسب ID
        balance_map = {}
        currency_map = {}
        for rec_id, balance, balance_cur in results:
            balance_map[rec_id] = balance or 0.0
            currency_map[rec_id] = balance_cur or 0.0

        # نعيّن فقط للسجلات الظاهرة حالياً
        for rec in self:
            rec.running_balance = balance_map.get(rec.id, 0.0)
            rec.running_balance_currency = currency_map.get(rec.id, 0.0)
