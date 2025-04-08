@api.depends('custom_amount', 'amount_currency', 'account_id', 'company_id', 'partner_id', 'currency_id')
def _compute_running_balance(self):
    if not self:
        return

    # تجميع المعرفات المطلوبة
    account_ids = self.mapped('account_id').ids
    company_ids = self.mapped('company_id').ids
    partner_ids = self.mapped('partner_id').ids
    currency_ids = self.mapped('currency_id').ids

    # جلب كل السطور المرتبطة بنفس الشروط حتى لو كانت غير ظاهرة
    domain = [
        ('account_id', 'in', account_ids),
        ('company_id', 'in', company_ids),
    ]
    if partner_ids:
        domain.append(('partner_id', 'in', partner_ids))
    if currency_ids:
        domain.append(('currency_id', 'in', currency_ids))

    # نفس ترتيب Odoo
    all_lines = self.env['account.move.line'].search(domain, order='id ASC')

    # خزن التراكمات
    balance = 0.0
    balance_currency = 0.0
    balance_map = {}
    currency_map = {}

    for line in all_lines:
        balance += line.custom_amount or 0.0
        balance_currency += line.amount_currency or 0.0
        balance_map[line.id] = balance
        currency_map[line.id] = balance_currency

    # تطبيق التراكم على السجلات الظاهرة فقط
    for rec in self:
        rec.running_balance = balance_map.get(rec.id, 0.0)
        rec.running_balance_currency = currency_map.get(rec.id, 0.0)
