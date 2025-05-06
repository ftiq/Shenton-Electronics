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

            # Update line labels
            for line in move.line_ids:
                if not line.name or line.name == '/':
                    line.name = memo

            # Remove zero-value lines if total amount is 0
            if payment.amount == 0:
                move.line_ids.filtered(lambda l: not l.debit and not l.credit).unlink()
                continue

            # Skip if no discount
            if not payment.cash_discount or not payment.discount_account_id:
                continue

            # Check if discount already applied
            already_exists = any(
                line.account_id.id == payment.discount_account_id.id and
                round(line.debit or line.credit, 2) == round(payment.cash_discount, 2)
                for line in move.line_ids
            )
            if already_exists:
                continue

            if move.state == 'posted':
                move.button_draft()

            # Add discount lines
            discount_line = {
                'account_id': payment.discount_account_id.id,
                'partner_id': payment.partner_id.id,
                'name': memo,
                'debit': payment.cash_discount if payment.payment_type == 'inbound' else 0.0,
                'credit': payment.cash_discount if payment.payment_type == 'outbound' else 0.0,
            }
            receivable_line = {
                'account_id': payment.destination_account_id.id,
                'partner_id': payment.partner_id.id,
                'name': memo,
                'debit': 0.0 if payment.payment_type == 'inbound' else payment.cash_discount,
                'credit': 0.0 if payment.payment_type == 'outbound' else payment.cash_discount,
            }

            move.write({
                'line_ids': [
                    (0, 0, discount_line),
                    (0, 0, receivable_line),
                ]
            })

            move.line_ids.filtered(lambda l: not l.debit and not l.credit).unlink()

            move.action_post()
