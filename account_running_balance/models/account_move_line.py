@api.depends('custom_amount', 'amount_currency', 'account_id', 'company_id', 'partner_id', 'currency_id')
def _compute_running_balance(self):
    if not self:
        return

    account_ids = self.mapped('account_id').ids
    company_ids = self.mapped('company_id').ids

    # تحديد كافة خطوط الحركة المطلوبة لحساب الرصيد (ترتيب دائم من الأقدم)
    domain = [
        ('account_id', 'in', account_ids),
        ('company_id', 'in', company_ids),
    ]

    # يتم التجاهل عن ترتيب العرض المستخدم في الفلتر
    all_lines = self.env['account.move.line'].search(domain, order='id ASC')

    balance = 0.0
    balance_currency = 0.0
    balance_map = {}
    currency_map = {}

    for line in all_lines:
        balance += line.custom_amount or 0.0
        balance_currency += line.amount_currency or 0.0
        balance_map[line.id] = balance
        currency_map[line.id] = balance_currency

    # الآن نعرض القيم المحسوبة حسب السجلات المعروضة (سواء كانت مفلترة أو لا)
    for rec in self:
        rec.running_balance = balance_map.get(rec.id, 0.0)
        rec.running_balance_currency = currency_map.get(rec.id, 0.0)
