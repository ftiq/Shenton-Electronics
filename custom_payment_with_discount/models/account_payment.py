from odoo import models, fields, api, _

class AccountPayment(models.Model):
    _inherit = 'account.payment'

    cash_discount = fields.Monetary(
        string="Cash Discount",
        currency_field='currency_id',
        help="The cash discount to apply for this payment."
    )
    discount_account_id = fields.Many2one(
        'account.account',
        string="Discount Account",
        help="The account used to record cash discounts."
    )

    def action_post(self):
        super(AccountPayment, self).action_post()

        for payment in self:
            move = payment.move_id
            if not move:
                raise ValueError(_("No journal entry found for the payment."))

            memo = payment.memo or 'Payment'

            if move.state == 'posted':
                move.button_draft()

            # تعديل أسماء الأسطر الفارغة
            for line in move.line_ids:
                if not line.name or line.name == '/':
                    line.name = memo

            # ✳️ تعديل فقط السطرين المتعلقين بالخصم إن وُجدا
            if payment.cash_discount > 0 and payment.discount_account_id:

                # تعديل سطر "Cash Discount"
                discount_line = move.line_ids.filtered(
                    lambda l: l.name == 'Cash Discount' and l.account_id == payment.discount_account_id
                )
                if discount_line:
                    discount_line.write({
                        'debit': payment.cash_discount if payment.payment_type == 'inbound' else 0.0,
                        'credit': payment.cash_discount if payment.payment_type == 'outbound' else 0.0,
                    })

                # تعديل سطر "Receivable Adjustment for Discount"
                receivable_line = move.line_ids.filtered(
                    lambda l: l.name == 'Receivable Adjustment for Discount' and l.account_id == payment.destination_account_id
                )
                if receivable_line:
                    receivable_line.write({
                        'debit': 0.0 if payment.payment_type == 'inbound' else payment.cash_discount,
                        'credit': 0.0 if payment.payment_type == 'outbound' else payment.cash_discount,
                    })

            # إعادة الترحيل
            move.action_post()
