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

            # إعادة القيد إلى مسودة دائماً لتجنب مشاكل الحذف
            if move.state == 'posted':
                move.button_draft()

            # حذف أي قيود صفرية سابقة
            move.line_ids.filtered(lambda l: not l.debit and not l.credit).unlink()

            # تحديث أسماء السطور الموجودة
            for line in move.line_ids:
                if not line.name or line.name == '/':
                    line.name = memo

            # إضافة سطرين بقيمة صفر (نقدي + حساب مدين)
            zero_cash_line = {
                'account_id': payment.journal_id.default_account_id.id,
                'partner_id': payment.partner_id.id,
                'name': 'Cash',
                'debit': 0.0,
                'credit': 0.0,
            }
            zero_receivable_line = {
                'account_id': payment.destination_account_id.id,
                'partner_id': payment.partner_id.id,
                'name': 'Receivable',
                'debit': 0.0,
                'credit': 0.0,
            }

            move.write({
                'line_ids': [
                    (0, 0, zero_cash_line),
                    (0, 0, zero_receivable_line),
                ]
            })

            # تطبيق قيد الخصم إن وُجد
            if payment.cash_discount > 0 and payment.discount_account_id:
                discount_line = {
                    'account_id': payment.discount_account_id.id,
                    'partner_id': payment.partner_id.id,
                    'name': 'Cash Discount',
                    'debit': payment.cash_discount if payment.payment_type == 'inbound' else 0.0,
                    'credit': payment.cash_discount if payment.payment_type == 'outbound' else 0.0,
                }
                receivable_discount_line = {
                    'account_id': payment.destination_account_id.id,
                    'partner_id': payment.partner_id.id,
                    'name': 'Receivable Adjustment for Discount',
                    'debit': 0.0 if payment.payment_type == 'inbound' else payment.cash_discount,
                    'credit': 0.0 if payment.payment_type == 'outbound' else payment.cash_discount,
                }

                move.write({
                    'line_ids': [
                        (0, 0, discount_line),
                        (0, 0, receivable_discount_line),
                    ]
                })

            # إعادة ترحيل القيد
            move.action_post()
